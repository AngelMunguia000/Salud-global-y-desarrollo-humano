"""Modelado estadístico M0–M6, diagnósticos, validación y sobre-desempeño.

Implementa el contrato §5.5–§5.6 y evalúa las hipótesis H1–H4.

Salidas (``05_ciencia/resultados`` y ``05_ciencia/figuras``) reproducibles con
``python -m 05_ciencia.scripts.modelos`` desde la raíz del repositorio.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GroupKFold

from common.ols import (OLSResult, design_matrix, diagnostics, fit_ols, vif)
from common.panel import RECENT_WINDOW, ROOT, WINDOW, add_derived, load_panel
from common.style import COLORES, REGIONES_ES, aplicar_estilo, pie_fuente

RES = ROOT / "05_ciencia" / "resultados"
FIG = ROOT / "05_ciencia" / "figuras"
EDA_JSON = ROOT / "04_analisis" / "tablas" / "resultados_eda.json"

# Criterio de sobre-desempeño (contrato §5.6)
Z_MEDIO_MIN = 1.0       # residuo medio >= +1 σ
SHARE_POS_MIN = 0.70    # residuo positivo en >= 70 % de los años de la ventana
MIN_ANIOS = 5

MODELOS: dict[str, dict] = {
    "M0": {"x": ["pib_per_capita_ppp"], "fe": [], "desc": "LE ~ PIB (niveles)"},
    "M1": {"x": ["ln_pib"], "fe": [], "desc": "LE ~ ln(PIB)"},
    "M2": {"x": ["ln_pib", "ln_gasto_pc"], "fe": [], "desc": "+ ln(gasto salud pc)"},
    "M3": {"x": ["ln_pib", "ln_gasto_pc", "escolaridad_promedio"], "fe": [],
           "desc": "+ escolaridad (modelo principal)"},
    "M4": {"x": ["ln_pib", "ln_gasto_pc", "escolaridad_promedio"], "fe": ["region", "anio"],
           "desc": "M3 + efectos fijos de región y año"},
    "M5": {"x": ["ln_pib", "ln_gasto_pc", "escolaridad_promedio"], "fe": ["iso3", "anio"],
           "desc": "Panel: efectos fijos de país y año"},
}
# Variante de M3 con efectos de año (solo para residuos de robustez, §5.6)
M3_ANIO = {"x": MODELOS["M3"]["x"], "fe": ["anio"], "desc": "M3 + efectos de año"}
_PREFIJOS_FE = ("region_", "anio_", "iso3_")


# --------------------------------------------------------------------------- #
# Ajuste
# --------------------------------------------------------------------------- #
def muestra_modelo(panel: pd.DataFrame) -> pd.DataFrame:
    """Casos completos de las variables de M3 en el periodo común."""
    cols = ["esperanza_vida", "ln_pib", "ln_gasto_pc", "escolaridad_promedio"]
    data = panel[panel["anio"].between(*WINDOW)].dropna(subset=cols).copy()
    data["anio"] = data["anio"].astype(int)
    return data


def ajustar(data: pd.DataFrame, spec: dict, cov: str = "cluster") -> OLSResult:
    """Ajusta un modelo de ``MODELOS`` (errores agrupados por país por defecto)."""
    X, names = design_matrix(data.assign(anio=data["anio"].astype(str)), spec["x"], spec["fe"])
    return fit_ols(X, data["esperanza_vida"].to_numpy(float), names, cov,
                   groups=data["iso3"].to_numpy())


def tabla_coef(res: OLSResult, modelo: str) -> pd.DataFrame:
    """Coeficientes sin las dummies de efectos fijos."""
    t = res.table()
    t = t[~t["variable"].str.startswith(_PREFIJOS_FE)].copy()
    t.insert(0, "modelo", modelo)
    return t


def ajustar_todos(data: pd.DataFrame) -> dict[str, OLSResult]:
    return {m: ajustar(data, s) for m, s in MODELOS.items()}


# --------------------------------------------------------------------------- #
# Validación fuera de muestra
# --------------------------------------------------------------------------- #
def _metricas(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    e = y - p
    return {"mae": float(np.abs(e).mean()), "rmse": float(np.sqrt((e ** 2).mean())),
            "r2": float(1 - (e @ e) / ((y - y.mean()) ** 2).sum())}


def _predecir(train: pd.DataFrame, test: pd.DataFrame, xcols: list[str],
              fe: list[str]) -> np.ndarray:
    both = pd.concat([train, test], keys=["tr", "te"])
    X, names = design_matrix(both, xcols, fe)
    n_tr = len(train)
    res = fit_ols(X[:n_tr], train["esperanza_vida"].to_numpy(float), names, "classic")
    return X[n_tr:] @ res.coef


def validacion(data: pd.DataFrame, corte: int = 2017) -> pd.DataFrame:
    """Valida M0–M3 (+ región) con división temporal y por países (5 pliegues)."""
    specs = {k: (MODELOS[k]["x"], []) for k in ("M0", "M1", "M2", "M3")}
    specs["M3+región"] = (MODELOS["M3"]["x"], ["region"])
    rows = []
    train, test = data[data["anio"] <= corte], data[data["anio"] > corte]
    folds = list(GroupKFold(n_splits=5).split(data, groups=data["iso3"]))
    for name, (x, fe) in specs.items():
        p = _predecir(train, test, x, fe)
        rows.append({"modelo": name, "esquema": f"temporal (entrena ≤{corte}, prueba >{corte})",
                     "n_prueba": len(test), **_metricas(test["esperanza_vida"].to_numpy(), p)})
        ys, ps = [], []
        for tr_i, te_i in folds:
            ps.append(_predecir(data.iloc[tr_i], data.iloc[te_i], x, fe))
            ys.append(data.iloc[te_i]["esperanza_vida"].to_numpy())
        rows.append({"modelo": name, "esquema": "países no vistos (GroupKFold 5)",
                     "n_prueba": len(data), **_metricas(np.concatenate(ys), np.concatenate(ps))})
    return pd.DataFrame(rows)


def modelo_ml(data: pd.DataFrame, corte: int = 2017) -> tuple[pd.DataFrame, pd.DataFrame]:
    """M6: gradient boosting como chequeo de no linealidades (no para inferencia)."""
    d = data.copy()
    d["region_cod"] = d["region"].astype("category").cat.codes
    feats = ["ln_pib", "ln_gasto_pc", "escolaridad_promedio", "region_cod"]
    make = lambda: HistGradientBoostingRegressor(          # noqa: E731
        categorical_features=[3], max_depth=3, learning_rate=0.05, max_iter=300,
        random_state=42)
    rows = []
    tr, te = d[d["anio"] <= corte], d[d["anio"] > corte]
    m = make().fit(tr[feats], tr["esperanza_vida"])
    rows.append({"modelo": "M6 GBM", "esquema": f"temporal (entrena ≤{corte}, prueba >{corte})",
                 "n_prueba": len(te), **_metricas(te["esperanza_vida"].to_numpy(), m.predict(te[feats]))})
    imp = permutation_importance(m, te[feats], te["esperanza_vida"], n_repeats=20,
                                 random_state=42)
    importancia = pd.DataFrame({"variable": feats, "importancia": imp.importances_mean,
                                "desv": imp.importances_std}).sort_values("importancia",
                                                                           ascending=False)
    ys, ps = [], []
    for tr_i, te_i in GroupKFold(n_splits=5).split(d, groups=d["iso3"]):
        mm = make().fit(d.iloc[tr_i][feats], d.iloc[tr_i]["esperanza_vida"])
        ps.append(mm.predict(d.iloc[te_i][feats]))
        ys.append(d.iloc[te_i]["esperanza_vida"].to_numpy())
    rows.append({"modelo": "M6 GBM", "esquema": "países no vistos (GroupKFold 5)",
                 "n_prueba": len(d), **_metricas(np.concatenate(ys), np.concatenate(ps))})
    return pd.DataFrame(rows), importancia


# --------------------------------------------------------------------------- #
# Sobre-desempeño
# --------------------------------------------------------------------------- #
def residuos_z(res: OLSResult, data: pd.DataFrame) -> pd.DataFrame:
    """Residuo y residuo estandarizado (resid / σ̂) por observación."""
    sigma = float(np.sqrt(res.resid @ res.resid / (res.n - res.k)))
    out = data[["iso3", "pais", "region", "anio"]].copy()
    out["residuo"] = res.resid
    out["z"] = res.resid / sigma
    return out


def evaluar_paises(rz: pd.DataFrame, ventana: tuple[int, int] = RECENT_WINDOW) -> pd.DataFrame:
    """Resume los residuos por país en la ventana y aplica el criterio §5.6."""
    w = rz[rz["anio"].between(*ventana)]
    g = w.groupby(["iso3", "pais", "region"])
    out = g.agg(n_anios=("z", "size"), z_medio=("z", "mean"), residuo_medio=("residuo", "mean"),
                z_sd=("z", "std")).reset_index()
    out["pct_anios_positivo"] = g["z"].apply(lambda s: (s > 0).mean()).to_numpy()
    out["ee_z_medio"] = out["z_sd"] / np.sqrt(out["n_anios"])
    out["pasa_criterio"] = ((out["z_medio"] >= Z_MEDIO_MIN)
                            & (out["pct_anios_positivo"] >= SHARE_POS_MIN)
                            & (out["n_anios"] >= MIN_ANIOS))
    return out.sort_values("z_medio", ascending=False).reset_index(drop=True)


def modelo_riqueza_m1(panel: pd.DataFrame) -> tuple[OLSResult, pd.DataFrame]:
    """M1 (solo ingreso) con efectos fijos de año, 1990–2023.

    Los efectos de año absorben el desplazamiento global de la curva
    ingreso–esperanza de vida (ver figura 04 del EDA); sin ellos, casi todos
    los países parecerían "sobre-desempeñar" en los años recientes.
    """
    d = panel[panel["anio"].between(1990, WINDOW[1])].dropna(
        subset=["esperanza_vida", "ln_pib"]).copy()
    d["anio"] = d["anio"].astype(int)
    X, names = design_matrix(d.assign(anio=d["anio"].astype(str)), ["ln_pib"], ["anio"])
    return fit_ols(X, d["esperanza_vida"].to_numpy(float), names, "classic"), d


def leave_one_country_out(d: pd.DataFrame, paises: list[str]) -> pd.DataFrame:
    """Reajusta M1 (con efectos de año) sin cada país candidato y recalcula su z."""
    X, names = design_matrix(d.assign(anio=d["anio"].astype(str)), ["ln_pib"], ["anio"])
    y = d["esperanza_vida"].to_numpy(float)
    rows = []
    for iso in paises:
        mask = (d["iso3"] != iso).to_numpy()
        res = fit_ols(X[mask], y[mask], names, "classic")
        sigma = float(np.sqrt(res.resid @ res.resid / (res.n - res.k)))
        sel = (~mask) & d["anio"].between(*RECENT_WINDOW).to_numpy()
        z = (y[sel] - X[sel] @ res.coef) / sigma
        rows.append({"iso3": iso, "z_medio_loco": float(z.mean()),
                     "pct_positivo_loco": float((z > 0).mean()),
                     "pasa_loco": bool(z.mean() >= Z_MEDIO_MIN and (z > 0).mean() >= SHARE_POS_MIN)})
    return pd.DataFrame(rows)


def sobre_desempeno(panel: pd.DataFrame, data: pd.DataFrame, res_m3: OLSResult
                    ) -> tuple[pd.DataFrame, dict]:
    """Aplica §5.6: lista bajo M1, y robustez bajo M3 y leave-one-country-out."""
    m1, d1 = modelo_riqueza_m1(panel)
    r1 = residuos_z(m1, d1)
    ev1 = evaluar_paises(r1).rename(columns={
        "z_medio": "z_medio_M1", "residuo_medio": "residuo_medio_M1",
        "pct_anios_positivo": "pct_positivo_M1", "pasa_criterio": "pasa_M1",
        "ee_z_medio": "ee_z_M1"}).drop(columns="z_sd")
    ev3 = evaluar_paises(residuos_z(res_m3, data))[
        ["iso3", "z_medio", "pct_anios_positivo", "pasa_criterio", "n_anios"]].rename(columns={
            "z_medio": "z_medio_M3", "pct_anios_positivo": "pct_positivo_M3",
            "pasa_criterio": "pasa_M3", "n_anios": "n_anios_M3"})
    tabla = ev1.merge(ev3, on="iso3", how="left")
    tabla["pasa_M3"] = tabla["pasa_M3"].fillna(False).astype(bool)
    cand = tabla.loc[tabla["pasa_M1"], "iso3"].tolist()
    loco = leave_one_country_out(d1, cand)
    tabla = tabla.merge(loco, on="iso3", how="left")
    tabla["pasa_loco"] = tabla["pasa_loco"].fillna(False).astype(bool)
    tabla["robusto"] = tabla["pasa_M1"] & tabla["pasa_M3"] & tabla["pasa_loco"]
    info = {"sigma_m1": float(np.sqrt(m1.resid @ m1.resid / (m1.n - m1.k))),
            "n_m1": m1.n, "beta_m1": float(m1.coef[1]),
            "candidatos_M1": int(tabla["pasa_M1"].sum()),
            "pasan_M3": int((tabla["pasa_M1"] & tabla["pasa_M3"]).sum()),
            "robustos": int(tabla["robusto"].sum())}
    return tabla, info


def perfil_paises(panel: pd.DataFrame, iso3s: list[str]) -> pd.DataFrame:
    """Perfil medio 2015–2023 de los países señalados."""
    w = panel[panel["anio"].between(*RECENT_WINDOW) & panel["iso3"].isin(iso3s)]
    cols = ["esperanza_vida", "mortalidad_infantil", "pib_per_capita_ppp",
            "gasto_salud_pct_pib", "gasto_salud_per_capita_ppp", "escolaridad_promedio"]
    return w.groupby(["iso3", "pais", "region"])[cols].mean().round(2).reset_index()


# --------------------------------------------------------------------------- #
# Hipótesis
# --------------------------------------------------------------------------- #
def evaluar_hipotesis(fits: dict[str, OLSResult], diag: pd.DataFrame, sob_info: dict,
                      eda: dict) -> pd.DataFrame:
    """Resume el veredicto de H1–H4 con la evidencia numérica."""
    d = diag.set_index("modelo")
    c3 = fits["M3"].table().set_index("variable")
    fe = {m: fits[m].table().set_index("variable") for m in ("M4", "M5")}
    h1 = (d.loc["M1", "r2_ajustado"] > d.loc["M0", "r2_ajustado"]) and d.loc["M0", "reset_p"] < 0.05
    h2_pool = (d.loc["M3", "r2_ajustado"] > d.loc["M1", "r2_ajustado"]
               and c3.loc["ln_gasto_pc", "p_valor"] < 0.05
               and c3.loc["escolaridad_promedio", "p_valor"] < 0.05)
    h2_fe = all(fe[m].loc[v, "p_valor"] < 0.05 for m in fe for v in ("ln_gasto_pc", "escolaridad_promedio"))
    h3 = sob_info["robustos"] > 0
    h4 = (eda["sigma_2023"] < eda["sigma_1990"]) and eda["beta_1990_2023"]["beta"] < 0 \
        and eda["beta_1990_2023"]["p_valor"] < 0.05

    def veredicto(ok: bool, parcial: bool = False) -> str:
        return "Parcialmente respaldada" if parcial else ("Respaldada" if ok else "No respaldada")

    rows = [
        ("H1", "La relación esperanza de vida–PIB es cóncava (ln supera a niveles)",
         veredicto(h1),
         f"R² aj. M0={d.loc['M0','r2_ajustado']:.3f} vs M1={d.loc['M1','r2_ajustado']:.3f}; "
         f"RESET M0 p={d.loc['M0','reset_p']:.2g}"),
        ("H2", "Gasto en salud y escolaridad aportan más allá del ingreso",
         veredicto(h2_pool and h2_fe, parcial=h2_pool and not h2_fe),
         f"M3 (agrupado): p(ln gasto)={c3.loc['ln_gasto_pc','p_valor']:.2g}, "
         f"p(escolaridad)={c3.loc['escolaridad_promedio','p_valor']:.2g}; "
         f"con efectos fijos M4: p={fe['M4'].loc['ln_gasto_pc','p_valor']:.2g}/"
         f"{fe['M4'].loc['escolaridad_promedio','p_valor']:.2g}; "
         f"M5: p={fe['M5'].loc['ln_gasto_pc','p_valor']:.2g}/{fe['M5'].loc['escolaridad_promedio','p_valor']:.2g}"),
        ("H3", "Existen países de sobre-desempeño robustos", veredicto(h3),
         f"{sob_info['candidatos_M1']} bajo M1; {sob_info['pasan_M3']} también bajo M3; "
         f"{sob_info['robustos']} robustos (también leave-one-country-out)"),
        ("H4", "La brecha de esperanza de vida converge (1990–2023)", veredicto(h4),
         f"σ 1990={eda['sigma_1990']:.2f} → 2023={eda['sigma_2023']:.2f}; "
         f"β={eda['beta_1990_2023']['beta']:.4f} (p={eda['beta_1990_2023']['p_valor']:.2g})"),
    ]
    return pd.DataFrame(rows, columns=["hipotesis", "enunciado", "veredicto", "evidencia"])


# --------------------------------------------------------------------------- #
# Figuras
# --------------------------------------------------------------------------- #
def _guardar(fig, nombre: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    pie_fuente(fig)
    fig.savefig(FIG / nombre, bbox_inches="tight")
    plt.close(fig)


def fig_diagnosticos(res: OLSResult, data: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4))
    ax = axes[0]
    for reg, idx in data.reset_index(drop=True).groupby("region").groups.items():
        ax.scatter(res.fitted[idx], res.resid[idx], s=5, alpha=0.5, color=COLORES[reg])
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("Valor ajustado (años)")
    ax.set_ylabel("Residuo (años)")
    ax.set_title("Residuos vs. ajustados (M3)")
    (osm, osr), (slope, intercept, _) = stats.probplot(res.resid, dist="norm")
    axes[1].scatter(osm, osr, s=5, alpha=0.5, color="#0072B2")
    axes[1].plot(osm, slope * np.array(osm) + intercept, color="black", lw=1)
    axes[1].set_xlabel("Cuantiles teóricos")
    axes[1].set_ylabel("Cuantiles de residuos")
    axes[1].set_title("QQ-plot de residuos")
    from common.ols import cooks_distance
    cook = cooks_distance(res)
    axes[2].scatter(res.leverage, cook, s=6, alpha=0.5, color="#D55E00")
    axes[2].axhline(4 / res.n, color="black", ls="--", lw=0.8, label="4/n")
    axes[2].set_xlabel("Apalancamiento")
    axes[2].set_ylabel("Distancia de Cook")
    axes[2].set_title("Observaciones influyentes")
    axes[2].legend()
    fig.tight_layout()
    _guardar(fig, "01_diagnosticos_m3.png")


def fig_coeficientes(coefs: pd.DataFrame) -> None:
    sub = coefs[(coefs["modelo"].isin(["M3", "M4", "M5"])) & (coefs["variable"] != "const")]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    labels = {"ln_pib": "ln PIB pc", "ln_gasto_pc": "ln gasto salud pc",
              "escolaridad_promedio": "Escolaridad (años)"}
    for ax, var in zip(axes, labels):
        s = sub[sub["variable"] == var].reset_index(drop=True)
        ax.errorbar(s["coef"], range(len(s)), xerr=[s["coef"] - s["ic95_inf"], s["ic95_sup"] - s["coef"]],
                    fmt="o", color="#0072B2", capsize=3)
        ax.set_yticks(range(len(s)), s["modelo"])
        ax.axvline(0, color="black", lw=0.8)
        ax.set_title(labels[var])
        ax.set_xlabel("Años de esperanza de vida (IC 95 %)")
    fig.suptitle("Efectos estimados (asociaciones), errores agrupados por país", fontweight="bold")
    fig.tight_layout()
    _guardar(fig, "02_coeficientes_m3_m4_m5.png")


def fig_sobre_desempeno(tabla: pd.DataFrame, top: int = 15) -> None:
    t = tabla[tabla["pasa_M1"]].copy()
    t = t.sort_values("z_medio_M1").tail(top)
    fig, ax = plt.subplots(figsize=(8.5, max(3.5, 0.34 * len(t) + 1.5)))
    colors = [COLORES[r] for r in t["region"]]
    ax.barh(t["pais"], t["z_medio_M1"], xerr=1.96 * t["ee_z_M1"], color=colors, alpha=0.9,
            error_kw={"ecolor": "#333333", "capsize": 2, "lw": 1})
    for i, (_, r) in enumerate(t.iterrows()):
        if r["robusto"]:
            ax.text(r["z_medio_M1"] + 1.96 * r["ee_z_M1"] + 0.05, i, "●", va="center", fontsize=8)
    ax.axvline(Z_MEDIO_MIN, color="black", ls="--", lw=0.8)
    ax.set_xlabel("Residuo medio estandarizado 2015–2023 (σ), M1 solo ingreso")
    ax.set_title("Países con esperanza de vida mayor a la predicha por su ingreso")
    handles = [plt.Line2D([], [], marker="s", ls="", color=COLORES[r], label=REGIONES_ES[r])
               for r in COLORES if r in set(t["region"])]
    ax.legend(handles=handles, fontsize=7, loc="lower right", title="● robusto (M1, M3, LOCO)",
              title_fontsize=7)
    fig.tight_layout()
    _guardar(fig, "03_paises_sobre_desempeno.png")


def fig_dispersion_resaltada(panel: pd.DataFrame, tabla: pd.DataFrame) -> None:
    g = panel[panel["anio"].between(*RECENT_WINDOW)].dropna(subset=["ln_pib", "esperanza_vida"])
    m = g.groupby(["iso3", "pais"]).agg(le=("esperanza_vida", "mean"), pib=("pib_per_capita_ppp", "mean")).reset_index()
    rob = set(tabla.loc[tabla["robusto"], "iso3"])
    fig, ax = plt.subplots(figsize=(9, 5.6))
    ax.scatter(m["pib"], m["le"], s=20, color="#B0B0B0")
    r = m[m["iso3"].isin(rob)]
    ax.scatter(r["pib"], r["le"], s=46, color="#D55E00", edgecolor="black", zorder=3,
               label="Sobre-desempeño robusto")
    for _, row in r.iterrows():
        ax.annotate(row["pais"], (row["pib"], row["le"]), fontsize=7, xytext=(4, 3),
                    textcoords="offset points")
    coef = np.polyfit(np.log(m["pib"]), m["le"], 1)
    xs = np.linspace(np.log(m["pib"].min()), np.log(m["pib"].max()), 100)
    ax.plot(np.exp(xs), np.polyval(coef, xs), color="black", lw=1.5,
            label="Tendencia (ajuste a las medias por país)")
    ax.set_xscale("log")
    ax.set_xlabel("PIB per cápita PPA medio 2015–2023 (log)")
    ax.set_ylabel("Esperanza de vida media 2015–2023")
    ax.set_title("Países que superan lo que predice su ingreso")
    ax.legend(fontsize=8, loc="lower right")
    _guardar(fig, "04_sobre_desempeno_dispersion.png")


def fig_importancia(imp: pd.DataFrame) -> None:
    names = {"ln_pib": "ln PIB pc", "ln_gasto_pc": "ln gasto salud pc",
             "escolaridad_promedio": "Escolaridad", "region_cod": "Región"}
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    s = imp.iloc[::-1]
    ax.barh([names[v] for v in s["variable"]], s["importancia"], xerr=s["desv"], color="#0072B2")
    ax.set_xlabel("Aumento del error (años) al permutar la variable")
    ax.set_title("M6 (GBM): importancia por permutación")
    fig.tight_layout()
    _guardar(fig, "05_importancia_m6.png")


# --------------------------------------------------------------------------- #
def main() -> None:
    """Ejecuta todo el modelado y guarda tablas, figuras y veredicto de hipótesis."""
    aplicar_estilo()
    RES.mkdir(parents=True, exist_ok=True)
    if not EDA_JSON.is_file():
        raise FileNotFoundError("Falta resultados_eda.json: ejecuta primero el EDA (make analisis).")
    eda = json.loads(EDA_JSON.read_text(encoding="utf-8"))

    panel = add_derived(load_panel())
    data = muestra_modelo(panel)
    print(f"[modelos] muestra: {len(data):,} país-año, {data['iso3'].nunique()} países")

    fits = ajustar_todos(data)
    coefs = pd.concat([tabla_coef(r, m) for m, r in fits.items()], ignore_index=True)
    coefs.to_csv(RES / "modelos_coeficientes.csv", index=False)

    diag_rows = []
    for m, spec in MODELOS.items():
        classic = ajustar(data, spec, cov="classic")
        dg = diagnostics(classic)
        diag_rows.append({"modelo": m, "descripcion": spec["desc"], **dg})
    diag = pd.DataFrame(diag_rows)
    diag.to_csv(RES / "modelos_ajuste_diagnosticos.csv", index=False)

    vif(data, MODELOS["M3"]["x"]).to_csv(RES / "vif_m3.csv", index=False)

    val = validacion(data)
    ml, imp = modelo_ml(data)
    pd.concat([val, ml], ignore_index=True).to_csv(RES / "validacion_fuera_de_muestra.csv", index=False)
    imp.to_csv(RES / "importancia_m6.csv", index=False)

    tabla, info = sobre_desempeno(panel, data, ajustar(data, M3_ANIO, cov="classic"))
    tabla.to_csv(RES / "paises_sobre_desempeno.csv", index=False)
    robustos = tabla[tabla["robusto"]]
    perfil_paises(panel, robustos["iso3"].tolist()).to_csv(RES / "perfil_sobre_desempeno.csv", index=False)
    cand = tabla[tabla["pasa_M1"]]
    cand.to_csv(RES / "candidatos_sobre_desempeno_M1.csv", index=False)
    sub = tabla.sort_values("z_medio_M1").head(15)[
        ["iso3", "pais", "region", "z_medio_M1", "residuo_medio_M1", "pct_positivo_M1"]]
    sub.to_csv(RES / "paises_bajo_desempeno_M1.csv", index=False)

    hip = evaluar_hipotesis(fits, diag, info, eda)
    hip.to_csv(RES / "hipotesis.csv", index=False)
    (RES / "resumen_modelos.json").write_text(
        json.dumps({**info, "n": len(data), "paises": int(data["iso3"].nunique())},
                   indent=2), encoding="utf-8")

    fig_diagnosticos(ajustar(data, MODELOS["M3"], cov="classic"), data)
    fig_coeficientes(coefs)
    fig_sobre_desempeno(tabla)
    fig_dispersion_resaltada(panel, tabla)
    fig_importancia(imp)

    print(diag[["modelo", "n", "r2", "r2_ajustado", "rmse", "reset_p", "breusch_pagan_p"]].round(4).to_string(index=False))
    print(val.round(3).to_string(index=False))
    print(ml.round(3).to_string(index=False))
    print(hip.to_string(index=False))
    print(robustos[["pais", "region", "z_medio_M1", "pct_positivo_M1", "z_medio_M3"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()

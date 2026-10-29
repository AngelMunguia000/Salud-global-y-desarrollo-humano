"""Análisis exploratorio completo (contrato §5.4 y §5.7; preguntas P1 y P3).

Salidas:
    04_analisis/tablas/*.csv        tablas reproducibles
    04_analisis/visualizaciones/*.png   figuras finales
    04_analisis/tablas/resultados_eda.json   cifras clave citadas en el informe

Uso: ``python -m 04_analisis.scripts.eda_completo`` desde la raíz del repo.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from common.ols import design_matrix, fit_ols
from common.panel import ROOT, WINDOW, add_derived, load_panel
from common.style import COLORES, REGIONES_ES, aplicar_estilo, pie_fuente

TABLAS = ROOT / "04_analisis" / "tablas"
FIGURAS = ROOT / "04_analisis" / "visualizaciones"
VARIABLES = {
    "esperanza_vida": "Esperanza de vida (años)",
    "mortalidad_infantil": "Mortalidad infantil (‰)",
    "pib_per_capita_ppp": "PIB per cápita PPA (US$ 2021)",
    "gasto_salud_pct_pib": "Gasto en salud (% PIB)",
    "gasto_salud_per_capita_ppp": "Gasto en salud per cápita PPA (US$)",
    "escolaridad_promedio": "Escolaridad promedio (años)",
}
CORR_COLS = ["esperanza_vida", "mortalidad_infantil", "ln_pib",
             "gasto_salud_pct_pib", "ln_gasto_pc", "escolaridad_promedio"]


# --------------------------------------------------------------------------- #
# Tablas
# --------------------------------------------------------------------------- #
def cobertura(panel: pd.DataFrame) -> pd.DataFrame:
    """Proporción de datos presentes por variable y región (periodo común)."""
    win = panel[panel["anio"].between(*WINDOW)]
    cols = list(VARIABLES)
    out = win.groupby("region")[cols].apply(lambda g: g.notna().mean())
    out.loc["Global"] = win[cols].notna().mean()
    return out


def descriptivos(panel: pd.DataFrame) -> pd.DataFrame:
    """Estadísticos descriptivos por variable (periodo común)."""
    win = panel[panel["anio"].between(*WINDOW)]
    return win[list(VARIABLES)].describe().T.assign(
        asimetria=win[list(VARIABLES)].skew()
    )


def correlaciones(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    """Matrices Pearson y Spearman sobre casos completos de las 6 variables."""
    data = panel[panel["anio"].between(*WINDOW)].dropna(subset=CORR_COLS)
    return data[CORR_COLS].corr("pearson"), data[CORR_COLS].corr("spearman"), len(data)


def ajuste_por_anio(panel: pd.DataFrame) -> pd.DataFrame:
    """R² de esperanza de vida ~ PIB (lineal vs log) en cada corte transversal."""
    rows = []
    for year, g in panel.dropna(subset=["esperanza_vida", "ln_pib"]).groupby("anio"):
        if len(g) < 30:
            continue
        y = g["esperanza_vida"].to_numpy()
        r2 = {}
        for label, col in (("lineal", "pib_per_capita_ppp"), ("log", "ln_pib")):
            X, names = design_matrix(g, [col])
            r2[label] = fit_ols(X, y, names, "classic").r2
        rows.append({"anio": year, "n": len(g), "r2_lineal": r2["lineal"],
                     "r2_log": r2["log"],
                     "spearman": g["esperanza_vida"].corr(g["ln_pib"], method="spearman")})
    return pd.DataFrame(rows)


def series_regionales(panel: pd.DataFrame, var: str) -> pd.DataFrame:
    """Media simple entre países por región y año (sin ponderar por población)."""
    return panel.groupby(["anio", "region"])[var].mean().unstack("region")


def convergencia_sigma(panel: pd.DataFrame) -> pd.DataFrame:
    """σ-convergencia: desviación estándar y CV entre países, y brecha regional."""
    g = panel.groupby("anio")["esperanza_vida"]
    out = pd.DataFrame({"desv_est": g.std(), "cv": g.std() / g.mean(), "n_paises": g.count()})
    reg = series_regionales(panel, "esperanza_vida")
    out["brecha_regional_max_min"] = reg.max(axis=1) - reg.min(axis=1)
    out["desv_est_entre_regiones"] = reg.std(axis=1)
    return out


def convergencia_beta(panel: pd.DataFrame, start: int, end: int) -> dict[str, float]:
    """β-convergencia: ΔLE anual ~ LE inicial (errores HC3)."""
    a = panel[panel["anio"] == start].set_index("iso3")["esperanza_vida"]
    b = panel[panel["anio"] == end].set_index("iso3")["esperanza_vida"]
    df = pd.concat([a.rename("le0"), b.rename("le1")], axis=1).dropna()
    df["crec"] = (df["le1"] - df["le0"]) / (end - start)
    X, names = design_matrix(df, ["le0"])
    res = fit_ols(X, df["crec"].to_numpy(), names, "HC3")
    t = res.table().set_index("variable").loc["le0"]
    return {"inicio": start, "fin": end, "n": len(df), "beta": float(t["coef"]),
            "p_valor": float(t["p_valor"]), "r2": float(res.r2)}


def sigma_por_periodo(panel: pd.DataFrame) -> pd.DataFrame:
    """Desviación estándar de esperanza de vida por región en años clave."""
    rows = []
    for year in (1960, 1990, 2000, 2010, 2019, 2023):
        g = panel[panel["anio"] == year].groupby("region")["esperanza_vida"].mean()
        rows.append({"anio": year, **g.round(2).to_dict()})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Figuras
# --------------------------------------------------------------------------- #
def _fmt_money(ax) -> None:
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))


def _guardar(fig, nombre: str) -> Path:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    pie_fuente(fig)
    path = FIGURAS / nombre
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_cobertura(cob: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(9, 4.8))
    data = cob.rename(index=REGIONES_ES, columns=VARIABLES) * 100
    im = ax.imshow(data.to_numpy(), cmap="viridis", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(data.shape[1]), data.columns, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(range(data.shape[0]), data.index, fontsize=8)
    ax.grid(False)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data.iat[i, j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8,
                    color="white" if v < 60 else "black")
    fig.colorbar(im, ax=ax, label="% de datos presentes")
    ax.set_title(f"Cobertura de datos por variable y región ({WINDOW[0]}–{WINDOW[1]})")
    fig.tight_layout()
    return _guardar(fig, "01_cobertura_datos.png")


def fig_correlaciones(pear: pd.DataFrame, spear: pd.DataFrame, n: int) -> Path:
    names = ["Esp. vida", "Mort. infantil", "ln PIB pc", "Gasto % PIB",
             "ln gasto pc", "Escolaridad"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for ax, mat, title in zip(axes, (pear, spear), ("Pearson", "Spearman")):
        im = ax.imshow(mat.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(6), names, rotation=40, ha="right", fontsize=8)
        ax.set_yticks(range(6), names, fontsize=8)
        ax.grid(False)
        for i in range(6):
            for j in range(6):
                ax.text(j, i, f"{mat.iat[i, j]:.2f}", ha="center", va="center", fontsize=7)
        ax.set_title(title)
    fig.colorbar(im, ax=axes, shrink=0.8, label="Coeficiente")
    fig.suptitle(f"Correlaciones (casos completos, n = {n:,} país-año, {WINDOW[0]}–{WINDOW[1]})",
                 fontweight="bold")
    return _guardar(fig, "02_correlaciones.png")


def fig_dispersion_log(panel: pd.DataFrame, year: int = 2021) -> Path:
    """Dispersión ingreso–esperanza de vida (escala log) con ajuste lineal y cuadrático."""
    g = panel[(panel["anio"] == year)].dropna(subset=["ln_pib", "esperanza_vida"])
    fig, ax = plt.subplots(figsize=(9, 5.6))
    for reg, d in g.groupby("region"):
        ax.scatter(d["pib_per_capita_ppp"], d["esperanza_vida"], s=26, alpha=0.85,
                   color=COLORES[reg], label=REGIONES_ES[reg], edgecolor="white", lw=0.4)
    xs = np.linspace(g["ln_pib"].min(), g["ln_pib"].max(), 200)
    coef = np.polyfit(g["ln_pib"], g["esperanza_vida"], 1)
    coef2 = np.polyfit(g["ln_pib"], g["esperanza_vida"], 2)
    ax.plot(np.exp(xs), np.polyval(coef, xs), color="#555555", ls="--", lw=1.3,
            label="Ajuste lineal en ln(PIB)")
    ax.plot(np.exp(xs), np.polyval(coef2, xs), color="#000000", lw=1.8,
            label="Ajuste cuadrático en ln(PIB)")
    ax.set_xscale("log")
    _fmt_money(ax)
    ax.set_xlabel("PIB per cápita PPA, US$ constantes 2021 (escala logarítmica)")
    ax.set_ylabel("Esperanza de vida al nacer (años)")
    ax.set_title(f"Ingreso y esperanza de vida, {year} (n = {len(g)} países)")
    ax.legend(fontsize=7.5, loc="lower right", ncol=2)
    return _guardar(fig, "03_dispersion_pib_esperanza_vida_log.png")


def fig_dispersion_decadas(panel: pd.DataFrame) -> Path:
    years = [1990, 2000, 2010, 2022]
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.8), sharey=True)
    for ax, year in zip(axes, years):
        g = panel[panel["anio"] == year].dropna(subset=["ln_pib", "esperanza_vida"])
        for reg, d in g.groupby("region"):
            ax.scatter(d["pib_per_capita_ppp"], d["esperanza_vida"], s=14, alpha=0.8,
                       color=COLORES[reg])
        ax.set_xscale("log")
        ax.set_title(f"{year} (n={len(g)})")
        ax.set_xlabel("PIB pc PPA (log)")
    axes[0].set_ylabel("Esperanza de vida")
    handles = [plt.Line2D([], [], marker="o", ls="", color=COLORES[r], label=REGIONES_ES[r])
               for r in COLORES]
    fig.legend(handles=handles, loc="lower center", ncol=7, fontsize=7.5,
               bbox_to_anchor=(0.5, -0.08))
    fig.suptitle("La curva ingreso–esperanza de vida se desplaza hacia arriba con el tiempo",
                 fontweight="bold")
    fig.tight_layout()
    return _guardar(fig, "04_dispersion_por_decada.png")


def fig_series_regionales(panel: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, var, title in zip(axes, ("esperanza_vida", "mortalidad_infantil"),
                              ("Esperanza de vida (años)", "Mortalidad infantil (por 1,000)")):
        s = series_regionales(panel, var)
        for reg in s.columns:
            ax.plot(s.index, s[reg], color=COLORES[reg], lw=2, label=REGIONES_ES[reg])
        ax.set_title(title)
        ax.set_xlabel("Año")
    axes[0].legend(fontsize=7.5, loc="lower right")
    fig.suptitle("Evolución regional (media simple de países), 1960–2024", fontweight="bold")
    fig.tight_layout()
    return _guardar(fig, "05_series_regionales.png")


def fig_convergencia(sigma: pd.DataFrame, panel: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    axes[0].plot(sigma.index, sigma["desv_est"], color="#0072B2", lw=2,
                 label="Entre todos los países")
    axes[0].plot(sigma.index, sigma["desv_est_entre_regiones"], color="#D55E00", lw=2,
                 label="Entre medias regionales")
    axes[0].set_title("σ-convergencia: dispersión de la esperanza de vida")
    axes[0].set_ylabel("Desviación estándar (años)")
    axes[0].set_xlabel("Año")
    axes[0].legend(fontsize=8)
    for reg, d in panel.groupby("region"):
        s = d.groupby("anio")["esperanza_vida"].std()
        axes[1].plot(s.index, s, color=COLORES[reg], lw=1.8, label=REGIONES_ES[reg])
    axes[1].set_title("Dispersión dentro de cada región")
    axes[1].set_xlabel("Año")
    axes[1].legend(fontsize=7, ncol=2)
    fig.suptitle("¿Convergencia o divergencia en salud? (1960–2024)", fontweight="bold")
    fig.tight_layout()
    return _guardar(fig, "06_convergencia_sigma.png")


def fig_beta(panel: pd.DataFrame, start: int = 1990, end: int = 2023) -> Path:
    a = panel[panel["anio"] == start].set_index("iso3")
    b = panel[panel["anio"] == end].set_index("iso3")["esperanza_vida"]
    df = a[["esperanza_vida", "region"]].join(b.rename("le1")).dropna()
    df["crec"] = (df["le1"] - df["esperanza_vida"]) / (end - start)
    fig, ax = plt.subplots(figsize=(8, 5))
    for reg, d in df.groupby("region"):
        ax.scatter(d["esperanza_vida"], d["crec"], s=26, color=COLORES[reg],
                   label=REGIONES_ES[reg], alpha=0.85, edgecolor="white", lw=0.4)
    c = np.polyfit(df["esperanza_vida"], df["crec"], 1)
    xs = np.linspace(df["esperanza_vida"].min(), df["esperanza_vida"].max(), 50)
    ax.plot(xs, np.polyval(c, xs), color="black", lw=1.5)
    ax.axhline(0, color="#888888", lw=0.8)
    ax.set_xlabel(f"Esperanza de vida en {start} (años)")
    ax.set_ylabel(f"Ganancia anual {start}–{end} (años/año)")
    ax.set_title(f"β-convergencia: quien partía más abajo ganó más (n = {len(df)})")
    ax.legend(fontsize=7, ncol=2)
    return _guardar(fig, "07_convergencia_beta.png")


def fig_relaciones(panel: pd.DataFrame, year: int = 2021) -> Path:
    g = panel[panel["anio"] == year]
    specs = [("ln_gasto_pc", "Gasto en salud per cápita PPA (log)", True),
             ("escolaridad_promedio", "Escolaridad promedio (años)", False),
             ("gasto_salud_pct_pib", "Gasto en salud (% del PIB)", False)]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    for ax, (col, label, is_log) in zip(axes, specs):
        d = g.dropna(subset=[col, "esperanza_vida"])
        for reg, dd in d.groupby("region"):
            ax.scatter(dd[col], dd["esperanza_vida"], s=16, color=COLORES[reg], alpha=0.85)
        rho = d[col].corr(d["esperanza_vida"], method="spearman")
        ax.set_title(f"ρ Spearman = {rho:.2f} (n={len(d)})")
        ax.set_xlabel(label)
        if is_log:
            ticks = np.log([10, 100, 1000, 10000])
            ax.set_xticks(ticks, ["10", "100", "1,000", "10,000"])
    axes[0].set_ylabel("Esperanza de vida (años)")
    fig.suptitle(f"Gasto en salud, educación y esperanza de vida, {year}", fontweight="bold")
    fig.tight_layout()
    return _guardar(fig, "08_gasto_educacion_vs_esperanza_vida.png")


def fig_ajuste_anio(aj: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    ax.plot(aj["anio"], aj["r2_lineal"], color="#555555", lw=2, ls="--", label="R² lineal en PIB")
    ax.plot(aj["anio"], aj["r2_log"], color="#0072B2", lw=2, label="R² lineal en ln(PIB)")
    ax.set_ylim(0, 1)
    ax.set_xlabel("Año")
    ax.set_ylabel("R² (corte transversal)")
    ax.set_title("El logaritmo del ingreso explica más que el ingreso en niveles")
    ax.legend()
    return _guardar(fig, "09_r2_lineal_vs_log_por_anio.png")


# --------------------------------------------------------------------------- #
def main() -> None:
    """Genera todas las tablas y figuras del EDA."""
    aplicar_estilo()
    TABLAS.mkdir(parents=True, exist_ok=True)
    panel = add_derived(load_panel())

    cob = cobertura(panel)
    desc = descriptivos(panel)
    pear, spear, n_cc = correlaciones(panel)
    aj = ajuste_por_anio(panel)
    sig = convergencia_sigma(panel)
    beta = convergencia_beta(panel, 1990, 2023)
    beta_00 = convergencia_beta(panel, 2000, 2023)

    cob.to_csv(TABLAS / "cobertura_variable_region.csv")
    desc.to_csv(TABLAS / "descriptivos.csv")
    pear.to_csv(TABLAS / "correlacion_pearson.csv")
    spear.to_csv(TABLAS / "correlacion_spearman.csv")
    aj.to_csv(TABLAS / "r2_lineal_vs_log_por_anio.csv", index=False)
    sig.to_csv(TABLAS / "sigma_convergencia.csv")
    sigma_por_periodo(panel).to_csv(TABLAS / "esperanza_vida_regional_anios_clave.csv", index=False)

    for fn in (lambda: fig_cobertura(cob), lambda: fig_correlaciones(pear, spear, n_cc),
               lambda: fig_dispersion_log(panel), lambda: fig_dispersion_decadas(panel),
               lambda: fig_series_regionales(panel), lambda: fig_convergencia(sig, panel),
               lambda: fig_beta(panel), lambda: fig_relaciones(panel),
               lambda: fig_ajuste_anio(aj)):
        print("figura:", fn().name)

    y21 = aj[aj["anio"] == 2021].iloc[0]
    resumen = {
        "n_casos_completos_6_variables": int(n_cc),
        "periodo": list(WINDOW),
        "pearson_le_lnpib": float(pear.loc["esperanza_vida", "ln_pib"]),
        "spearman_le_lnpib": float(spear.loc["esperanza_vida", "ln_pib"]),
        "spearman_le_escolaridad": float(spear.loc["esperanza_vida", "escolaridad_promedio"]),
        "spearman_le_lngasto": float(spear.loc["esperanza_vida", "ln_gasto_pc"]),
        "pearson_mortinf_lnpib": float(pear.loc["mortalidad_infantil", "ln_pib"]),
        "r2_2021_lineal": float(y21["r2_lineal"]), "r2_2021_log": float(y21["r2_log"]),
        "r2_log_mayor_en_anios": int((aj["r2_log"] > aj["r2_lineal"]).sum()),
        "anios_evaluados": int(len(aj)),
        "sigma_1960": float(sig.loc[1960, "desv_est"]), "sigma_1990": float(sig.loc[1990, "desv_est"]),
        "sigma_2010": float(sig.loc[2010, "desv_est"]), "sigma_2023": float(sig.loc[2023, "desv_est"]),
        "sigma_max_anio": int(sig["desv_est"].idxmax()),
        "sigma_max": float(sig["desv_est"].max()),
        "brecha_regional_1960": float(sig.loc[1960, "brecha_regional_max_min"]),
        "brecha_regional_1990": float(sig.loc[1990, "brecha_regional_max_min"]),
        "brecha_regional_2023": float(sig.loc[2023, "brecha_regional_max_min"]),
        "beta_1990_2023": beta, "beta_2000_2023": beta_00,
    }
    (TABLAS / "resultados_eda.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

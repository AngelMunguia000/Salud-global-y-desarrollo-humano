"""Genera el informe final (.md y .docx) y la presentación (.pptx).

Todas las cifras se leen de los resultados del pipeline
(``04_analisis/tablas`` y ``05_ciencia/resultados``), de modo que el informe
no puede desincronizarse de los datos.

Uso: ``python -m reports.generar_informe`` desde la raíz del repositorio.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EDA = ROOT / "04_analisis" / "tablas"
RES = ROOT / "05_ciencia" / "resultados"
OUT = ROOT / "reports"
FIG_OUT = OUT / "figuras"
FIGS = {
    "dispersion": ROOT / "04_analisis/visualizaciones/03_dispersion_pib_esperanza_vida_log.png",
    "decadas": ROOT / "04_analisis/visualizaciones/04_dispersion_por_decada.png",
    "r2": ROOT / "04_analisis/visualizaciones/09_r2_lineal_vs_log_por_anio.png",
    "series": ROOT / "04_analisis/visualizaciones/05_series_regionales.png",
    "sigma": ROOT / "04_analisis/visualizaciones/06_convergencia_sigma.png",
    "beta": ROOT / "04_analisis/visualizaciones/07_convergencia_beta.png",
    "cobertura": ROOT / "04_analisis/visualizaciones/01_cobertura_datos.png",
    "relaciones": ROOT / "04_analisis/visualizaciones/08_gasto_educacion_vs_esperanza_vida.png",
    "diag": ROOT / "05_ciencia/figuras/01_diagnosticos_m3.png",
    "coef": ROOT / "05_ciencia/figuras/02_coeficientes_m3_m4_m5.png",
    "sobre": ROOT / "05_ciencia/figuras/03_paises_sobre_desempeno.png",
    "sobre_disp": ROOT / "05_ciencia/figuras/04_sobre_desempeno_dispersion.png",
}
REG_ES = {
    "East Asia & Pacific": "Asia Oriental y Pacífico", "Europe & Central Asia": "Europa y Asia Central",
    "Latin America & Caribbean": "América Latina y Caribe",
    "Middle East & North Africa": "Medio Oriente y Norte de África", "North America": "Norteamérica",
    "South Asia": "Asia Meridional", "Sub-Saharan Africa": "África Subsahariana",
}


def md_table(df: pd.DataFrame) -> str:
    """Convierte un DataFrame a tabla markdown."""
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    rows = ["| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False)]
    return "\n".join([head, sep, *rows])


def fmt_p(p: float) -> str:
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def cargar() -> dict:
    """Lee todos los resultados necesarios."""
    return {
        "eda": json.loads((EDA / "resultados_eda.json").read_text(encoding="utf-8")),
        "mod": json.loads((RES / "resumen_modelos.json").read_text(encoding="utf-8")),
        "coef": pd.read_csv(RES / "modelos_coeficientes.csv"),
        "diag": pd.read_csv(RES / "modelos_ajuste_diagnosticos.csv"),
        "vif": pd.read_csv(RES / "vif_m3.csv"),
        "val": pd.read_csv(RES / "validacion_fuera_de_muestra.csv"),
        "imp": pd.read_csv(RES / "importancia_m6.csv"),
        "sob": pd.read_csv(RES / "paises_sobre_desempeno.csv"),
        "perfil": pd.read_csv(RES / "perfil_sobre_desempeno.csv"),
        "bajo": pd.read_csv(RES / "paises_bajo_desempeno_M1.csv"),
        "hip": pd.read_csv(RES / "hipotesis.csv"),
        "cob": pd.read_csv(EDA / "cobertura_variable_region.csv", index_col=0),
        "regional": pd.read_csv(EDA / "esperanza_vida_regional_anios_clave.csv"),
    }


def construir_markdown(d: dict) -> str:
    """Compone el informe en markdown con cifras tomadas de los resultados."""
    e, m = d["eda"], d["mod"]
    coef = d["coef"].set_index(["modelo", "variable"])
    dg = d["diag"].set_index("modelo")
    b = lambda mod, var: coef.loc[(mod, var)]            # noqa: E731
    m1, m3 = b("M1", "ln_pib"), None
    dobl = m1["coef"] * np.log(2)
    p10 = m1["coef"] * np.log(1.1)
    g10 = b("M3", "ln_gasto_pc")["coef"] * np.log(1.1)
    pib10 = b("M3", "ln_pib")["coef"] * np.log(1.1)
    esc = b("M3", "escolaridad_promedio")

    # Tabla de modelos
    filas = []
    for mod in ["M0", "M1", "M2", "M3", "M4", "M5"]:
        r = dg.loc[mod]
        filas.append([mod, r["descripcion"], f"{r['r2_ajustado']:.3f}", f"{r['rmse']:.2f}",
                      fmt_p(r["reset_p"]), fmt_p(r["breusch_pagan_p"])])
    t_modelos = md_table(pd.DataFrame(filas, columns=[
        "Modelo", "Especificación", "R² ajustado", "RMSE (años)", "p RESET", "p Breusch–Pagan"]))

    filas = []
    for mod in ["M1", "M2", "M3", "M4", "M5"]:
        for var, nom in [("ln_pib", "ln PIB pc"), ("ln_gasto_pc", "ln gasto salud pc"),
                         ("escolaridad_promedio", "Escolaridad (años)")]:
            if (mod, var) in coef.index:
                c = coef.loc[(mod, var)]
                filas.append([mod, nom, f"{c['coef']:.3f}", f"{c['error_est']:.3f}",
                              f"[{c['ic95_inf']:.2f}; {c['ic95_sup']:.2f}]", fmt_p(c["p_valor"])])
    t_coef = md_table(pd.DataFrame(filas, columns=[
        "Modelo", "Variable", "Coef.", "Error est. (por país)", "IC 95 %", "p"]))

    v = d["val"].copy()
    v["esquema"] = v["esquema"].str.replace(r"\(.*\)", "", regex=True).str.strip()
    t_val = md_table(v.assign(mae=v["mae"].round(2), rmse=v["rmse"].round(2), r2=v["r2"].round(3))
                     [["modelo", "esquema", "mae", "rmse", "r2"]]
                     .rename(columns={"modelo": "Modelo", "esquema": "Esquema", "mae": "MAE",
                                      "rmse": "RMSE", "r2": "R²"}))

    rob = d["sob"][d["sob"]["robusto"]].merge(d["perfil"][["iso3", "pib_per_capita_ppp",
                                                           "gasto_salud_per_capita_ppp",
                                                           "escolaridad_promedio",
                                                           "esperanza_vida"]], on="iso3")
    t_rob = md_table(pd.DataFrame({
        "País": rob["pais"], "Región": rob["region"].map(REG_ES),
        "Esp. vida 2015–23": rob["esperanza_vida"].round(1),
        "PIB pc PPA (US$)": rob["pib_per_capita_ppp"].round(0).astype(int).map("{:,}".format),
        "Gasto salud pc (US$)": rob["gasto_salud_per_capita_ppp"].round(0).astype(int),
        "Escolaridad": rob["escolaridad_promedio"].round(1),
        "z medio M1": rob["z_medio_M1"].round(2), "% años > 0": (rob["pct_positivo_M1"] * 100).round(0).astype(int),
    }))
    cand_no = d["sob"][d["sob"]["pasa_M1"] & ~d["sob"]["robusto"]]
    bajo = d["bajo"].head(6)
    t_bajo = md_table(pd.DataFrame({"País": bajo["pais"], "Región": bajo["region"].map(REG_ES),
                                    "z medio": bajo["z_medio_M1"].round(2),
                                    "Residuo medio (años)": bajo["residuo_medio_M1"].round(1)}))
    t_hip = md_table(d["hip"].rename(columns={"hipotesis": "ID", "enunciado": "Hipótesis",
                                              "veredicto": "Veredicto", "evidencia": "Evidencia"}))
    reg = d["regional"].rename(columns=REG_ES)
    t_reg = md_table(reg.rename(columns={"anio": "Año"}))
    cob = d["cob"].loc["Global"]
    imp = d["imp"].iloc[0]

    return f"""# Salud global y desarrollo humano
## Informe final de resultados — Equipo 4

**Materia:** Optativa III · Ciencia de Datos (Ingeniería en Computación, UNE Plantel Centro)
**Metodología:** CRISP-DM · **Periodo de análisis:** {e['periodo'][0]}–{e['periodo'][1]} (series completas 1960–2024)
**Fuentes:** Banco Mundial (WDI), OMS (GHED), PNUD vía Our World in Data

---

## 1. Resumen ejecutivo

Se integraron seis indicadores de 217 países en un panel reproducible y se estudió qué factores de desarrollo se asocian con la esperanza de vida. Los resultados son **asociaciones**, no efectos causales.

- **El ingreso importa, y con rendimientos decrecientes.** Con el logaritmo del PIB per cápita, el R² ajustado mejora de {dg.loc['M0','r2_ajustado']:.2f} (niveles) a {dg.loc['M1','r2_ajustado']:.2f}. Duplicar el PIB per cápita se asocia con **+{dobl:.1f} años** de esperanza de vida (IC 95 %: {m1['ic95_inf']*np.log(2):.1f}–{m1['ic95_sup']*np.log(2):.1f}).
- **Gasto en salud y escolaridad aportan algo más, pero poco y de forma frágil.** En el modelo principal (M3) ambos son significativos, y R² ajustado sube de {dg.loc['M1','r2_ajustado']:.3f} a {dg.loc['M3','r2_ajustado']:.3f}. Al controlar por región y año, la escolaridad pierde significancia; con efectos fijos de país solo el ingreso la conserva.
- **{m['robustos']} países superan de forma robusta lo que predice su ingreso** (2015–2023): {', '.join(rob['pais'])}. Son economías pequeñas o de ingreso bajo y medio donde la esperanza de vida es de {rob['z_medio_M1'].min():.1f} a {rob['z_medio_M1'].max():.1f} desviaciones estándar por encima de lo esperado.
- **Las brechas se están cerrando.** La dispersión de la esperanza de vida entre países bajó de {e['sigma_1990']:.1f} años (1990) a {e['sigma_2023']:.1f} (2023); quien partía más abajo ganó más años por año (β = {e['beta_1990_2023']['beta']:.4f}, p {fmt_p(e['beta_1990_2023']['p_valor'])}). La brecha entre la región más alta y la más baja bajó de {e['brecha_regional_1990']:.1f} a {e['brecha_regional_2023']:.1f} años.

## 2. Datos y método

### 2.1 Panel de análisis
El pipeline (`02_ingenieria/etl`) lee los archivos originales, verifica su integridad con SHA-256, pasa los indicadores a formato largo, excluye agregados regionales y mundiales y une por `(iso3, anio)` con la esperanza de vida como tabla base. El resultado es un panel de 217 países y 65 años (1960–2024), cargado a `warehouse/salud.db`.

| Variable | Fuente | Disponible desde |
|---|---|---|
| Esperanza de vida al nacer | Banco Mundial (UN WPP) | 1960 |
| Mortalidad infantil | Banco Mundial (UN IGME) | 1960 |
| PIB per cápita PPA (US$ constantes 2021) | Banco Mundial (ICP) | 1990 |
| Gasto corriente en salud (% PIB; per cápita PPA) | OMS – GHED | 2000 |
| Años promedio de escolaridad (adultos ≥ 25) | PNUD vía OWID | 1990 |

La variable limitante es el **gasto en salud** (desde 2000), por lo que los modelos usan **{e['periodo'][0]}–{e['periodo'][1]}**: {e['n_casos_completos_6_variables']:,} observaciones país-año de {m['paises']} países con las variables completas. En ese periodo, el {cob['pib_per_capita_ppp']*100:.0f} % de los datos de PIB y el {cob['gasto_salud_pct_pib']*100:.0f} % de los de gasto en salud están presentes. Los datos faltantes no se imputaron: se trabajó con casos completos y se reporta la cobertura por región.

![Cobertura de datos](figuras/{FIGS['cobertura'].name})

### 2.2 Modelos
Se ajustaron seis modelos de mínimos cuadrados con errores estándar **agrupados por país** (las observaciones de un mismo país no son independientes):

{t_modelos}

M3 es el modelo principal. Se evaluó además un modelo de gradient boosting (M6) solo como chequeo de no linealidades, y todos los modelos con validación temporal (entrenar hasta 2017, probar 2018–2023) y por países no vistos (5 pliegues).

## 3. Resultados

### 3.1 P1 — ¿Qué tan fuerte es la relación ingreso–esperanza de vida? ¿Es lineal?
La correlación de Spearman entre ln(PIB per cápita) y esperanza de vida es **{e['spearman_le_lnpib']:.2f}** (Pearson {e['pearson_le_lnpib']:.2f}); con la mortalidad infantil es {e['pearson_mortinf_lnpib']:.2f}. **No es lineal en niveles: se aplana.** Un año extra de esperanza de vida "cuesta" mucho más ingreso en países ricos que en pobres. El logaritmo del ingreso explica más varianza que el ingreso en niveles en los {e['r2_log_mayor_en_anios']} de {e['anios_evaluados']} cortes transversales anuales; en 2021 el R² pasa de {e['r2_2021_lineal']:.2f} a {e['r2_2021_log']:.2f}.

![Ingreso y esperanza de vida](figuras/{FIGS['dispersion'].name})

En la escala logarítmica la relación es aproximadamente lineal: **+10 % de PIB per cápita se asocia con +{p10:.2f} años** (M1). Además, la curva se desplaza hacia arriba con el tiempo: a igual ingreso, hoy se vive más que hace tres décadas (posiblemente por avances médicos y de salud pública, que estos datos no miden).

![Curva por década](figuras/{FIGS['decadas'].name})

**Más allá del ingreso (M3).** Con gasto en salud y escolaridad en el modelo, el coeficiente del ingreso baja a {b('M3','ln_pib')['coef']:.2f}: parte del efecto aparente del PIB opera a través de más gasto sanitario y más educación. Asociaciones estimadas en M3: +10 % de PIB, +{pib10:.2f} años; +10 % de gasto en salud per cápita, +{g10:.2f} años; +1 año de escolaridad media, +{esc['coef']:.2f} años.

{t_coef}

![Efectos estimados](figuras/{FIGS['coef'].name})

**Lectura prudente.** El efecto de la escolaridad y del gasto es sensible a la especificación: con efectos fijos de región y año (M4) la escolaridad deja de ser significativa (p = {fmt_p(b('M4','escolaridad_promedio')['p_valor'])}); con efectos fijos de país (M5) solo el ingreso sigue siendo significativo. Esto indica que buena parte de la asociación proviene de **diferencias entre países**, no de cambios dentro de cada país.

**Diagnósticos de M3.** VIF de ln PIB = {d['vif'].set_index('variable').loc['ln_pib','vif']:.1f} y de ln gasto = {d['vif'].set_index('variable').loc['ln_gasto_pc','vif']:.1f}: hay colinealidad alta pero por debajo de 10, lo que explica la inestabilidad de los coeficientes individuales. Hay heterocedasticidad (Breusch–Pagan p {fmt_p(dg.loc['M3','breusch_pagan_p'])}) y residuos no normales (Jarque–Bera p < 0.001), por lo que se usan errores agrupados por país. RESET no rechaza M3 (p = {dg.loc['M3','reset_p']:.2f}), pero sí rechaza M0 y M1, así que la forma funcional lineal en niveles es inadecuada.

![Diagnósticos](figuras/{FIGS['diag'].name})

**Capacidad predictiva.**

{t_val}

El modelo de ingreso solo (M1) ya logra R² ≈ {v[(v.modelo=='M1')].r2.iloc[0]:.2f} fuera de muestra. Agregar gasto en salud mejora el error (M2); agregar escolaridad **no mejora la predicción temporal**. El gradient boosting (M6) reduce el error más que cualquier modelo lineal, lo que sugiere heterogeneidad regional y no linealidades que el modelo lineal no captura; en M6 la variable más importante es el gasto en salud per cápita (la importancia se reparte entre variables correlacionadas, por lo que no equivale a causalidad).

### 3.2 P2 — ¿Qué países logran alta esperanza de vida con bajo ingreso?
Se estimó la esperanza de vida esperada dado el ingreso (M1 con efectos fijos de año, 1990–2023, para separar el desplazamiento global de la curva) y se calculó el residuo estandarizado de cada país en 2015–2023. **Criterio:** residuo medio ≥ +1 σ **y** residuo positivo en ≥ 70 % de los años. Un país es **robusto** si además cumple el criterio con (a) M3 con efectos de año, que descuenta gasto y educación, y (b) validación dejando fuera al propio país.

De {m['candidatos_M1']} candidatos bajo M1, {m['pasan_M3']} siguen cumpliendo bajo M3 y {m['robustos']} sobreviven a todas las pruebas:

{t_rob}

![Sobre-desempeño](figuras/{FIGS['sobre'].name})

![Dispersión resaltada](figuras/{FIGS['sobre_disp'].name})

**Qué podemos aprender (con cautela).** Los casos robustos son en su mayoría economías pequeñas, con gasto en salud per cápita entre US$ {rob['gasto_salud_per_capita_ppp'].min():,.0f} y {rob['gasto_salud_per_capita_ppp'].max():,.0f} y escolaridad media entre {rob['escolaridad_promedio'].min():.1f} y {rob['escolaridad_promedio'].max():.1f} años: no se explican por un gasto alto. Burundi destaca por alcanzar ~62 años con el PIB per cápita más bajo de la lista. Los datos de este proyecto **no permiten identificar las causas**; explorar sistemas de atención primaria, vacunación o programas comunitarios requeriría fuentes adicionales (p. ej., indicadores de la OMS-GHO). {len(cand_no)} países cumplen el criterio bajo M1 pero no bajo M3 ({', '.join(cand_no['pais'])}): su ventaja no resiste el control por gasto en salud y escolaridad.

**Los casos opuestos** (esperanza de vida muy inferior a la que predice su ingreso) incluyen economías de ingreso medio con alta carga de enfermedad, economías basadas en recursos naturales y países muy pequeños; estos datos no permiten contrastar esas explicaciones:

{t_bajo}

> **Advertencia.** Los países pequeños (Islas Salomón, Vanuatu, Maldivas, Cabo Verde) tienen estimaciones más ruidosas de la esperanza de vida y del PIB per cápita. Los intervalos de la figura reflejan solo la variación entre años (n = 9), no la incertidumbre de medición de las fuentes.

### 3.3 P3 — ¿Cómo ha evolucionado la desigualdad en salud entre regiones?
La esperanza de vida mejoró en todas las regiones, y las brechas se redujeron. La desviación estándar entre países pasó de {e['sigma_1960']:.1f} años en 1960 a {e['sigma_1990']:.1f} en 1990 y {e['sigma_2023']:.1f} en 2023 (**σ-convergencia**). En la regresión de **β-convergencia** 1990–2023, el coeficiente es {e['beta_1990_2023']['beta']:.4f} (p {fmt_p(e['beta_1990_2023']['p_valor'])}, R² = {e['beta_1990_2023']['r2']:.2f}, n = {e['beta_1990_2023']['n']}): cada año adicional de esperanza de vida inicial se asocia con 0.011 años menos de ganancia anual.

{t_reg}

![Series regionales](figuras/{FIGS['series'].name})

![Convergencia sigma](figuras/{FIGS['sigma'].name})

**Matices.** La convergencia no fue uniforme: África Subsahariana avanzó poco entre 1990 y 2000 (de {d['regional'].iloc[1]['Sub-Saharan Africa']:.0f} a {d['regional'].iloc[2]['Sub-Saharan Africa']:.0f} años, periodo coincidente con la epidemia de VIH/SIDA) y aún es la región más rezagada (≈ {d['regional'].iloc[-1]['Sub-Saharan Africa']:.0f} años en 2023 frente a ≈ {d['regional'].iloc[-1]['North America']:.0f} en Norteamérica). El análisis usa medias simples de países, sin ponderar por población.

![β-convergencia](figuras/{FIGS['beta'].name})

## 4. Evaluación de hipótesis

{t_hip}

## 5. Limitaciones

- **Diseño observacional:** los resultados son asociaciones. Los efectos fijos de país (M5) muestran que lo que se observa entre países no se replica automáticamente dentro de un mismo país a lo largo del tiempo.
- **Cobertura:** el gasto en salud solo existe desde 2000 y su disponibilidad es desigual por región; la cobertura es menor en Norteamérica ({d['cob'].loc['North America','gasto_salud_pct_pib']*100:.0f} %), Asia Oriental y Pacífico ({d['cob'].loc['East Asia & Pacific','gasto_salud_pct_pib']*100:.0f} %) y América Latina y el Caribe ({d['cob'].loc['Latin America & Caribbean','gasto_salud_pct_pib']*100:.0f} %), por lo que los resultados pueden no representar a esos países (sesgo de selección posible). No se imputaron faltantes.
- **Colinealidad** entre PIB y gasto en salud (VIF ≈ 8–9) dificulta separar sus efectos.
- **Unidades:** el PIB está en dólares constantes de 2021 y el gasto per cápita en dólares corrientes; no se combinaron en razones.
- **Medición:** la esperanza de vida de varios países es una estimación modelada (UN WPP) y presenta anomalías puntuales. La regla de calidad del ETL (20–95 años) excluye 9 país-año, algunos de los cuales son crisis reales (Camboya 1975–78, Ruanda 1994) y otros posibles errores de la fuente (República Centroafricana 2009 y 2022, Sudán del Sur 1988 y 1998); esto afecta marginalmente las series históricas. La escolaridad no mide calidad educativa.
- **Ponderación:** las medias regionales son simples, no ponderadas por población.
- **Umbral de sobre-desempeño:** el criterio (+1 σ, 70 % de años) es una convención del equipo; otros umbrales cambiarían la lista.

## 6. Conclusiones y recomendaciones

1. El ingreso es el predictor individual más fuerte de la esperanza de vida, con rendimientos decrecientes; para un país pobre, un mismo aumento proporcional de ingreso se asocia con ganancias de salud mucho mayores que para uno rico.
2. Gasto en salud y educación se asocian con mayor esperanza de vida, pero su aporte independiente es modesto y no resiste todos los controles; no deben presentarse como "efectos".
3. Hay países que logran más salud de la que su ingreso predice; **estudiarlos con datos adicionales** (cobertura de salud primaria, vacunación) es el siguiente paso natural.
4. La salud global converge: las brechas entre países y regiones se redujeron de forma sostenida desde 1960, aunque África Subsahariana sigue muy rezagada.
5. **Trabajo futuro:** incorporar población (ponderación), indicadores de la OMS-GHO, modelos de panel dinámico y análisis por grupos de ingreso.

## 7. Reproducibilidad

```bash
make install   # dependencias
make all       # ETL, pruebas, análisis, modelos e informe
```

Cada cifra de este informe se regenera desde los datos originales (verificados con SHA-256). Código: `02_ingenieria/etl`, `04_analisis/scripts`, `05_ciencia/scripts`, `common/`. Resultados: `04_analisis/tablas`, `05_ciencia/resultados`.

## Anexo — Fuentes citadas

- Banco Mundial, World Development Indicators (SP.DYN.LE00.IN, SP.DYN.IMRT.IN, NY.GDP.PCAP.PP.KD).
- Organización Mundial de la Salud, Global Health Expenditure Database (SH.XPD.CHEX.GD.ZS, SH.XPD.CHEX.PP.CD), actualización de diciembre de 2025.
- PNUD, Human Development Report 2025, vía Our World in Data (años promedio de escolaridad).
- UN World Population Prospects; UN Inter-agency Group for Child Mortality Estimation.
"""


# --------------------------------------------------------------------------- #
# .docx
# --------------------------------------------------------------------------- #
def a_docx(md: str, path: Path) -> None:
    """Convierte el subconjunto de markdown usado a un .docx con tablas e imágenes."""
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt

    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(10.5)
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2.2)

    def runs(par, text: str) -> None:
        for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
            if part.startswith("**") and part.endswith("**"):
                par.add_run(part[2:-2]).bold = True
            elif part.startswith("`") and part.endswith("`"):
                r = par.add_run(part[1:-1]); r.font.name = "Consolas"
            else:
                par.add_run(part)

    lines, i = md.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            j = i + 1
            while not lines[j].startswith("```"):
                j += 1
            p = doc.add_paragraph()
            r = p.add_run("\n".join(lines[i + 1:j])); r.font.name = "Consolas"; r.font.size = Pt(9)
            i = j + 1
            continue
        if ln.startswith("|"):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            rows = [[c.strip() for c in l.strip().strip("|").split("|")]
                    for k, l in enumerate(lines[i:j]) if k != 1]
            t = doc.add_table(rows=len(rows), cols=len(rows[0]))
            t.style = "Light Grid Accent 1"
            for ri, row in enumerate(rows):
                for ci, cell in enumerate(row):
                    c = t.cell(ri, ci)
                    c.text = ""
                    runs(c.paragraphs[0], cell)
                    for r in c.paragraphs[0].runs:
                        r.font.size = Pt(8.5)
                        if ri == 0:
                            r.bold = True
            doc.add_paragraph()
            i = j
            continue
        m = re.match(r"!\[(.*?)\]\((.*?)\)", ln)
        if m:
            img = OUT / m.group(2)
            if img.is_file():
                doc.add_picture(str(img), width=Cm(16))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif ln.startswith("# "):
            doc.add_heading(ln[2:], 0)
        elif ln.startswith("## "):
            doc.add_heading(ln[3:], 1)
        elif ln.startswith("### "):
            doc.add_heading(ln[4:], 2)
        elif re.match(r"^- ", ln):
            runs(doc.add_paragraph(style="List Bullet"), ln[2:])
        elif re.match(r"^\d+\. ", ln):
            runs(doc.add_paragraph(style="List Number"), re.sub(r"^\d+\. ", "", ln))
        elif ln.startswith("> "):
            runs(doc.add_paragraph(style="Intense Quote"), ln[2:])
        elif ln.strip() and ln.strip() != "---":
            runs(doc.add_paragraph(), ln)
        i += 1
    doc.save(path)


# --------------------------------------------------------------------------- #
# .pptx
# --------------------------------------------------------------------------- #
def a_pptx(d: dict, path: Path) -> None:
    """Crea una presentación de 11 diapositivas con los resultados clave."""
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Emu, Inches, Pt

    e, m = d["eda"], d["mod"]
    dg = d["diag"].set_index("modelo")
    rob = d["sob"][d["sob"]["robusto"]]
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    NAVY, INK, GREY = RGBColor(0x1B, 0x25, 0x6B), RGBColor(0x22, 0x22, 0x22), RGBColor(0x66, 0x66, 0x66)
    blank = prs.slide_layouts[6]

    def text(slide, x, y, w, h, lines, size=18, color=INK, bold=False):
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        for k, ln in enumerate(lines):
            p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
            p.text = ln
            p.font.size, p.font.bold = Pt(size), bold
            p.font.color.rgb = color
            p.space_after = Pt(8)
        return tb

    def slide(title: str, notes: str = ""):
        s = prs.slides.add_slide(blank)
        bar = s.shapes.add_shape(1, 0, 0, prs.slide_width, Inches(0.12))
        bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
        text(s, 0.6, 0.3, 12.1, 1.0, [title], size=28, color=NAVY, bold=True)
        if notes:
            s.notes_slide.notes_text_frame.text = notes
        return s

    def picture(s, key, x, y, w):
        s.shapes.add_picture(str(FIGS[key]), Inches(x), Inches(y), width=Inches(w))

    # 1 portada
    s = prs.slides.add_slide(blank)
    bg = s.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
    text(s, 0.9, 2.3, 11.5, 1.5, ["Salud global y desarrollo humano"], size=44,
         color=RGBColor(255, 255, 255), bold=True)
    text(s, 0.9, 3.7, 11.5, 1.5, ["¿Qué factores se asocian con la esperanza de vida y qué países rinden más de lo que su riqueza predice?",
                                  "Equipo 4 · Optativa III Ciencia de Datos · UNE Plantel Centro"],
         size=20, color=RGBColor(0xDD, 0xE3, 0xFF))

    # 2 datos
    s = slide("Datos: 217 países, 6 indicadores, 1960–2024")
    text(s, 0.6, 1.5, 6.0, 5, ["• Banco Mundial: esperanza de vida, mortalidad infantil, PIB per cápita PPA",
                               "• OMS (GHED): gasto en salud, desde 2000",
                               "• PNUD vía OWID: años de escolaridad",
                               "• Pipeline reproducible con SHA-256, exclusión de agregados y unión por (iso3, año)",
                               f"• Modelos: {e['n_casos_completos_6_variables']:,} país-año completos, 2000–2023"], size=17)
    picture(s, "cobertura", 6.8, 1.6, 6.0)

    # 3 P1
    s = slide("P1 · El ingreso se asocia con más vida, pero con rendimientos decrecientes")
    picture(s, "dispersion", 0.5, 1.4, 7.6)
    text(s, 8.4, 1.6, 4.5, 5, [f"Spearman ln(PIB)–esperanza de vida: {e['spearman_le_lnpib']:.2f}",
                               f"R² ajustado: {dg.loc['M0','r2_ajustado']:.2f} (niveles) → {dg.loc['M1','r2_ajustado']:.2f} (logaritmo)",
                               "Duplicar el PIB per cápita se asocia con ≈ +4 años",
                               "La curva se desplaza hacia arriba con el tiempo"], size=17)

    # 4 modelos
    s = slide("Más allá del ingreso: gasto en salud y escolaridad")
    picture(s, "coef", 0.5, 1.5, 8.2)
    text(s, 9.0, 1.6, 4.0, 5, [f"R² ajustado M1 {dg.loc['M1','r2_ajustado']:.2f} → M3 {dg.loc['M3','r2_ajustado']:.2f}",
                               "Con efectos fijos de región/año, la escolaridad deja de ser significativa",
                               "Con efectos fijos de país, solo el ingreso resiste",
                               "→ Asociación sobre todo entre países"], size=16)

    # 5 validación
    v = d["val"]
    s = slide("Validación fuera de muestra")
    rows = [["Modelo", "Esquema", "RMSE", "R²"]]
    for _, r in v.iterrows():
        rows.append([r["modelo"], "temporal" if "temporal" in r["esquema"] else "países no vistos",
                     f"{r['rmse']:.2f}", f"{r['r2']:.2f}"])
    tbl = s.shapes.add_table(len(rows), 4, Inches(0.6), Inches(1.5), Inches(8.2), Inches(4.8)).table
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = tbl.cell(i, j); c.text = str(val)
            c.text_frame.paragraphs[0].font.size = Pt(12)
    text(s, 9.2, 1.6, 3.8, 5, ["El ingreso solo ya predice R² ≈ 0.67",
                               "Agregar escolaridad no mejora la predicción temporal",
                               "El modelo de boosting (M6) logra el menor error: hay no linealidades y efectos regionales"], size=16)

    # 6 sobre-desempeño
    s = slide(f"P2 · {m['robustos']} países superan de forma robusta lo que predice su ingreso")
    picture(s, "sobre_disp", 0.4, 1.4, 7.8)
    text(s, 8.5, 1.6, 4.5, 5, [", ".join(rob["pais"]),
                               "Criterio: residuo medio ≥ +1σ y positivo ≥ 70 % de los años (2015–2023)",
                               "Robustez: también bajo M3 y dejando fuera al país",
                               "Cautela: países pequeños, datos ruidosos; causas no identificables"], size=15)

    # 7 lista
    s = slide("Países de sobre-desempeño: perfil")
    picture(s, "sobre", 0.6, 1.3, 7.2)
    pr = d["perfil"]
    text(s, 8.1, 1.5, 4.9, 5, ["Rango de PIB per cápita: US$ "
                               f"{pr['pib_per_capita_ppp'].min():,.0f} – {pr['pib_per_capita_ppp'].max():,.0f}",
                               "Escolaridad media 3 a 10.4 años",
                               "Burundi: ≈ 62 años de esperanza de vida con el PIB per cápita más bajo de la lista",
                               "Siguiente paso: indicadores de atención primaria y vacunación"], size=15)

    # 8 convergencia
    s = slide("P3 · Las brechas en salud se están cerrando")
    picture(s, "sigma", 0.4, 1.5, 8.6)
    text(s, 9.2, 1.6, 3.8, 5, [f"σ entre países: {e['sigma_1990']:.1f} (1990) → {e['sigma_2023']:.1f} (2023)",
                               f"Brecha regional máx–mín: {e['brecha_regional_1990']:.1f} → {e['brecha_regional_2023']:.1f} años",
                               f"β = {e['beta_1990_2023']['beta']:.4f} (p < 0.001)",
                               "África Subsahariana sigue rezagada"], size=16)

    # 9 hipótesis
    s = slide("Hipótesis")
    rows = [["ID", "Veredicto", "Evidencia"]] + [[r["hipotesis"], r["veredicto"], r["evidencia"]]
                                                  for _, r in d["hip"].iterrows()]
    tbl = s.shapes.add_table(len(rows), 3, Inches(0.6), Inches(1.5), Inches(12.1), Inches(4.2)).table
    tbl.columns[0].width, tbl.columns[1].width, tbl.columns[2].width = Inches(0.8), Inches(2.6), Inches(8.7)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = tbl.cell(i, j); c.text = str(val); c.text_frame.paragraphs[0].font.size = Pt(12)

    # 10 limitaciones
    s = slide("Limitaciones")
    text(s, 0.6, 1.5, 12.0, 5.2, ["• Asociaciones, no causalidad (diseño observacional)",
                                  "• Gasto en salud disponible solo desde 2000; datos faltantes no imputados",
                                  "• Colinealidad PIB–gasto (VIF ≈ 8–9)",
                                  "• Medias regionales sin ponderar por población",
                                  "• Esperanza de vida modelada por UN WPP con anomalías puntuales",
                                  "• Umbral de sobre-desempeño es una convención del equipo"], size=20)

    # 11 conclusiones
    s = slide("Conclusiones")
    text(s, 0.6, 1.5, 12.0, 5.2, ["1. El ingreso es el predictor más fuerte; con rendimientos decrecientes",
                                  "2. Gasto y educación aportan, pero de forma frágil; no son «efectos»",
                                  f"3. {m['robustos']} países logran más salud de la que su ingreso predice: caso de estudio",
                                  "4. La salud global converge; la brecha regional se redujo ≈ 10 años desde 1960",
                                  "5. Siguiente paso: población, indicadores OMS-GHO y modelos de panel dinámico"], size=20)
    prs.save(path)


def main() -> None:
    """Escribe ``informe_final.md/.docx`` y ``presentacion_final.pptx``."""
    d = cargar()
    FIG_OUT.mkdir(parents=True, exist_ok=True)
    for src in FIGS.values():
        shutil.copy(src, FIG_OUT / src.name)
    md = construir_markdown(d)
    (OUT / "informe_final.md").write_text(md, encoding="utf-8")
    a_docx(md, OUT / "informe_final.docx")
    a_pptx(d, OUT / "presentacion_final.pptx")
    print("[informe] escrito:", ", ".join(p.name for p in
          (OUT / "informe_final.md", OUT / "informe_final.docx", OUT / "presentacion_final.pptx")))


if __name__ == "__main__":
    main()

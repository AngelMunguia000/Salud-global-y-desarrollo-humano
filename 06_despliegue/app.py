"""Aplicación Streamlit del proyecto: sigue los cinco momentos de la rúbrica de presentación.

Solo lee resultados ya generados (`make all`); no entrena modelos. Ejecutar desde la raíz:
    streamlit run 06_despliegue/app.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # Streamlit solo agrega la carpeta del script al path

from common.panel import RECENT_WINDOW, WINDOW, add_derived, load_panel  # noqa: E402
from common.style import COLORES, FUENTE, REGIONES_ES  # noqa: E402

TABLAS = ROOT / "04_analisis" / "tablas"
RESULTADOS = ROOT / "05_ciencia" / "resultados"
FIGURAS = ROOT / "reports" / "figuras"
COLORES_ES = {REGIONES_ES[k]: v for k, v in COLORES.items()}

st.set_page_config(page_title="Salud global y desarrollo humano", page_icon="🌍", layout="wide")


@st.cache_data
def panel() -> pd.DataFrame:
    data = add_derived(load_panel())
    data["region_es"] = data["region"].map(REGIONES_ES)
    return data


@st.cache_data
def csv(carpeta: Path, nombre: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(carpeta / nombre, **kwargs)


@st.cache_data
def resumen() -> dict:
    eda = json.loads((TABLAS / "resultados_eda.json").read_text(encoding="utf-8"))
    modelos = json.loads((RESULTADOS / "resumen_modelos.json").read_text(encoding="utf-8"))
    return {**eda, **modelos}


def por_que(texto: str) -> None:
    """Caja de justificación: la rúbrica pide explicar el porqué de cada dato y método."""
    st.info(f"**¿Por qué?** {texto}", icon="💡")


def figura(nombre: str, pie: str) -> None:
    st.image(str(FIGURAS / nombre), caption=pie, width="stretch")


# ---------------------------------------------------------------- 1. Problema y pregunta
def pagina_problema() -> None:
    r = resumen()
    st.title("Salud global y desarrollo humano")
    st.caption("Equipo 4 · Optativa III: Ciencia de Datos · UNE Plantel Centro")
    st.markdown(
        "### Pregunta central\n"
        "> **¿Qué países alcanzan una esperanza de vida superior a la que cabría esperar "
        "según su nivel de ingreso y otros indicadores de desarrollo?**"
    )
    st.markdown(
        "Dos países con el mismo ingreso pueden tener esperanzas de vida muy distintas. "
        "Si encontramos a los que logran *más salud con menos recursos*, tenemos casos concretos "
        "de los que otros países pueden aprender."
    )
    c = st.columns(4)
    c[0].metric("Países en el panel", "217")
    c[1].metric("Periodo de las series", "1960–2024")
    c[2].metric("Observaciones completas", f"{r['n']:,}", help=f"País-año con las 6 variables, {WINDOW[0]}–{WINDOW[1]}")
    c[3].metric("Países con sobre-desempeño robusto", r["robustos"])
    st.markdown(
        "**Preguntas de investigación**\n"
        "1. ¿Qué tan fuerte es la relación entre ingreso y esperanza de vida, y es lineal?\n"
        "2. ¿Qué países logran alta esperanza de vida con bajo ingreso?\n"
        "3. ¿Cómo ha evolucionado la desigualdad en salud entre regiones?"
    )
    st.warning("Todos los resultados son **asociaciones**, no efectos causales: es un diseño observacional.")


# ---------------------------------------------------------------- 2. Justificación de los datos
def pagina_datos() -> None:
    st.title("Los datos")
    st.markdown(
        "| Variable | Fuente | Desde |\n|---|---|---|\n"
        "| Esperanza de vida al nacer (variable objetivo) | Banco Mundial (UN WPP) | 1960 |\n"
        "| Mortalidad infantil | Banco Mundial (UN IGME) | 1960 |\n"
        "| PIB per cápita PPA (US$ constantes 2021) | Banco Mundial (ICP) | 1990 |\n"
        "| Gasto en salud (% PIB y per cápita PPA) | OMS – GHED | 2000 |\n"
        "| Años promedio de escolaridad (≥ 25 años) | PNUD vía Our World in Data | 1990 |"
    )
    por_que(
        "Banco Mundial y OMS son las fuentes oficiales con **metodología armonizada entre países**, "
        "licencia abierta (CC BY 4.0) y códigos ISO3 que permiten unirlas sin ambigüedad. "
        "Las variables cubren las tres dimensiones del desarrollo humano del PNUD: **salud, ingreso y educación**. "
        "No usamos la esperanza de vida de OWID porque duplica la misma serie (UN WPP)."
    )
    por_que(
        f"Modelamos **{WINDOW[0]}–{WINDOW[1]}** porque el gasto en salud de la OMS solo existe desde 2000: "
        "es la intersección donde las seis variables están disponibles."
    )
    st.subheader("Cobertura por región")
    cobertura = csv(TABLAS, "cobertura_variable_region.csv", index_col="region")
    cobertura.index = cobertura.index.map(REGIONES_ES)
    st.plotly_chart(
        px.imshow((cobertura * 100).round(0), text_auto=True, color_continuous_scale="Blues",
                  labels={"color": "% con dato"}, aspect="auto"),
        width="stretch",
    )
    por_que(
        "Mostramos la cobertura porque **condiciona qué tan representativos son los resultados**: "
        "Norteamérica, Asia Oriental y América Latina tienen menos datos de gasto, así que ahí hay posible sesgo de selección."
    )


# ---------------------------------------------------------------- 3. Preparación de los datos
def pagina_preparacion() -> None:
    st.title("Preparación de los datos")
    st.markdown("Pipeline ETL reproducible: archivos originales → verificación SHA-256 → formato largo → unión → DuckDB.")
    decisiones = [
        ("Unir solo por `(iso3, año)`", "Los nombres de país difieren entre Banco Mundial y OWID; el código ISO3 es único.", "Unir por nombre"),
        ("Excluir agregados (Mundo, regiones, grupos de ingreso)", "No son países: duplicarían observaciones y sesgarían los modelos.", "Lista manual de códigos"),
        ("Esperanza de vida como tabla base (left join)", "Es la variable objetivo; evita multiplicar filas.", "Outer join"),
        ("**No imputar** faltantes", "Ausencia ≠ cero. Imputar gasto en salud de 200+ países crearía datos sintéticos; preferimos 4,339 observaciones reales.", "Mediana o MICE"),
        ("Logaritmo del PIB y del gasto per cápita", "Rendimientos decrecientes: un dólar extra vale más en un país pobre que en uno rico.", "Niveles"),
        ("Errores estándar agrupados por país", "Las observaciones de un mismo país a lo largo del tiempo no son independientes.", "Errores sin agrupar"),
        ("Regla de calidad 20–95 años", "Excluye 9 país-año extremos (p. ej. Camboya 1975–78, Ruanda 1994); los originales no se tocan.", "Conservarlos sin marcar"),
    ]
    st.table(pd.DataFrame(decisiones, columns=["Decisión", "Razón", "Alternativa descartada"]))
    por_que(
        "Cada decisión tiene una alternativa descartada: así podemos defender que **no fue arbitraria**. "
        "El registro completo está en `docs/decisiones.md`."
    )
    st.subheader("¿El logaritmo de verdad ayuda?")
    r2 = csv(TABLAS, "r2_lineal_vs_log_por_anio.csv")
    fig = px.line(r2, x="anio", y=["r2_lineal", "r2_log"], markers=True,
                  labels={"anio": "Año", "value": "R²", "variable": "Escala del PIB"})
    fig.for_each_trace(lambda t: t.update(name={"r2_lineal": "Niveles", "r2_log": "Logaritmo"}[t.name]))
    st.plotly_chart(fig, width="stretch")
    por_que(
        f"Comparamos año por año para no depender de un solo corte: el logaritmo explica más varianza "
        f"en **{resumen()['r2_log_mayor_en_anios']} de {resumen()['anios_evaluados']} años**."
    )


# ---------------------------------------------------------------- 4. Análisis y hallazgos
def pagina_analisis() -> None:
    st.title("Análisis y hallazgos")
    t1, t2, t3, t4 = st.tabs(["Explorador", "P1 · Ingreso y modelos", "P2 · Sobre-desempeño", "P3 · Convergencia"])

    with t1:
        data = panel()
        anios = sorted(data.dropna(subset=["pib_per_capita_ppp", "esperanza_vida"])["anio"].unique())
        anio = st.select_slider("Año", options=anios, value=anios[-2] if len(anios) > 1 else anios[0])
        corte = data[(data["anio"] == anio)].dropna(subset=["pib_per_capita_ppp", "esperanza_vida"])
        fig = px.scatter(corte, x="pib_per_capita_ppp", y="esperanza_vida", color="region_es", log_x=True,
                         hover_name="pais", color_discrete_map=COLORES_ES,
                         labels={"pib_per_capita_ppp": "PIB per cápita PPA (US$ 2021, escala log)",
                                 "esperanza_vida": "Esperanza de vida (años)", "region_es": "Región"})
        st.plotly_chart(fig, width="stretch")
        por_que("Eje X en **escala logarítmica**: así la relación se ve casi lineal y los países pobres no quedan amontonados a la izquierda.")
        paises = st.multiselect("Comparar países en el tiempo", sorted(data["pais"].dropna().unique()),
                                default=["Mexico", "Cabo Verde", "Jordan"])
        if paises:
            serie = data[data["pais"].isin(paises)]
            st.plotly_chart(px.line(serie, x="anio", y="esperanza_vida", color="pais",
                                    labels={"anio": "Año", "esperanza_vida": "Esperanza de vida (años)", "pais": "País"}),
                            width="stretch")

    with t2:
        ajuste = csv(RESULTADOS, "modelos_ajuste_diagnosticos.csv")
        st.dataframe(ajuste[["modelo", "descripcion", "r2_ajustado", "rmse"]].round(3)
                     .rename(columns={"descripcion": "Especificación", "r2_ajustado": "R² ajustado", "rmse": "RMSE (años)"}),
                     hide_index=True, width="stretch")
        por_que(
            "Construimos los modelos **de menor a mayor** (M0 → M5) para ver qué aporta cada variable. "
            "M3 es el principal; M4 y M5 agregan efectos fijos para comprobar si el resultado sobrevive "
            "a diferencias no observadas entre regiones, países y años."
        )
        figura("02_coeficientes_m3_m4_m5.png", "Coeficientes con IC 95 % (errores agrupados por país)")
        st.markdown(
            "**Hallazgo:** duplicar el PIB per cápita se asocia con **+4.2 años** de esperanza de vida. "
            "Gasto en salud y escolaridad aportan, pero de forma **frágil**: con efectos fijos de país solo el ingreso sigue siendo significativo."
        )
        st.subheader("Validación fuera de muestra")
        val = csv(RESULTADOS, "validacion_fuera_de_muestra.csv")
        st.plotly_chart(px.bar(val, x="modelo", y="rmse", color="esquema", barmode="group",
                               labels={"rmse": "RMSE (años, menor es mejor)", "modelo": "Modelo", "esquema": "Esquema"}),
                        width="stretch")
        por_que(
            "Dos esquemas responden dos usos distintos: **temporal** (¿sirve para predecir el futuro?) y "
            "**países no vistos** (¿sirve para países sin datos?). El gradient boosting (M6) es solo un *benchmark*: "
            "que gane indica no linealidades que el modelo lineal no captura."
        )
        vif = csv(RESULTADOS, "vif_m3.csv")
        st.caption("VIF de M3: " + ", ".join(f"{v} = {x:.1f}" for v, x in zip(vif["variable"], vif["vif"]))
                   + " → colinealidad alta entre PIB y gasto (< 10), por eso los coeficientes individuales son inestables.")

    with t3:
        robustos = csv(RESULTADOS, "paises_sobre_desempeno.csv").query("robusto")
        perfil = csv(RESULTADOS, "perfil_sobre_desempeno.csv")
        tabla = robustos[["iso3", "pais", "region", "z_medio_M1", "residuo_medio_M1"]].merge(
            perfil[["iso3", "esperanza_vida", "pib_per_capita_ppp", "gasto_salud_per_capita_ppp"]], on="iso3")
        tabla["region"] = tabla["region"].map(REGIONES_ES)
        st.dataframe(tabla.drop(columns="iso3").round(2).rename(columns={
            "pais": "País", "region": "Región", "z_medio_M1": "z medio", "residuo_medio_M1": "Años sobre lo esperado",
            "esperanza_vida": "Esp. vida", "pib_per_capita_ppp": "PIB pc (US$)", "gasto_salud_per_capita_ppp": "Gasto salud pc (US$)"}),
            hide_index=True, width="stretch")
        por_que(
            f"Criterio: residuo medio **≥ +1σ** y positivo en **≥ 70 % de los años** ({RECENT_WINDOW[0]}–{RECENT_WINDOW[1]}). "
            "Así filtramos el ruido y exigimos que el país supere lo esperado **de forma persistente**, no un año suelto. "
            "Un país es *robusto* si además cumple con el modelo M3 y al excluir un país a la vez (leave-one-country-out)."
        )
        figura("04_sobre_desempeno_dispersion.png", "Países con sobre-desempeño resaltados sobre la curva ingreso–esperanza de vida")
        st.warning("Son economías pequeñas: sus estimaciones son más ruidosas. Los datos **no identifican causas**.")

    with t4:
        sigma = csv(TABLAS, "sigma_convergencia.csv")
        st.plotly_chart(px.line(sigma, x="anio", y="desv_est",
                                labels={"anio": "Año", "desv_est": "Desviación estándar entre países (años)"}),
                        width="stretch")
        r = resumen()
        st.markdown(
            f"La dispersión bajó de **{r['sigma_1990']:.1f} años (1990)** a **{r['sigma_2023']:.1f} (2023)**; "
            f"la brecha entre la región más alta y la más baja, de {r['brecha_regional_1990']:.1f} a {r['brecha_regional_2023']:.1f} años."
        )
        por_que(
            "**σ-convergencia** mide si la dispersión baja; **β-convergencia** si los que partían más abajo crecen más rápido "
            f"(β = {r['beta_1990_2023']['beta']:.4f}, p < 0.001). Usamos ambas porque responden preguntas distintas."
        )
        figura("05_series_regionales.png", "Esperanza de vida por región (medias simples, sin ponderar por población)")


# ---------------------------------------------------------------- 5. Conclusiones
def pagina_conclusiones() -> None:
    st.title("Conclusiones")
    hip = csv(RESULTADOS, "hipotesis.csv")
    st.dataframe(hip.rename(columns={"hipotesis": "ID", "enunciado": "Hipótesis", "veredicto": "Veredicto", "evidencia": "Evidencia"}),
                 hide_index=True, width="stretch")
    st.markdown(
        "1. El **ingreso** es el predictor más fuerte, con rendimientos decrecientes.\n"
        "2. **Gasto en salud y educación** se asocian con más esperanza de vida, pero su aporte independiente es modesto.\n"
        "3. **8 países** logran de forma robusta más salud de la que predice su ingreso.\n"
        "4. La salud global **converge**, aunque África Subsahariana sigue rezagada."
    )
    st.success(
        "**Recomendación:** los tomadores de decisión no deberían enfocarse solo en el crecimiento del PIB. "
        "Proponemos estudiar las políticas de **atención primaria** de países como **Cabo Verde, Jordania o Albania**, "
        "que alcanzan alta esperanza de vida con recursos moderados, incorporando datos de cobertura de salud y vacunación (OMS-GHO)."
    )
    st.subheader("Limitaciones")
    st.markdown(
        "- **Observacional:** asociaciones, no causalidad.\n"
        "- **Cobertura desigual** del gasto en salud por región; no se imputaron faltantes.\n"
        "- **Colinealidad** PIB–gasto (VIF ≈ 8–9).\n"
        "- PIB en dólares constantes y gasto en corrientes: no se combinaron en razones.\n"
        "- Esperanza de vida **modelada** (UN WPP) en varios países; la escolaridad no mide calidad.\n"
        "- Medias regionales **sin ponderar** por población.\n"
        "- El umbral de sobre-desempeño (+1σ, 70 %) es una **convención** del equipo."
    )


if __name__ == "__main__":  # `streamlit run` ejecuta el script como __main__; las pruebas lo importan
    st.navigation([
        st.Page(pagina_problema, title="1 · Problema y pregunta", icon="❓", url_path="problema", default=True),
        st.Page(pagina_datos, title="2 · Los datos", icon="🗂️", url_path="datos"),
        st.Page(pagina_preparacion, title="3 · Preparación", icon="🧹", url_path="preparacion"),
        st.Page(pagina_analisis, title="4 · Análisis y hallazgos", icon="📈", url_path="analisis"),
        st.Page(pagina_conclusiones, title="5 · Conclusiones", icon="✅", url_path="conclusiones"),    ]).run()
    st.sidebar.caption(FUENTE)

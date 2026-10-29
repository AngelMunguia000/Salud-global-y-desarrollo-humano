"""Fase 3 · Análisis exploratorio: explorador, ingreso, correlaciones y convergencia (P1 y P3)."""
import plotly.express as px
import streamlit as st

from common.style import COLORES, REGIONES_ES
from components import encabezado, figura, por_que
from services.pipeline import TABLAS, csv, panel, resumen

COLORES_ES = {REGIONES_ES[k]: v for k, v in COLORES.items()}


def render() -> None:
    encabezado("Fase 3 · Análisis exploratorio", "Análisis y hallazgos",
               "Distribuciones, relaciones y tendencias antes de modelar.")
    t1, t2, t3, t4 = st.tabs(["Explorador", "P1 · Ingreso", "Correlaciones", "P3 · Convergencia"])

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
        r2 = csv(TABLAS, "r2_lineal_vs_log_por_anio.csv")
        fig = px.line(r2, x="anio", y=["r2_lineal", "r2_log"], markers=True,
                      labels={"anio": "Año", "value": "R²", "variable": "Escala del PIB"})
        fig.for_each_trace(lambda t: t.update(name={"r2_lineal": "Niveles", "r2_log": "Logaritmo"}[t.name]))
        st.plotly_chart(fig, width="stretch")
        r = resumen()
        por_que(
            f"Comparamos año por año para no depender de un solo corte: el logaritmo explica más varianza "
            f"en **{r['r2_log_mayor_en_anios']} de {r['anios_evaluados']} años**. La relación se **aplana**: "
            "un año más de vida cuesta mucho más ingreso en países ricos."
        )

    with t3:
        spearman = csv(TABLAS, "correlacion_spearman.csv", index_col=0)
        st.plotly_chart(px.imshow(spearman.round(2), text_auto=True, color_continuous_scale="RdBu",
                                  zmin=-1, zmax=1, aspect="auto"), width="stretch")
        por_que(
            "Usamos **Spearman** además de Pearson porque mide relaciones monótonas sin suponer linealidad "
            "y es menos sensible a valores extremos. La alta correlación PIB–gasto anticipa la colinealidad de los modelos."
        )

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

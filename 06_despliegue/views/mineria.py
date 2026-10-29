"""Fase 1 · Minería: fuentes, por qué se eligieron y cobertura."""
import plotly.express as px
import streamlit as st

from common.panel import WINDOW
from common.style import REGIONES_ES
from components import encabezado, por_que
from services.pipeline import TABLAS, csv


def render() -> None:
    encabezado("Fase 1 · Minería de datos", "Los datos",
               "Localizar, evaluar y obtener fuentes comparables entre países.")
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

"""Inicio: problema, pregunta central y respuesta corta."""
import streamlit as st

from common.panel import WINDOW
from services.pipeline import resumen


def render() -> None:
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
    st.subheader("Respuesta corta")
    st.markdown(
        "- Duplicar el PIB per cápita se asocia con **+4.2 años** de esperanza de vida, con rendimientos decrecientes.\n"
        "- Gasto en salud y escolaridad aportan, pero de forma **frágil**.\n"
        f"- **{r['robustos']} países** viven más de lo que predice su ingreso.\n"
        f"- Las brechas se cierran: la dispersión bajó de {r['sigma_1990']:.1f} a {r['sigma_2023']:.1f} años (1990–2023)."
    )
    st.markdown(
        "**Recorrido por fases:** Minería → Ingeniería → Análisis → Ciencia de datos → MLOps (menú de la izquierda)."
    )
    st.warning("Todos los resultados son **asociaciones**, no efectos causales: es un diseño observacional.")

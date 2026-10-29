"""Punto de entrada de la aplicación Streamlit: una vista por fase del proyecto.

Estructura: ``views/`` (una página por fase), ``components.py`` (piezas visuales) y
``services/pipeline.py`` (carga de resultados). Ejecutar desde la raíz:
    streamlit run 06_despliegue/app.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # raíz del repo, para importar common/

from views import analisis, ciencia, home, ingenieria, mineria, mlops  # noqa: E402

st.set_page_config(page_title="Salud global y desarrollo humano", page_icon="🌍", layout="wide")

st.navigation([
    st.Page(home.render, title="Inicio", icon="🏠", url_path="home", default=True),
    st.Page(mineria.render, title="1 · Minería", icon="⛏️", url_path="mineria"),
    st.Page(ingenieria.render, title="2 · Ingeniería", icon="🛠️", url_path="ingenieria"),
    st.Page(analisis.render, title="3 · Análisis", icon="📈", url_path="analisis"),
    st.Page(ciencia.render, title="4 · Ciencia de datos", icon="🧪", url_path="ciencia"),
    st.Page(mlops.render, title="5 · MLOps", icon="⚙️", url_path="mlops"),
]).run()
st.sidebar.caption("Fuente: Banco Mundial (WDI), OMS (GHED), PNUD vía Our World in Data. Elaboración propia.")

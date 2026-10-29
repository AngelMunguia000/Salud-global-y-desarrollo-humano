"""Componentes visuales reutilizables por todas las vistas."""
from __future__ import annotations

import streamlit as st

from services.pipeline import FIGURAS


def encabezado(fase: str, titulo: str, descripcion: str) -> None:
    st.caption(fase.upper())
    st.title(titulo)
    st.markdown(descripcion)


def por_que(texto: str) -> None:
    """Caja de justificación: la rúbrica pide explicar el porqué de cada dato y método."""
    st.info(f"**¿Por qué?** {texto}", icon="💡")


def figura(nombre: str, pie: str) -> None:
    st.image(str(FIGURAS / nombre), caption=pie, width="stretch")

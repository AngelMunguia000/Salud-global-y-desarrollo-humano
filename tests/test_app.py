"""Prueba de humo de la app de Streamlit: cada página se ejecuta sin excepciones."""
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP_DIR = Path(__file__).resolve().parents[1] / "06_despliegue"
PAGINAS = ["problema", "datos", "preparacion", "analisis", "conclusiones"]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_sin_errores(pagina):
    # AppTest.switch_page solo admite páginas en archivos; aquí se llama la función de cada página.
    codigo = f"import sys; sys.path.insert(0, r'{APP_DIR}'); import app; app.pagina_{pagina}()"
    app = AppTest.from_string(codigo, default_timeout=60).run()
    assert not app.exception, app.exception

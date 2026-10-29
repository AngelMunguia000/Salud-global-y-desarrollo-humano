"""Prueba de humo de la app de Streamlit: cada vista se ejecuta sin excepciones."""
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP_DIR = Path(__file__).resolve().parents[1] / "06_despliegue"
VISTAS = ["home", "mineria", "ingenieria", "analisis", "ciencia", "mlops"]


@pytest.mark.parametrize("vista", VISTAS)
def test_vista_sin_errores(vista):
    # AppTest.switch_page solo admite páginas en archivos; aquí se llama el render() de cada vista.
    codigo = f"import sys; sys.path.insert(0, r'{APP_DIR}'); from views import {vista}; {vista}.render()"
    app = AppTest.from_string(codigo, default_timeout=60).run()
    assert not app.exception, app.exception


def test_app_principal_sin_errores():
    app = AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=60).run()
    assert not app.exception, app.exception
    assert app.title[0].value == "Salud global y desarrollo humano"  # la página de inicio se dibujó

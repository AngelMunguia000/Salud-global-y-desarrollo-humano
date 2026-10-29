"""Acceso a los resultados del pipeline (ETL → EDA → modelos). La app solo lee; no recalcula nada."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))  # para importar common/ desde la raíz del repositorio

from common.panel import add_derived, load_panel  # noqa: E402
from common.style import REGIONES_ES  # noqa: E402

TABLAS = ROOT / "04_analisis" / "tablas"
RESULTADOS = ROOT / "05_ciencia" / "resultados"
FIGURAS = ROOT / "reports" / "figuras"
PROCESADOS = ROOT / "03_data" / "processed"
TESTS = ROOT / "tests"


@st.cache_data
def panel() -> pd.DataFrame:
    """Panel país-año con logaritmos y nombre de región en español."""
    data = add_derived(load_panel())
    data["region_es"] = data["region"].map(REGIONES_ES)
    return data


@st.cache_data
def csv(carpeta: Path, nombre: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(carpeta / nombre, **kwargs)


@st.cache_data
def resumen() -> dict:
    """Cifras clave del EDA y de los modelos en un solo diccionario."""
    eda = json.loads((TABLAS / "resultados_eda.json").read_text(encoding="utf-8"))
    modelos = json.loads((RESULTADOS / "resumen_modelos.json").read_text(encoding="utf-8"))
    return {**eda, **modelos}


@st.cache_data
def hashes() -> pd.DataFrame:
    """Manifiesto SHA-256 de los archivos originales."""
    datos = json.loads((PROCESADOS / "source_hashes.json").read_text(encoding="utf-8"))
    return pd.DataFrame(
        [{"archivo": Path(k.replace("\\", "/")).name, "bytes": v["bytes"], "sha256": v["sha256"]}
         for k, v in datos.items()]
    )


@st.cache_data
def conteo_pruebas() -> pd.DataFrame:
    """Número de funciones de prueba por archivo de tests/."""
    filas = [{"archivo": f"tests/{p.name}", "pruebas": p.read_text(encoding="utf-8").count("\ndef test_")}
             for p in sorted(TESTS.glob("test_*.py"))]
    return pd.DataFrame(filas)

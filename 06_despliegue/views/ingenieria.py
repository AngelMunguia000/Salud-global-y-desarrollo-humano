"""Fase 2 · Ingeniería: pipeline ETL, decisiones de limpieza y almacén."""
import pandas as pd
import streamlit as st

from components import encabezado, por_que
from services.pipeline import panel


def render() -> None:
    encabezado("Fase 2 · Ingeniería de datos", "Preparación de los datos",
               "Pipeline ETL reproducible en `02_ingenieria/etl/`.")
    st.code(
        "03_data/ (CSV originales, verificados con SHA-256)\n"
        "   │  extract.py    lee las fuentes y calcula hashes\n"
        "   │  transform.py  formato largo, ISO3, excluye agregados\n"
        "   │  merge.py      une por (iso3, anio), regla 20–95 años\n"
        "   ▼  load.py       Parquet + CSV + almacén DuckDB\n"
        "03_data/processed/panel_salud_global.parquet  ·  warehouse/salud.db",
        language=None,
    )
    decisiones = [
        ("Unir solo por `(iso3, año)`", "Los nombres de país difieren entre Banco Mundial y OWID; el código ISO3 es único.", "Unir por nombre"),
        ("Excluir agregados (Mundo, regiones, grupos de ingreso)", "No son países: duplicarían observaciones y sesgarían los modelos.", "Lista manual de códigos"),
        ("Esperanza de vida como tabla base (left join)", "Es la variable objetivo; evita multiplicar filas.", "Outer join"),
        ("**No imputar** faltantes", "Ausencia ≠ cero. Imputar gasto en salud de 200+ países crearía datos sintéticos; preferimos 4,339 observaciones reales.", "Mediana o MICE"),
        ("Logaritmo del PIB y del gasto per cápita", "Rendimientos decrecientes: un dólar extra vale más en un país pobre que en uno rico.", "Niveles"),
        ("Regla de calidad 20–95 años", "Excluye 9 país-año extremos (p. ej. Camboya 1975–78, Ruanda 1994); los originales no se tocan.", "Conservarlos sin marcar"),
    ]
    st.table(pd.DataFrame(decisiones, columns=["Decisión", "Razón", "Alternativa descartada"]))
    por_que(
        "Cada decisión tiene una alternativa descartada: así podemos defender que **no fue arbitraria**. "
        "El registro completo está en `docs/decisiones.md`."
    )
    st.subheader("Resultado: el panel")
    data = panel()
    c = st.columns(3)
    c[0].metric("Filas país-año", f"{len(data):,}")
    c[1].metric("Países", data["iso3"].nunique())
    c[2].metric("Años", f"{data['anio'].min()}–{data['anio'].max()}")
    st.dataframe(data.drop(columns=["ln_pib", "ln_gasto_pc", "region_es"]).head(20), hide_index=True, width="stretch")
    st.subheader("Almacén DuckDB (`warehouse/salud.db`)")
    st.table(pd.DataFrame([
        ("dim_pais", "iso3, pais, region"),
        ("dim_indicador", "codigo_indicador, nombre, unidad"),
        ("hechos_indicador", "iso3, anio, codigo_indicador, valor"),
    ], columns=["Tabla", "Columnas"]))
    por_que("Un esquema dimensional (hechos + dimensiones) permite consultar cualquier indicador por país y año con SQL.")

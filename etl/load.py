"""Exportación del panel y carga del almacén analítico local."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd

INDICATOR_METADATA = {
    "esperanza_vida": ("SP.DYN.LE00.IN", "Esperanza de vida al nacer", "años"),
    "mortalidad_infantil": (
        "SP.DYN.IMRT.IN",
        "Mortalidad infantil",
        "por 1.000 nacidos vivos",
    ),
    "pib_per_capita_ppp": (
        "NY.GDP.PCAP.PP.KD",
        "PIB per cápita PPA",
        "USD internacionales constantes",
    ),
    "gasto_salud_pct_pib": ("SH.XPD.CHEX.GD.ZS", "Gasto corriente en salud", "% del PIB"),
    "gasto_salud_per_capita_ppp": (
        "SH.XPD.CHEX.PP.CD",
        "Gasto en salud per cápita PPA",
        "USD internacionales corrientes",
    ),
    "escolaridad_promedio": ("OWID:schooling", "Años promedio de escolaridad", "años"),
}


def write_hash_manifest(hashes: dict[str, dict[str, object]], output: Path) -> None:
    """Escribe un manifiesto legible con tamaño y SHA-256 de cada archivo crudo."""
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Manifiesto SHA-256 de fuentes",
        "",
        "Hashes calculados durante la extracción; los archivos de origen no se modifican.",
        "",
        "| Archivo | Bytes | SHA-256 |",
        "|---|---:|---|",
    ]
    for filename, details in sorted(hashes.items()):
        lines.append(
            f"| `{filename}` | {details['bytes']} | `{details['sha256']}` |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_panel(panel: pd.DataFrame, output_dir: Path) -> None:
    """Exporta el panel maestro en Parquet y CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_dir / "panel_salud_global.parquet", index=False)
    panel.to_csv(output_dir / "panel_salud_global.csv", index=False)


def _warehouse_tables(
    panel: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    countries = panel[["iso3", "pais", "region"]].drop_duplicates().sort_values("iso3")
    indicator_rows = [
        {
            "codigo_indicador": code,
            "nombre": name,
            "unidad": unit,
        }
        for code, name, unit in INDICATOR_METADATA.values()
    ]
    dimensions = pd.DataFrame(indicator_rows)

    value_columns = [
        column for column in INDICATOR_METADATA if column in panel.columns
    ]
    facts = panel.melt(
        id_vars=["iso3", "anio"],
        value_vars=value_columns,
        var_name="variable",
        value_name="valor",
    ).dropna(subset=["valor"])
    variable_to_code = {
        variable: metadata[0] for variable, metadata in INDICATOR_METADATA.items()
    }
    facts["codigo_indicador"] = facts["variable"].map(variable_to_code)
    facts = facts[["iso3", "anio", "codigo_indicador", "valor"]]
    return countries, dimensions.merge(
        facts[["codigo_indicador"]].drop_duplicates(),
        on="codigo_indicador",
        how="inner",
    ).drop_duplicates(), facts


def load_warehouse(panel: pd.DataFrame, database_path: Path) -> None:
    """Crea/reemplaza las dimensiones y la tabla de hechos en DuckDB."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    countries, indicators, facts = _warehouse_tables(panel)
    connection = duckdb.connect(str(database_path))
    try:
        connection.register("countries_frame", countries)
        connection.register("indicators_frame", indicators)
        connection.register("facts_frame", facts)
        connection.execute(
            "CREATE OR REPLACE TABLE dim_pais AS SELECT * FROM countries_frame"
        )
        connection.execute(
            "CREATE OR REPLACE TABLE dim_indicador AS SELECT * FROM indicators_frame"
        )
        connection.execute(
            """
            CREATE OR REPLACE TABLE hechos_indicador AS
            SELECT iso3, anio, codigo_indicador, valor
            FROM facts_frame
            """
        )
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_hechos_indicador
            ON hechos_indicador (iso3, anio, codigo_indicador)
            """
        )
    finally:
        connection.close()


def save_hashes_json(hashes: dict[str, dict[str, object]], output: Path) -> None:
    """Guarda hashes en formato estructurado para automatizaciones posteriores."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(hashes, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

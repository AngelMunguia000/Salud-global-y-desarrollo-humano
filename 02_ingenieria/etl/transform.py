"""Normalización de indicadores a nivel país-año."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from .extract import WORLD_BANK_INDICATORS

ISO3_PATTERN = re.compile(r"^[A-Z]{3}$")
YEAR_PATTERN = re.compile(r"^\d{4}$")


def transform_countries(metadata: pd.DataFrame) -> pd.DataFrame:
    """Devuelve países con código ISO-3 y región asignada."""
    required = {"Country Code", "Region", "TableName"}
    missing = required.difference(metadata.columns)
    if missing:
        raise ValueError(f"Faltan columnas en Metadata_Country: {sorted(missing)}")

    countries = metadata.loc[
        metadata["Region"].notna()
        & metadata["Region"].astype(str).str.strip().ne("")
        & metadata["Country Code"].astype(str).str.fullmatch(ISO3_PATTERN),
        ["Country Code", "Region", "TableName"],
    ].copy()
    countries = countries.rename(
        columns={
            "Country Code": "iso3",
            "Region": "region",
            "TableName": "pais",
        }
    )
    countries["iso3"] = countries["iso3"].str.upper()
    if countries["iso3"].duplicated().any():
        raise ValueError("Metadata_Country contiene códigos de país duplicados.")
    return countries.reset_index(drop=True)


def transform_world_bank(
    wide_data: pd.DataFrame,
    countries: pd.DataFrame,
    indicator_code: str,
) -> pd.DataFrame:
    """Convierte una tabla WDI ancha a registros ISO-3/año/indicador."""
    if indicator_code not in WORLD_BANK_INDICATORS:
        raise ValueError(f"Indicador WDI no soportado: {indicator_code}")
    required = {"Country Code", "Country Name"}
    missing = required.difference(wide_data.columns)
    if missing:
        raise ValueError(f"Faltan columnas WDI: {sorted(missing)}")

    year_columns = [
        column
        for column in wide_data.columns
        if YEAR_PATTERN.fullmatch(str(column))
    ]
    if not year_columns:
        raise ValueError(f"No se encontraron columnas de año para {indicator_code}.")

    country_codes = set(countries["iso3"])
    selected = wide_data.loc[
        wide_data["Country Code"].astype(str).str.upper().isin(country_codes)
    ]
    long_data = selected.melt(
        id_vars=["Country Code"],
        value_vars=year_columns,
        var_name="anio",
        value_name=WORLD_BANK_INDICATORS[indicator_code],
    )
    long_data = long_data.rename(columns={"Country Code": "iso3"})
    long_data["iso3"] = long_data["iso3"].str.upper()
    long_data["anio"] = pd.to_numeric(long_data["anio"], errors="raise").astype("int64")
    value_column = WORLD_BANK_INDICATORS[indicator_code]
    long_data[value_column] = pd.to_numeric(long_data[value_column], errors="coerce")
    return long_data.dropna(subset=[value_column]).reset_index(drop=True)


def transform_education(
    education: pd.DataFrame,
    countries: pd.DataFrame,
) -> pd.DataFrame:
    """Estandariza OWID a iso3/año y excluye entidades no-país."""
    required = {"Code", "Year"}
    missing = required.difference(education.columns)
    if missing:
        raise ValueError(f"Faltan columnas OWID: {sorted(missing)}")
    value_columns = [
        column
        for column in education.columns
        if column not in {"Entity", "Code", "Year"}
    ]
    if len(value_columns) != 1:
        raise ValueError(
            "Se esperaba una única columna de valores en el archivo OWID de escolaridad."
        )

    source_value = value_columns[0]
    country_codes = set(countries["iso3"])
    result = education.loc[
        education["Code"].astype(str).str.upper().isin(country_codes),
        ["Code", "Year", source_value],
    ].copy()
    result = result.rename(
        columns={
            "Code": "iso3",
            "Year": "anio",
            source_value: "escolaridad_promedio",
        }
    )
    result["iso3"] = result["iso3"].str.upper()
    result["anio"] = pd.to_numeric(result["anio"], errors="raise").astype("int64")
    result["escolaridad_promedio"] = pd.to_numeric(
        result["escolaridad_promedio"], errors="coerce"
    )
    return result.dropna(subset=["escolaridad_promedio"]).reset_index(drop=True)


def transform_sources(extracted: dict[str, Any]) -> dict[str, Any]:
    """Transforma todas las fuentes y conserva la dimensión de países."""
    countries = transform_countries(extracted["countries"])
    indicators = {
        WORLD_BANK_INDICATORS[indicator_code]: transform_world_bank(
            data, countries, indicator_code
        )
        for indicator_code, data in extracted["world_bank"].items()
    }
    indicators["escolaridad_promedio"] = transform_education(
        extracted["education"], countries
    )
    return {
        "countries": countries,
        "indicators": indicators,
        "hashes": extracted["hashes"],
    }

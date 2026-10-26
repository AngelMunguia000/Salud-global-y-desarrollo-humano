"""Pruebas unitarias de las reglas de calidad del ETL."""

from pathlib import Path

import pandas as pd
import pytest

from ingenieria.etl.merge import merge_indicators
from ingenieria.etl.transform import (
    transform_countries,
    transform_education,
    transform_world_bank,
)


@pytest.fixture
def source_data():
    """Fuentes pequeñas con países, agregado y valores dentro/fuera de rango."""
    country_metadata = pd.DataFrame(
        {
            "Country Code": ["AFG", "USA", "WLD"],
            "Region": ["South Asia", "North America", ""],
            "TableName": ["Afghanistan", "United States", "World"],
        }
    )
    world_bank_wide = pd.DataFrame(
        {
            "Country Name": ["Afghanistan", "United States", "World"],
            "Country Code": ["AFG", "USA", "WLD"],
            "Indicator Name": [
                "Life expectancy",
                "Life expectancy",
                "Life expectancy",
            ],
            "Indicator Code": ["SP.DYN.LE00.IN"] * 3,
            "2020": [64.0, 77.0, 73.0],
            "2021": [65.0, 78.0, 74.0],
        }
    )
    education = pd.DataFrame(
        {
            "Entity": ["Afghanistan", "United States", "World"],
            "Code": ["AFG", "USA", "OWID_WRL"],
            "Year": [2020, 2020, 2020],
            "Average years of schooling": [2.5, 13.7, 8.0],
        }
    )
    countries = transform_countries(country_metadata)
    return countries, world_bank_wide, education


@pytest.fixture
def sample_panel(source_data):
    """Panel integrado mínimo para las pruebas de calidad."""
    countries, wide_data, education = source_data
    life_expectancy = transform_world_bank(
        wide_data, countries, "SP.DYN.LE00.IN"
    )
    schooling = transform_education(education, countries)
    return merge_indicators(
        {
            "esperanza_vida": life_expectancy,
            "escolaridad_promedio": schooling,
        },
        countries,
    )


def test_panel_key_is_unique(sample_panel):
    """El panel integrado mantiene una fila por país y año."""
    assert not sample_panel.duplicated(["iso3", "anio"]).any()


def test_panel_excludes_regional_and_world_aggregates(sample_panel):
    """Metadata regional y códigos OWID ajenos al conjunto de países se excluyen."""
    assert set(sample_panel["iso3"]) == {"AFG", "USA"}
    assert sample_panel["region"].notna().all()


def test_life_expectancy_is_within_logical_range(sample_panel):
    """La esperanza de vida del panel debe estar entre 20 y 95 años."""
    assert sample_panel["esperanza_vida"].between(
        20, 95, inclusive="both"
    ).all()


def test_duplicate_indicator_keys_are_rejected(source_data):
    """La integración falla explícitamente si una fuente duplica país-año."""
    countries, wide_data, _ = source_data
    life_expectancy = transform_world_bank(
        wide_data, countries, "SP.DYN.LE00.IN"
    )
    duplicate = pd.concat([life_expectancy, life_expectancy.iloc[[0]]])

    with pytest.raises(ValueError, match="duplicadas"):
        merge_indicators(
            {"esperanza_vida": life_expectancy, "duplicate": duplicate},
            countries,
        )


@pytest.fixture
def processed_panel():
    """Carga el panel que genera ``make test`` antes de ejecutar pytest."""
    panel_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "processed"
        / "panel_salud_global.parquet"
    )
    if not panel_path.is_file():
        pytest.fail("Ejecuta primero `make etl` para generar el panel procesado.")
    return pd.read_parquet(panel_path)


def test_processed_panel_key_is_unique(processed_panel):
    """El panel producido no repite la llave compuesta."""
    assert not processed_panel.duplicated(["iso3", "anio"]).any()


def test_processed_panel_has_no_aggregates(processed_panel):
    """Cada registro del panel corresponde a un país con región asignada."""
    assert processed_panel["iso3"].str.fullmatch(r"[A-Z]{3}").all()
    assert processed_panel["region"].notna().all()
    assert processed_panel["region"].str.strip().ne("").all()


def test_processed_panel_life_expectancy_range(processed_panel):
    """La esperanza de vida procesada se encuentra entre 20 y 95 años."""
    assert processed_panel["esperanza_vida"].between(
        20, 95, inclusive="both"
    ).all()

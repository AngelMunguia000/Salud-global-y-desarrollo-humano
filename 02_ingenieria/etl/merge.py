"""Integración de indicadores usando exclusivamente iso3 y año."""

from __future__ import annotations

import logging

import pandas as pd

from .extract import WORLD_BANK_INDICATORS

KEY_COLUMNS = ["iso3", "anio"]
LOGGER = logging.getLogger(__name__)


def merge_indicators(
    indicators: dict[str, pd.DataFrame],
    countries: pd.DataFrame,
) -> pd.DataFrame:
    """Une indicadores usando esperanza de vida como tabla base."""
    base_name = WORLD_BANK_INDICATORS["SP.DYN.LE00.IN"]
    if base_name not in indicators:
        raise ValueError("La esperanza de vida es requerida como tabla base.")

    panel = indicators[base_name].copy()
    for name, data in indicators.items():
        if name == base_name:
            continue
        if data.duplicated(KEY_COLUMNS).any():
            raise ValueError(f"El indicador {name} tiene claves iso3/año duplicadas.")
        panel = panel.merge(
            data[KEY_COLUMNS + [name]],
            on=KEY_COLUMNS,
            how="left",
            validate="one_to_one",
        )

    if panel.duplicated(KEY_COLUMNS).any():
        raise ValueError("La unión produjo claves iso3/año duplicadas.")

    panel = panel.merge(
        countries,
        on="iso3",
        how="left",
        validate="many_to_one",
    )
    if panel[["pais", "region"]].isna().any().any():
        raise ValueError("Hay países del panel sin nombre o región en la dimensión.")
    out_of_range = ~panel["esperanza_vida"].between(20, 95, inclusive="both")
    if out_of_range.any():
        LOGGER.warning(
            "Se excluyeron %s observaciones con esperanza de vida fuera del rango "
            "lógico de 20–95 años.",
            int(out_of_range.sum()),
        )
        panel = panel.loc[~out_of_range].copy()
    return panel.sort_values(KEY_COLUMNS).reset_index(drop=True)

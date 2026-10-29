"""Carga del panel consolidado y variables derivadas compartidas por las fases."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PANEL_PARQUET = ROOT / "03_data" / "processed" / "panel_salud_global.parquet"
PANEL_CSV = ROOT / "03_data" / "processed" / "panel_salud_global.csv"

REQUIRED_COLUMNS = {
    "iso3", "anio", "pais", "region", "esperanza_vida", "mortalidad_infantil",
    "pib_per_capita_ppp", "gasto_salud_pct_pib", "gasto_salud_per_capita_ppp",
    "escolaridad_promedio",
}
WINDOW = (2000, 2023)          # periodo común con las seis variables
RECENT_WINDOW = (2015, 2023)   # ventana para el análisis de residuos


def load_panel(path: Path | None = None) -> pd.DataFrame:
    """Carga el panel (Parquet si es posible; CSV como respaldo) y lo valida.

    Raises:
        FileNotFoundError: si no existe ninguna versión del panel.
        ValueError: si faltan columnas requeridas.
    """
    candidates = [path] if path else [PANEL_PARQUET, PANEL_CSV]
    last_error: Exception | None = None
    for candidate in candidates:
        if candidate is None or not Path(candidate).is_file():
            continue
        try:
            panel = (pd.read_parquet(candidate) if str(candidate).endswith(".parquet")
                     else pd.read_csv(candidate))
        except ImportError as exc:  # pyarrow ausente: usa el CSV
            last_error = exc
            continue
        missing = REQUIRED_COLUMNS - set(panel.columns)
        if missing:
            raise ValueError(f"Faltan columnas en el panel: {sorted(missing)}")
        return panel
    raise FileNotFoundError(
        f"No se pudo cargar el panel ({last_error}). Ejecuta `make etl` primero."
    )


def add_derived(panel: pd.DataFrame) -> pd.DataFrame:
    """Agrega logaritmos de PIB y gasto per cápita (solo valores > 0)."""
    out = panel.copy()
    out["ln_pib"] = np.log(out["pib_per_capita_ppp"].where(out["pib_per_capita_ppp"] > 0))
    out["ln_gasto_pc"] = np.log(
        out["gasto_salud_per_capita_ppp"].where(out["gasto_salud_per_capita_ppp"] > 0)
    )
    return out


def complete_cases(panel: pd.DataFrame, columns: list[str],
                   years: tuple[int, int] | None = WINDOW) -> pd.DataFrame:
    """Filtra el periodo y conserva solo filas completas en ``columns``."""
    data = panel
    if years:
        data = data[data["anio"].between(*years)]
    return data.dropna(subset=columns).copy()

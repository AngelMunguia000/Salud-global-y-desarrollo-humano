"""Resumen y visualizaciones del panel consolidado."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PANEL_PATH = ROOT / "03_data" / "processed" / "panel_salud_global.parquet"
OUTPUT_DIR = ROOT / "04_analisis" / "visualizaciones"


def load_panel(path: Path = PANEL_PATH) -> pd.DataFrame:
    """Carga el panel final y valida sus columnas mínimas."""
    if not path.is_file():
        raise FileNotFoundError(
            f"No existe el panel consolidado: {path}. Ejecuta primero el ETL."
        )
    panel = pd.read_parquet(path)
    required = {"iso3", "anio", "esperanza_vida", "region", "pais"}
    missing = required.difference(panel.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el panel: {sorted(missing)}")
    return panel


def descriptive_summary(panel: pd.DataFrame) -> pd.DataFrame:
    """Calcula estadísticas descriptivas de los indicadores numéricos."""
    numeric = panel.select_dtypes(include="number")
    return numeric.describe().T


def missingness_summary(panel: pd.DataFrame) -> pd.DataFrame:
    """Resume cantidad y proporción de valores ausentes por variable."""
    return pd.DataFrame(
        {
            "faltantes": panel.isna().sum(),
            "proporcion_faltante": panel.isna().mean(),
        }
    ).sort_values("proporcion_faltante", ascending=False)


def save_life_income_plot(panel: pd.DataFrame, output_dir: Path = OUTPUT_DIR) -> Path:
    """Guarda la relación entre PIB per cápita y esperanza de vida."""
    columns = ["pib_per_capita_ppp", "esperanza_vida"]
    data = panel[columns].dropna()
    if data.empty:
        raise ValueError("No hay observaciones completas para el gráfico de ingreso.")
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "pib_vs_esperanza_vida.png"
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.scatter(data["pib_per_capita_ppp"], data["esperanza_vida"], alpha=0.35)
    axis.set_xscale("log")
    axis.set_xlabel("PIB per cápita PPA (escala logarítmica)")
    axis.set_ylabel("Esperanza de vida (años)")
    axis.set_title("PIB per cápita y esperanza de vida")
    figure.tight_layout()
    figure.savefig(output, dpi=150)
    plt.close(figure)
    return output


def main() -> None:
    """Genera resúmenes exploratorios y una visualización base."""
    panel = load_panel()
    print(descriptive_summary(panel).to_string())
    print("\nValores faltantes:\n", missingness_summary(panel).to_string())
    print(f"\nGráfico: {save_life_income_plot(panel)}")


if __name__ == "__main__":
    main()

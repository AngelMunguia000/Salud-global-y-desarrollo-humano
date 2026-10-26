"""Punto de entrada reproducible del pipeline de datos local."""

from __future__ import annotations

import argparse
from pathlib import Path

from etl.extract import extract_sources
from etl.load import (
    load_warehouse,
    save_hashes_json,
    save_panel,
    write_hash_manifest,
)
from etl.merge import merge_indicators
from etl.transform import transform_sources


def resolve_raw_dir(project_root: Path, requested: Path | None) -> Path:
    """Selecciona data/raw cuando existe; admite el layout actual bajo data/."""
    if requested is not None:
        return requested if requested.is_absolute() else project_root / requested
    raw_dir = project_root / "data" / "raw"
    if raw_dir.is_dir():
        return raw_dir
    return project_root / "data"


def run_pipeline(raw_dir: Path, output_dir: Path, warehouse_path: Path) -> None:
    """Ejecuta extracción, transformación, integración y carga."""
    extracted = extract_sources(raw_dir)
    transformed = transform_sources(extracted)
    panel = merge_indicators(
        transformed["indicators"],
        transformed["countries"],
    )
    save_panel(panel, output_dir)
    load_warehouse(panel, warehouse_path)
    write_hash_manifest(
        transformed["hashes"],
        output_dir / "MANIFEST.md",
    )
    save_hashes_json(
        transformed["hashes"],
        output_dir / "source_hashes.json",
    )
    print(f"Panel generado: {len(panel):,} filas, {panel['iso3'].nunique()} países.")
    print(f"Archivos procesados: {output_dir}")
    print(f"Almacén DuckDB: {warehouse_path}")


def main() -> None:
    """Interfaz de línea de comandos del pipeline."""
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=None,
        help="Directorio de fuentes crudas.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project_root / "data" / "processed",
        help="Directorio de exportación.",
    )
    parser.add_argument(
        "--warehouse",
        type=Path,
        default=project_root / "warehouse" / "salud.db",
        help="Ruta del almacén DuckDB.",
    )
    args = parser.parse_args()
    raw_dir = resolve_raw_dir(project_root, args.raw_dir)
    run_pipeline(raw_dir, args.output_dir, args.warehouse)


if __name__ == "__main__":
    main()

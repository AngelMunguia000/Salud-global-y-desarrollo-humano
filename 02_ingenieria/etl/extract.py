"""Extracción y verificación de fuentes WDI y OWID."""

from __future__ import annotations

import hashlib
import io
import re
import zipfile
from pathlib import Path
from typing import Callable

import pandas as pd

WORLD_BANK_INDICATORS = {
    "SP.DYN.LE00.IN": "esperanza_vida",
    "SP.DYN.IMRT.IN": "mortalidad_infantil",
    "NY.GDP.PCAP.PP.KD": "pib_per_capita_ppp",
    "SH.XPD.CHEX.GD.ZS": "gasto_salud_pct_pib",
    "SH.XPD.CHEX.PP.CD": "gasto_salud_per_capita_ppp",
}
EDUCATION_FILE = "average-years-of-schooling-among-adults.csv"
WDI_SKIPROWS = 4


def sha256_file(path: Path) -> str:
    """Calcula el hash SHA-256 de un archivo en bloques."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _all_raw_files(raw_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in raw_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".csv", ".zip"}
    )


def _read_csv_bytes(content: bytes, skiprows: int = 0) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(content), skiprows=skiprows, low_memory=False)


def _read_csv_path(path: Path, skiprows: int = 0) -> pd.DataFrame:
    return pd.read_csv(path, skiprows=skiprows, low_memory=False)


def _zip_member(path: Path, predicate: Callable[[str], bool]) -> str | None:
    with zipfile.ZipFile(path) as archive:
        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            raise ValueError(
                f"El archivo {path} contiene un miembro dañado: {corrupt_member}"
            )
        matches = [name for name in archive.namelist() if predicate(Path(name).name)]
        return sorted(matches)[0] if matches else None


def _find_source(
    raw_files: list[Path], filename_predicate: Callable[[str], bool]
) -> tuple[Path, str | None]:
    direct_csvs = [
        path
        for path in raw_files
        if path.suffix.lower() == ".csv" and filename_predicate(path.name)
    ]
    if direct_csvs:
        return direct_csvs[0], None

    for path in raw_files:
        if path.suffix.lower() != ".zip":
            continue
        member = _zip_member(path, filename_predicate)
        if member:
            return path, member
    raise FileNotFoundError("No se encontró una fuente CSV requerida en el directorio de datos.")


def _load_source(
    source: tuple[Path, str | None], skiprows: int = 0
) -> pd.DataFrame:
    path, member = source
    if member is None:
        return _read_csv_path(path, skiprows=skiprows)
    with zipfile.ZipFile(path) as archive:
        return _read_csv_bytes(archive.read(member), skiprows=skiprows)


def extract_sources(raw_dir: Path) -> dict[str, Any]:
    """Lee las fuentes crudas, valida archivos comprimidos y registra sus hashes."""
    raw_dir = raw_dir.resolve()
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"No existe el directorio de fuentes: {raw_dir}")

    raw_files = _all_raw_files(raw_dir)
    if not raw_files:
        raise FileNotFoundError(f"No se encontraron CSV o ZIP en {raw_dir}")
    for path in raw_files:
        if path.suffix.lower() == ".zip":
            _zip_member(path, lambda _name: False)

    hashes = {
        str(path.relative_to(raw_dir)): {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in raw_files
    }

    world_bank: dict[str, pd.DataFrame] = {}
    for indicator_code in WORLD_BANK_INDICATORS:
        filename = re.compile(
            rf"^API_{re.escape(indicator_code)}_.*\.csv$", re.IGNORECASE
        )
        source = _find_source(raw_files, lambda name: bool(filename.match(name)))
        world_bank[indicator_code] = _load_source(source, skiprows=WDI_SKIPROWS)

    metadata_pattern = re.compile(r"^Metadata_Country_.*\.csv$", re.IGNORECASE)
    metadata_source = _find_source(
        raw_files, lambda name: bool(metadata_pattern.match(name))
    )
    countries = _load_source(metadata_source)

    education_pattern = re.compile(
        rf"^{re.escape(EDUCATION_FILE)}$", re.IGNORECASE
    )
    education_source = _find_source(
        raw_files, lambda name: bool(education_pattern.match(name))
    )
    education = _load_source(education_source)

    return {
        "world_bank": world_bank,
        "countries": countries,
        "education": education,
        "hashes": hashes,
    }

"""Ejecuta las consultas de ``02_ingenieria/sql/consultas_ejemplo.sql`` sobre el almacén."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SQL_PATH = ROOT / "02_ingenieria" / "sql" / "consultas_ejemplo.sql"
DB_PATH = ROOT / "warehouse" / "salud.db"


def split_queries(sql_text: str) -> list[tuple[str, str]]:
    """Separa el archivo en ``(titulo, consulta)`` usando los comentarios ``-- Qn.``."""
    out, title, buf = [], None, []
    for line in sql_text.splitlines():
        if line.startswith("-- Q"):
            if title and buf:
                out.append((title, "\n".join(buf).strip()))
            title, buf = line[3:].strip(), []
        elif title is not None and not line.startswith("--"):
            buf.append(line)
    if title and buf:
        out.append((title, "\n".join(buf).strip()))
    return out


def main() -> None:
    """Corre cada consulta e imprime el número de filas y las primeras filas."""
    import duckdb

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    queries = split_queries(SQL_PATH.read_text(encoding="utf-8"))
    connection = duckdb.connect(str(args.db), read_only=True)
    try:
        for title, query in queries:
            frame = connection.execute(query.rstrip(";")).df()
            print(f"\n== {title}  ({len(frame)} filas)")
            print(frame.head(5).to_string(index=False))
    finally:
        connection.close()


if __name__ == "__main__":
    main()

# Fase 2 — Ingeniería de datos

## Propósito
Transformar los archivos originales en un conjunto de datos integrado, consistente y reproducible para el análisis estadístico.

## Entradas
Archivos y metadatos documentados en la fase de minería, conservados en `03_data/00_raw/`.

## Actividades
1. Inspeccionar esquemas, tipos de datos, nombres de columnas y granularidad.
2. Normalizar los códigos de país utilizando identificadores estables cuando estén disponibles.
3. Estandarizar el año y comprobar que cada registro tenga una clave país-año adecuada para su indicador.
4. Normalizar nombres de variables y unidades sin perder la definición original.
5. Detectar duplicados, valores imposibles, cambios de cobertura y registros inconsistentes.
6. Analizar los valores faltantes y documentar cualquier imputación; no rellenar automáticamente sin justificación.
7. Integrar los indicadores por país y año, comprobando cardinalidad y evitando multiplicar filas accidentalmente.
8. Generar reportes de validación y registrar las transformaciones aplicadas.
9. Exportar los resultados intermedios, limpios y consolidados a las carpetas correspondientes.

## Organización de datos
- `03_data/00_raw/`: originales sin modificar.
- `03_data/01_processed/`: datos transformados de forma inicial.
- `03_data/02_clean/`: datos limpios y validados por fuente.
- `03_data/03_consolidated/`: tabla integrada para análisis.

## Reglas de calidad
- No confundir ausencia de dato con cero.
- No combinar indicadores con unidades o definiciones distintas sin una transformación documentada.
- No eliminar países o años silenciosamente.
- Conservar trazabilidad hacia la fuente y registrar las decisiones de limpieza.
- Validar unicidad de las claves previstas y comparar filas antes y después de cada unión.

## Ejecución local

El ETL lee los indicadores WDI y la serie OWID de escolaridad, excluye agregados,
integra las fuentes por `iso3` y `anio`, y produce el panel y el almacén local.
Los originales no se modifican.

```bash
python -m pip install -r requirements.txt
make etl
make test
```

`make etl` genera `03_data/processed/panel_salud_global.csv`,
`03_data/processed/panel_salud_global.parquet`, manifiestos SHA-256 y
`warehouse/salud.db` (DuckDB).

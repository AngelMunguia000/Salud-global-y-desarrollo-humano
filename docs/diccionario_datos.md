# Diccionario de datos

## Panel maestro: `03_data/processed/panel_salud_global.{parquet,csv}`
Granularidad: un registro por país y año. Llave única: `(iso3, anio)`. 14,062 filas, 217 países, 1960–2024.

| Columna | Tipo | Unidad | Definición | Fuente / código | Nulos permitidos |
|---|---|---|---|---|---|
| `iso3` | texto | — | Código ISO 3166-1 alfa-3 del país (solo países, sin agregados) | Banco Mundial | No |
| `anio` | entero | año | Año calendario | — | No |
| `esperanza_vida` | decimal | años | Años que viviría un recién nacido con los patrones de mortalidad del año | `SP.DYN.LE00.IN` | No (tabla base) |
| `mortalidad_infantil` | decimal | por 1,000 nacidos vivos | Muertes de menores de 1 año | `SP.DYN.IMRT.IN` | Sí |
| `pib_per_capita_ppp` | decimal | US$ internacionales constantes 2021 | PIB por persona con paridad de poder adquisitivo | `NY.GDP.PCAP.PP.KD` | Sí |
| `gasto_salud_pct_pib` | decimal | % del PIB | Gasto corriente en salud (excluye capital) | `SH.XPD.CHEX.GD.ZS` | Sí |
| `gasto_salud_per_capita_ppp` | decimal | US$ internacionales corrientes | Gasto corriente en salud por persona, PPA | `SH.XPD.CHEX.PP.CD` | Sí |
| `escolaridad_promedio` | decimal | años | Años promedio de educación formal de adultos ≥ 25 | OWID / PNUD | Sí |
| `region` | texto | — | Región del Banco Mundial (7 categorías) | `Metadata_Country` | No |
| `pais` | texto | — | Nombre del país (`TableName`) | `Metadata_Country` | No |

**Regla de nulos:** la ausencia de dato **no** se rellena ni se interpreta como cero.

**Rangos de validación** (`tests/`): esperanza de vida 20–95 (el ETL excluye 9 país-año fuera de rango, ver `docs/fuentes.md`),
mortalidad infantil 0–500, gasto en salud 0–40 % del PIB, escolaridad 0–20 años, PIB y gasto per cápita > 0.

## Variables derivadas (`common/panel.py`)
| Variable | Definición |
|---|---|
| `ln_pib` | `ln(pib_per_capita_ppp)` (solo valores > 0) |
| `ln_gasto_pc` | `ln(gasto_salud_per_capita_ppp)` (solo valores > 0) |

## Almacén: `warehouse/salud.db` (DuckDB)
| Tabla | Columnas | Descripción |
|---|---|---|
| `dim_pais` | `iso3`, `pais`, `region` | Dimensión de países |
| `dim_indicador` | `codigo_indicador`, `nombre`, `unidad` | Dimensión de indicadores |
| `hechos_indicador` | `iso3`, `anio`, `codigo_indicador`, `valor` | Hechos en formato largo; índice único `(iso3, anio, codigo_indicador)` |

Consultas de ejemplo: `02_ingenieria/sql/consultas_ejemplo.sql` (`make consultas`).

## Resultados de análisis y modelado
| Archivo | Contenido |
|---|---|
| `04_analisis/tablas/*.csv` | Cobertura, descriptivos, correlaciones, σ-convergencia, R² por año |
| `04_analisis/tablas/resultados_eda.json` | Cifras clave del EDA citadas en el informe |
| `05_ciencia/resultados/modelos_coeficientes.csv` | Coeficientes, errores agrupados por país e IC 95 % (M1–M5) |
| `05_ciencia/resultados/modelos_ajuste_diagnosticos.csv` | R², RMSE, RESET, Breusch–Pagan, Jarque–Bera, Cook |
| `05_ciencia/resultados/validacion_fuera_de_muestra.csv` | MAE, RMSE y R² con validación temporal y por países |
| `05_ciencia/resultados/paises_sobre_desempeno.csv` | Residuo estandarizado por país, criterio y robustez |
| `05_ciencia/resultados/hipotesis.csv` | Veredicto de H1–H4 con evidencia |

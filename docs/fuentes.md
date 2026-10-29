# Fuentes de datos

Fecha de consulta de las descargas: octubre de 2026. Integridad verificada con SHA-256
(`03_data/processed/MANIFEST.md`, `source_hashes.json`). Los archivos originales no se modifican.

| # | Indicador | Código | Organismo / fuente | URL | Cobertura temporal | Completitud en el panel* | Licencia |
|---|---|---|---|---|---|---:|---|
| 1 | Esperanza de vida al nacer, total (años) | `SP.DYN.LE00.IN` | Banco Mundial (WDI) con datos de UN World Population Prospects, Eurostat y oficinas nacionales | https://data.worldbank.org/indicator/SP.DYN.LE00.IN | 1960–2024 | 100 % (tabla base) | CC BY 4.0 |
| 2 | Mortalidad infantil (por 1,000 nacidos vivos) | `SP.DYN.IMRT.IN` | Banco Mundial (WDI) con UN IGME (UNICEF, OMS, BM, ONU) | https://data.worldbank.org/indicator/SP.DYN.IMRT.IN | 1960–2024 | 83.9 % | CC BY 4.0 |
| 3 | PIB per cápita, PPA (US$ internacionales constantes 2021) | `NY.GDP.PCAP.PP.KD` | Banco Mundial (WDI) con ICP, Eurostat, OCDE, FMI | https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.KD | 1990–2025 | 48.3 % | CC BY 4.0 |
| 4 | Gasto corriente en salud (% del PIB) | `SH.XPD.CHEX.GD.ZS` | OMS, Global Health Expenditure Database (act. dic-2025), vía Banco Mundial | https://apps.who.int/nha/database | 2000–2024 | 32.4 % | CC BY 4.0 |
| 5 | Gasto corriente en salud per cápita, PPA (US$ internacionales corrientes) | `SH.XPD.CHEX.PP.CD` | OMS, GHED, vía Banco Mundial | https://apps.who.int/nha/database | 2000–2024 | 32.4 % | CC BY 4.0 |
| 6 | Años promedio de escolaridad, adultos ≥ 25 (ambos sexos) | `OWID:schooling` | PNUD, Human Development Report 2025, vía Our World in Data | https://ourworldindata.org/grapher/years-of-schooling | 1990–2023 | 43.2 % | CC BY 4.0 (OWID) |

\* Proporción de filas país-año con dato, sobre el panel completo de 14,062 filas (217 países, 1960–2024).
Dentro del periodo de análisis 2000–2023 la cobertura es de ≈ 87–91 % (ver `reports/informe_final.md`, §2.1).

## Archivos auxiliares
- `Metadata_Country_*.csv` (Banco Mundial): región y grupo de ingreso. Una región vacía identifica un **agregado**
  (p. ej. `WLD`, `EUU`, `LIC`), que se excluye del panel.
- `Metadata_Indicator_*.csv`: definiciones, notas y organismos fuente de cada indicador.
- `average-years-of-schooling-among-adults.metadata.json`: definición oficial de la variable de escolaridad.

## Fuentes consideradas y no incorporadas
- **OMS – Global Health Observatory (GHO):** se usó su base de gasto (GHED) a través del Banco Mundial. Los demás
  indicadores del GHO (vacunación, atención primaria) quedan como trabajo futuro (ver informe, §6).
- **Our World in Data (esperanza de vida):** duplica la serie del Banco Mundial (misma base UN WPP); se prefirió una sola
  fuente para el objetivo y evitar discrepancias de definición.

## Notas metodológicas y limitaciones de cada fuente
- La esperanza de vida de varios países es una **estimación modelada**; hay valores atípicos documentados
  (Camboya 1975–78, Ruanda 1994 por crisis históricas; República Centroafricana 2009 y 2022, Sudán del Sur 1988 y 1998
  por revisar). La regla de calidad 20–95 años del ETL (`02_ingenieria/etl/merge.py`) **excluye del panel esos 9 país-año**
  (con una advertencia en el registro); los valores originales permanecen intactos en `03_data`.
- El PIB está en dólares **constantes** de 2021 y el gasto per cápita en dólares **corrientes**: no se combinan en razones.
- La escolaridad mide años completados, **no calidad** educativa; excluye años repetidos.
- OWID incluye agregados con código `OWID_*` y filas sin código, excluidos por no ser países.

## Atribución
Banco Mundial (World Development Indicators); Organización Mundial de la Salud (GHED); PNUD (HDR 2025) a través de Our
World in Data; UN Population Division (WPP); UN Inter-agency Group for Child Mortality Estimation.

# Registro de decisiones técnicas

| # | Decisión | Razón | Alternativa descartada |
|---|---|---|---|
| D1 | Unir **solo por `(iso3, anio)`** | Los nombres de país difieren entre WDI y OWID | Unir por nombre |
| D2 | Excluir agregados usando `Region` vacía en `Metadata_Country` y códigos `OWID_*` | Regla reproducible y estricta | Lista manual de códigos |
| D3 | La **esperanza de vida es la tabla base** (left join) | Es la variable objetivo; evita multiplicar filas | Outer join |
| D4 | **No imputar** datos faltantes; análisis de casos completos 2000–2023 | Ausencia ≠ cero; contrato §5.3; el gasto en salud solo existe desde 2000 | Mediana (la usaba el modelo base inicial) o MICE |
| D5 | Periodo de modelado **2000–2023** | Intersección de las seis variables | Usar 1990–2023 y perder el gasto en salud |
| D6 | **Logaritmo** del PIB y del gasto per cápita | Rendimientos decrecientes; mejora de R² y RESET (H1) | Niveles |
| D7 | Errores estándar **agrupados por país** | Paneles con dependencia dentro del país; heterocedasticidad (Breusch–Pagan p < 0.001) | HC3 sin agrupar |
| D8 | OLS implementado con `numpy`/`scipy` en `common/ols.py` y verificado con `tests/test_ols.py` contra `sklearn` y fórmulas explícitas | Control total de errores agrupados, VIF y diagnósticos sin dependencias pesadas | `statsmodels` |
| D9 | Residuos de sobre-desempeño con **efectos fijos de año** | Sin ellos, el desplazamiento global de la curva hace que casi todos los países parezcan sobre-desempeñar | Modelo agrupado sin año |
| D10 | "Presente en ≥ 70 % de los años" = residuo **positivo** en ≥ 70 % de los años, junto a media ≥ +1 σ | El contrato no precisaba "presente"; la media ≥ +1 σ ya exige magnitud | Exigir z ≥ +1 en cada año |
| D11 | Medias regionales **sin ponderar** por población | No hay población en las fuentes elegidas | Ponderar con datos externos |
| D12 | Se **mantiene** la regla del ETL que excluye del panel los 9 país-año con esperanza de vida < 20 años (Camboya 1975–78, Ruanda 1994, Rep. Centroafricana 2009 y 2022, Sudán del Sur 1988 y 1998), con advertencia en el registro | Es el criterio de calidad ya acordado (rango 20–95). **Costo:** parte de esos casos son crisis reales, no errores; su exclusión afecta marginalmente las series regionales y la convergencia de los años 70–90 | Conservarlos y marcarlos como atípicos (recomendado como mejora: `flag_atipico`) |
| D13 | Layout `01_mineria … 05_ciencia`, `03_data/` y `warehouse/` del repositorio actual | Ya adoptado por el equipo; difiere de `data/raw`, `data/processed` del contrato original | Reestructurar |
| D14 | Almacén en **DuckDB** | Ya implementado en la capa de ingeniería | SQLite |
| D15 | Informe, documento Word y presentación se **generan por código** desde los resultados | Garantiza consistencia entre cifras y texto | Redacción manual |

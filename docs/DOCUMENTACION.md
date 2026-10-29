# Documentación técnica — Salud global y desarrollo humano

**Equipo 4** · Optativa III: Ciencia de Datos · Ingeniería en Computación · UNE Plantel Centro · Octubre 2026

**Aplicación web:** https://salud-global-equipo4.streamlit.app
**Repositorio:** https://github.com/AngelMunguia000/Salud-global-y-desarrollo-humano

---

## Índice
1. Descripción general
2. Tecnologías
3. Arquitectura y flujo de datos
4. Estructura del repositorio
5. Módulos del sistema
6. Modelo de datos
7. Instalación y ejecución
8. Pruebas automáticas
9. Despliegue de la aplicación web
10. Decisiones técnicas
11. Limitaciones y trabajo futuro

## 1. Descripción general

Sistema de ciencia de datos que integra indicadores de salud, ingreso y educación de 217 países (1960–2024) para responder:

> ¿Qué países alcanzan una esperanza de vida superior a la que cabría esperar según su nivel de ingreso y otros indicadores de desarrollo?

Preguntas de investigación:
- **P1.** ¿Qué tan fuerte es la relación ingreso–esperanza de vida y es lineal?
- **P2.** ¿Qué países logran alta esperanza de vida con bajo ingreso?
- **P3.** ¿Cómo ha evolucionado la desigualdad en salud entre regiones?

El sistema va de los archivos originales hasta los entregables sin pasos manuales: extrae y verifica los datos, los integra en un panel país-año, los guarda en un almacén analítico, ejecuta el análisis exploratorio y los modelos, genera el informe y publica una aplicación web interactiva.

**Resultados principales:**
- Duplicar el PIB per cápita se asocia con **+4.2 años** de esperanza de vida; con logaritmo, el R² ajustado pasa de 0.47 a 0.68.
- Gasto en salud y escolaridad aportan de forma modesta y frágil (pierden significancia con efectos fijos).
- **8 países** superan de forma robusta lo que predice su ingreso (2015–2023).
- La dispersión entre países bajó de 9.9 años (1990) a 7.1 (2023): hay convergencia.

Metodología: **CRISP-DM** (detalle en `docs/metodologia.md`).

## 2. Tecnologías

| Herramienta | Uso en el proyecto |
|---|---|
| Python 3.10+ | Lenguaje de todo el sistema |
| pandas, numpy | Limpieza, transformación e integración de datos |
| pyarrow | Lectura y escritura del panel en formato Parquet |
| DuckDB | Almacén analítico local (`warehouse/salud.db`) y consultas SQL |
| scipy | Pruebas estadísticas del módulo OLS propio |
| statsmodels, scikit-learn | Modelo base, validación cruzada y gradient boosting (M6) |
| matplotlib | Figuras del análisis y del informe |
| python-docx, python-pptx | Generación automática del informe Word y la presentación |
| Streamlit, Plotly | Aplicación web interactiva |
| pytest | Pruebas automáticas (37 pruebas) |
| Make | Automatización de las fases (`make all`) |
| Git, GitHub | Control de versiones y trabajo en ramas |
| Streamlit Community Cloud | Hospedaje de la aplicación web |

## 3. Arquitectura y flujo de datos

El proyecto está organizado en fases numeradas; cada fase lee lo que produjo la anterior:

```
 03_data/ (CSV originales del Banco Mundial, OMS y OWID)
     │
     ▼  02_ingenieria/etl   extract → transform → merge → load
 03_data/processed/panel_salud_global.parquet  +  warehouse/salud.db
     │
     ▼  04_analisis/scripts/eda_completo.py
 04_analisis/tablas/*.csv  +  04_analisis/visualizaciones/*.png
     │
     ▼  05_ciencia/scripts/modelos.py
 05_ciencia/resultados/*.csv  +  05_ciencia/figuras/*.png
     │
     ├─▶ reports/generar_informe.py   → informe_final.md/.docx, presentacion_final.pptx
     └─▶ 06_despliegue/app.py         → aplicación web (Streamlit Cloud)
```

Principios del diseño:
- **Datos originales intactos:** nunca se sobrescriben; su integridad se verifica con SHA-256.
- **Reproducible:** `make all` regenera todo desde los datos originales; semilla fija (`random_state=42`).
- **Una sola fuente de cifras:** el informe, la presentación y la web leen los mismos archivos de resultados, por eso sus números coinciden.
- **Código compartido en `common/`:** carga del panel, regresión OLS y estilo gráfico se escriben una sola vez.

## 4. Estructura del repositorio

| Carpeta / archivo | Contenido |
|---|---|
| `01_mineria/` | Contrato del proyecto y evaluación de fuentes |
| `02_ingenieria/etl/` | Pipeline ETL: `extract.py`, `transform.py`, `merge.py`, `load.py`, `pipeline.py`, `consultas.py` |
| `02_ingenieria/sql/` | Consultas SQL de ejemplo sobre el almacén |
| `03_data/` | Datos originales y `processed/` con el panel final |
| `04_analisis/` | Análisis exploratorio: scripts, notebooks, tablas y figuras |
| `05_ciencia/` | Modelos M0–M6: scripts, notebooks, resultados y figuras |
| `06_despliegue/` | Aplicación web en Streamlit |
| `common/` | Módulos compartidos: `panel.py`, `ols.py`, `style.py` |
| `docs/` | Documentación: metodología, decisiones, diccionario, fuentes y este documento |
| `reports/` | Informe final, presentación y su generador |
| `tests/` | Pruebas automáticas |
| `warehouse/` | Almacén DuckDB `salud.db` |
| `.streamlit/config.toml` | Tema visual de la aplicación web |
| `Makefile`, `requirements.txt` | Automatización y dependencias |

## 5. Módulos del sistema

### 5.1 Ingeniería de datos (`02_ingenieria/etl/`)

Convierte los archivos originales en un panel limpio de una fila por país y año.

| Archivo | Función principal | Qué hace |
|---|---|---|
| `extract.py` | `extract_sources` | Lee los CSV del Banco Mundial (y sus ZIP) y de OWID; calcula el SHA-256 de cada archivo (`sha256_file`) |
| `transform.py` | `transform_sources` | Pasa las tablas anchas del Banco Mundial a formato largo (`transform_world_bank`), estandariza la escolaridad de OWID (`transform_education`) y obtiene la lista de países con región (`transform_countries`), excluyendo agregados |
| `merge.py` | `merge_indicators` | Une todos los indicadores por `(iso3, anio)` con la esperanza de vida como tabla base; falla si una fuente duplica país-año y aplica la regla de calidad de 20 a 95 años |
| `load.py` | `save_panel`, `load_warehouse` | Guarda el panel en Parquet y CSV, escribe el manifiesto de hashes y crea el almacén DuckDB |
| `pipeline.py` | `run_pipeline`, `main` | Orquesta los cuatro pasos; se ejecuta con `python -m 02_ingenieria.etl.pipeline` |
| `consultas.py` | `main` | Ejecuta las consultas de `02_ingenieria/sql/consultas_ejemplo.sql` e imprime los resultados |

**Salidas:** `03_data/processed/panel_salud_global.parquet` y `.csv`, `MANIFEST.md`, `source_hashes.json`, `warehouse/salud.db`.

### 5.2 Módulos compartidos (`common/`)

| Archivo | Funciones | Qué hace |
|---|---|---|
| `panel.py` | `load_panel`, `add_derived`, `complete_cases` | Carga y valida el panel (Parquet, o CSV de respaldo), agrega logaritmos de PIB y gasto, y filtra casos completos del periodo 2000–2023 |
| `ols.py` | `fit_ols`, `vif`, `breusch_pagan`, `reset_test`, `jarque_bera`, `cooks_distance`, `diagnostics` | Regresión por mínimos cuadrados con errores robustos (HC3 o agrupados por país) y diagnósticos, implementada con numpy y scipy y verificada contra scikit-learn |
| `style.py` | `aplicar_estilo`, `pie_fuente` | Paleta Okabe–Ito apta para daltonismo, nombres de regiones en español y pie de fuente en las figuras |

### 5.3 Análisis exploratorio (`04_analisis/`)

`scripts/eda_completo.py` genera las tablas y figuras que responden P1 y P3:

| Función | Resultado |
|---|---|
| `cobertura` | Porcentaje de datos por variable y región |
| `descriptivos`, `correlaciones` | Estadísticos descriptivos; matrices de Pearson y Spearman |
| `ajuste_por_anio` | R² de esperanza de vida contra PIB, lineal vs. logaritmo, en cada año |
| `series_regionales` | Esperanza de vida media por región y año |
| `convergencia_sigma`, `convergencia_beta` | Dispersión entre países en el tiempo y regresión de convergencia β |

**Salidas:** `04_analisis/tablas/` (CSV y `resultados_eda.json`) y `04_analisis/visualizaciones/` (9 figuras).

### 5.4 Ciencia de datos (`05_ciencia/`)

`scripts/modelos.py` ajusta y evalúa los modelos y responde P2:

| Función | Qué hace |
|---|---|
| `ajustar`, `ajustar_todos` | Ajusta M0 a M5 con errores agrupados por país |
| `validacion` | Validación temporal (entrena hasta 2017) y por países no vistos (5 pliegues) |
| `modelo_ml` | M6: gradient boosting como referencia no lineal |
| `residuos_z`, `evaluar_paises` | Residuo estandarizado por país y criterio de sobre-desempeño (≥ +1σ y positivo en ≥ 70 % de los años) |
| `leave_one_country_out`, `sobre_desempeno` | Pruebas de robustez y lista final de países |
| `evaluar_hipotesis` | Veredicto de H1–H4 con su evidencia numérica |

| Modelo | Especificación |
|---|---|
| M0 | Esperanza de vida ~ PIB (niveles) |
| M1 | ~ ln(PIB) |
| M2 | ~ ln(PIB) + ln(gasto en salud per cápita) |
| M3 | ~ ln(PIB) + ln(gasto) + escolaridad (**principal**) |
| M4 | M3 + efectos fijos de región y año |
| M5 | M3 + efectos fijos de país y año |
| M6 | Gradient boosting (solo referencia) |

`scripts/modelo_base.py` conserva el modelo base inicial del equipo.

**Salidas:** `05_ciencia/resultados/` (coeficientes, diagnósticos, validación, países, hipótesis) y `05_ciencia/figuras/`.

### 5.5 Reportes (`reports/`)

`generar_informe.py` toma los resultados y escribe `informe_final.md`, `informe_final.docx` y `presentacion_final.pptx`, de modo que las cifras del texto siempre coinciden con las calculadas.

### 5.6 Aplicación web (`06_despliegue/`)

`app.py` es una aplicación Streamlit de cinco páginas, ordenadas según la rúbrica de presentación:

| Página | Contenido |
|---|---|
| 1 · Problema y pregunta | Pregunta central, preguntas de investigación y cifras clave |
| 2 · Los datos | Fuentes, periodo de estudio y mapa de cobertura |
| 3 · Preparación | Decisiones del ETL con su justificación; R² lineal vs. logaritmo |
| 4 · Análisis y hallazgos | Explorador interactivo por año y país, modelos, validación, sobre-desempeño y convergencia |
| 5 · Conclusiones | Hipótesis, recomendación y limitaciones |

Características:
- Solo **lee** resultados ya generados; no entrena modelos, por eso carga rápido.
- Usa `st.cache_data` para leer cada archivo una sola vez.
- Cada gráfica incluye una caja **"¿Por qué?"** que justifica el dato o el método.
- Reutiliza `common/panel.py` y `common/style.py`.

## 6. Modelo de datos

### 6.1 Panel (`panel_salud_global.parquet`)

Una fila por país y año (llave `iso3` + `anio`); 217 países, 1960–2024.

| Columna | Descripción | Unidad | Fuente |
|---|---|---|---|
| `iso3` | Código ISO de 3 letras del país | — | Banco Mundial |
| `anio` | Año | — | — |
| `pais`, `region` | Nombre y región del Banco Mundial | — | Banco Mundial |
| `esperanza_vida` | Esperanza de vida al nacer (variable objetivo) | años | Banco Mundial (UN WPP) |
| `mortalidad_infantil` | Mortalidad infantil | por 1,000 nacidos vivos | Banco Mundial (UN IGME) |
| `pib_per_capita_ppp` | PIB per cápita | US$ PPA constantes 2021 | Banco Mundial (ICP) |
| `gasto_salud_pct_pib` | Gasto corriente en salud | % del PIB | OMS (GHED) |
| `gasto_salud_per_capita_ppp` | Gasto en salud per cápita | US$ PPA corrientes | OMS (GHED) |
| `escolaridad_promedio` | Años promedio de escolaridad (≥ 25 años) | años | PNUD vía OWID |

Definiciones completas: `docs/diccionario_datos.md`; fuentes y licencias: `docs/fuentes.md`.

### 6.2 Almacén DuckDB (`warehouse/salud.db`)

Esquema dimensional:

| Tabla | Columnas | Contenido |
|---|---|---|
| `dim_pais` | `iso3`, `pais`, `region` | Un registro por país |
| `dim_indicador` | `codigo_indicador`, `nombre`, `unidad` | Un registro por indicador |
| `hechos_indicador` | `iso3`, `anio`, `codigo_indicador`, `valor` | Un valor por país, año e indicador |

Ejemplos de consulta en `02_ingenieria/sql/consultas_ejemplo.sql` (se ejecutan con `make consultas`).

## 7. Instalación y ejecución

**Requisitos:** Python 3.10 o superior y Git. `make` es opcional.

```
git clone https://github.com/AngelMunguia000/Salud-global-y-desarrollo-humano.git
cd Salud-global-y-desarrollo-humano
git switch feature/despliegue-streamlit
pip install -r requirements.txt
```

| Comando `make` | Equivalente sin make | Qué hace |
|---|---|---|
| `make etl` | `python -m 02_ingenieria.etl.pipeline` | Construye el panel y el almacén |
| `make analisis` | `python -m 04_analisis.scripts.eda_completo` | Tablas y figuras del EDA |
| `make modelos` | `python -m 05_ciencia.scripts.modelos` | Modelos M0–M6 y resultados |
| `make informe` | `python -m reports.generar_informe` | Informe y presentación |
| `make consultas` | `python -m 02_ingenieria.etl.consultas` | Consultas SQL de ejemplo |
| `make test` | `python -m pytest -q` | Pruebas automáticas |
| `make app` | `python -m streamlit run 06_despliegue/app.py` | Aplicación web en http://localhost:8501 |
| `make all` | — | Todas las fases, de los datos originales al informe |

Todos los comandos se ejecutan desde la raíz del repositorio.

## 8. Pruebas automáticas

37 pruebas con pytest (`python -m pytest -q`), todas aprobadas:

| Archivo | Pruebas | Qué verifica |
|---|---|---|
| `tests/test_etl.py` | 7 | Llave única país-año, exclusión de agregados, rango 20–95 años y rechazo de duplicados, con datos sintéticos y con el panel real |
| `tests/test_ols.py` | 9 | Coeficientes iguales a scikit-learn, errores HC3, errores agrupados, VIF, Breusch–Pagan, RESET y Cook |
| `tests/test_analisis_modelos.py` | 16 | Muestra del modelo, signos de M3, log mejor que niveles, criterio de sobre-desempeño, convergencia, consultas SQL, hipótesis y existencia de entregables |
| `tests/test_app.py` | 5 | Cada página de la aplicación web se ejecuta sin errores |

## 9. Despliegue de la aplicación web

La aplicación está publicada en **Streamlit Community Cloud**:

| Parámetro | Valor |
|---|---|
| URL | https://salud-global-equipo4.streamlit.app |
| Repositorio | `AngelMunguia000/Salud-global-y-desarrollo-humano` |
| Rama | `feature/despliegue-streamlit` |
| Archivo principal | `06_despliegue/app.py` |
| Dependencias | `06_despliegue/requirements.txt` (solo lo que usa la app) |
| Tema | Claro, fijado en `.streamlit/config.toml` |

- Cada push a la rama vuelve a desplegar la app automáticamente.
- Un cambio en `.streamlit/config.toml` requiere reiniciarla desde **Manage app → Reboot app**.
- Solo el dueño del repositorio puede desplegar (Streamlit exige permisos de administrador).

Guía paso a paso y solución de problemas: `06_despliegue/README_despliegue.md`.

## 10. Decisiones técnicas

Las más importantes (registro completo con alternativas descartadas en `docs/decisiones.md`):

| Decisión | Razón |
|---|---|
| Unir solo por `(iso3, anio)` | Los nombres de país difieren entre fuentes |
| Excluir agregados (Mundo, regiones, grupos de ingreso) | No son países; duplicarían observaciones |
| No imputar datos faltantes | Ausencia no es cero; se trabaja con casos completos |
| Periodo de modelado 2000–2023 | Es cuando existen las seis variables |
| Logaritmo del PIB y del gasto | Rendimientos decrecientes |
| Errores agrupados por país | Las observaciones de un país no son independientes |
| OLS propio en `common/ols.py` | Control total de errores agrupados y diagnósticos; verificado contra scikit-learn |
| Informe, presentación y web generados desde los resultados | Las cifras siempre coinciden |
| App web solo de lectura | Carga rápida y sin recalcular en la nube |

## 11. Limitaciones y trabajo futuro

**Limitaciones:**
- Estudio observacional: los resultados son asociaciones, no causas.
- El gasto en salud tiene cobertura desigual por región; no se imputaron faltantes.
- Colinealidad alta entre PIB y gasto (VIF ≈ 8–9).
- Medias regionales sin ponderar por población.
- El umbral de sobre-desempeño (+1σ, 70 %) es una convención del equipo.

**Trabajo futuro:**
- Ponderar por población.
- Incorporar indicadores de la OMS-GHO (vacunación, atención primaria).
- Modelos de panel dinámico y análisis por grupos de ingreso.
- Unir la rama `feature/despliegue-streamlit` a `main` cuando el equipo lo decida.

# Salud-global-y-desarrollo-humano

# Salud global y desarrollo humano

## Descripción
Proyecto de ciencia de datos para estudiar la relación entre el desarrollo socioeconómico y los resultados de salud de los países a lo largo del tiempo. Se analizará especialmente la esperanza de vida y su asociación con el ingreso, el gasto en salud y la educación.

## Pregunta central
¿Qué países alcanzan una esperanza de vida superior a la que cabría esperar según su nivel de ingreso y otros indicadores de desarrollo?

## Objetivos
- Integrar indicadores comparables por país y año.
- Evaluar cobertura, calidad y limitaciones de las fuentes.
- Analizar tendencias temporales y diferencias regionales.
- Cuantificar asociaciones mediante modelos estadísticos.
- Identificar países con residuos positivos, interpretados como resultados superiores a la predicción del modelo y no como prueba causal.

## Fases del proyecto
1. **Minería:** localizar, documentar y obtener los datos.
2. **Ingeniería:** limpiar, validar, estandarizar e integrar los datasets.
3. **Análisis:** explorar distribuciones, correlaciones, tendencias y desigualdades.
4. **Ciencia de datos:** construir y evaluar modelos de regresión y analizar sus residuos.

## Fuentes candidatas
- [Our World in Data](https://ourworldindata.org/)
- [OMS — Global Health Observatory](https://www.who.int/data/gho)
- [Banco Mundial — Datos Abiertos](https://data.worldbank.org/)

Las variables e indicadores definitivos se elegirán después de revisar disponibilidad, definiciones, cobertura temporal y comparabilidad.

## Flujo de datos
`01_mineria → 02_ingenieria → 03_data → 04_analisis → 05_ciencia → 06_despliegue`

Los datos originales se conservarán sin sobrescribir. Se documentarán las transformaciones, los indicadores, las unidades y las limitaciones.

## Estructura del repositorio

A continuación se describe la función de cada carpeta y de los documentos principales del proyecto:

- `01_mineria/`: carpeta dedicada a la fase de adquisición y evaluación de fuentes.
  - `README_mineria.md`: metodología, fuentes, indicadores y entregables.
  - `CONTRATO_PROYECTO_SALUD_GLOBAL.md`: acuerdo técnico, alcance y criterios.

- `02_ingenieria/`: contiene la infraestructura del pipeline de ETL (extracción, transformación y carga).
  - `README_ingenieria.md`: describe la fase de ingeniería, las transformaciones esperadas y el flujo de validación del dataset.
  - `etl/`: scripts Python que ejecutan cada paso del flujo:
    - `extract.py`: descarga o lectura de fuentes originales.
    - `transform.py`: limpieza, normalización y transformación de variables.
    - `merge.py`: integración de múltiples fuentes por país y año.
    - `load.py`: almacenamiento en archivos o bases de datos.
    - `pipeline.py`: orquestación del ETL completo.
    - `__init__.py`: marca el paquete Python.

- `04_analisis/`: espacio para análisis exploratorio, estadística descriptiva y visualizaciones iniciales.
  - `README_analisis.md`: define la etapa de análisis exploratorio, preguntas de investigación y entregables esperados.

- `05_ciencia/`: carpeta para el modelado estadístico y la evaluación de resultados.
  - `README_ciencia.md`: documenta el objetivo del modelado, variables candidatas, métricas de validación y criterios para analizar residuos.

- `03_data/`: conserva los datos del proyecto organizados por etapas de procesamiento.
  - `README_data.md`: describe la estructura de los datos (`00_raw`, `01_processed`, `02_clean`, `03_consolidated`) y las reglas de tratamiento.
  - `00_raw/`: copias originales sin modificar.
  - `01_processed/`: datos transformados iniciales.
  - `02_clean/`: datos depurados y validados.
  - `03_consolidated/`: archivo conjunto para análisis.
  - `processed/`: dataset final generado para uso analítico (`panel_salud_global.csv`, `panel_salud_global.parquet`, `MANIFEST.md`, `source_hashes.json`).
  - Subcarpetas como `API_.../`: archivos descargados de indicadores del Banco Mundial y sus metadatos.

- `docs/`: documentación transversal del proyecto.
  - `README_docs.md`: indica la documentación general del proyecto, fuentes, diccionario de datos y metodología.

- `reports/`: resultados y entregables finales. Aquí no se guardan notebooks de trabajo, sino reportes, gráficos y resúmenes finales.
  - `README.md`: explica el propósito de la carpeta y el tipo de material que debe incluirse.

- `tests/`: pruebas automáticas del flujo de ETL y validación de calidad.
  - `test_etl.py`: verifica que el proceso de extracción, transformación y consolidación funcione correctamente.

- `common/`: módulos compartidos (carga del panel, OLS con errores robustos y diagnósticos, estilo gráfico).

- `warehouse/`: almacenamiento persistente para resultados analíticos o bases de datos locales.
  - `salud.db`: base de datos del proyecto para consultar el panel consolidado.

- `06_despliegue/`: aplicación web en Streamlit que presenta el proyecto siguiendo la rúbrica de presentación.
  - `app.py`: la aplicación (solo lee resultados ya generados).
  - `requirements.txt`: dependencias mínimas para Streamlit Cloud.
  - `README_despliegue.md`: cómo ejecutarla en local y cómo desplegarla en Streamlit Cloud.

- `requirements.txt`: dependencias del proyecto (bibliotecas de Python necesarias para análisis y ETL).
- `Makefile`: automatiza tareas repetitivas como ejecución del ETL y validación de calidad.
- `README.md`: documento principal del proyecto, con descripción general, objetivos, fases y estructura del repositorio.

## Alcance y precauciones
El análisis observacional permite estudiar asociaciones, pero no demuestra causalidad por sí solo. Las comparaciones entre países deberán considerar datos faltantes, cambios metodológicos, diferencias en definiciones y posibles sesgos de cobertura.

## Ejecución completa
```bash
make install   # dependencias
make all       # ETL → EDA → modelos → informe/presentación → pruebas
make help      # lista de comandos (etl, analisis, modelos, informe, consultas, test, app)
make app       # aplicación web en http://localhost:8501
```
Todo se regenera desde los datos originales de `03_data/` (verificados con SHA-256).

## Resultados principales
- **Informe final:** `reports/informe_final.md` (y `.docx`); presentación en `reports/presentacion_final.pptx`.
- **Panel:** 217 países, 1960–2024; modelos sobre 4,339 país-año (186 países, 2000–2023).
- **Hallazgos:** el ingreso se asocia con más esperanza de vida con rendimientos decrecientes (R² aj. 0.47 → 0.68 al usar logaritmo); gasto en salud y escolaridad aportan de forma frágil; 8 países superan de forma robusta lo que predice su ingreso; las brechas entre países y regiones convergen.
- Resultados numéricos: `04_analisis/tablas/` y `05_ciencia/resultados/`. Documentación: `docs/`.

## Estado
Proyecto **completo** en sus cinco fases (minería, ingeniería, análisis, ciencia de datos y reporte), con aplicación web en `06_despliegue/`. Pendientes: publicar la app en Streamlit Cloud (ver `06_despliegue/README_despliegue.md`) y firmas del contrato (`01_mineria/CONTRATO_PROYECTO_SALUD_GLOBAL.md`, §9 y §13).

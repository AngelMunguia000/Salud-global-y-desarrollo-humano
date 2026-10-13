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
`Fuentes originales → data/00_raw → data/01_processed → data/02_clean → data/03_consolidated → análisis y modelos`

Los datos originales se conservarán sin sobrescribir. Se documentarán las transformaciones, los indicadores, las unidades y las limitaciones.

## Estructura
- `mineria/`: investigación y adquisición de datos.
- `ingenieria/`: limpieza, integración y validación.
- `analisis/`: análisis exploratorio y visualizaciones.
- `ciencia/`: modelado, evaluación y análisis de residuos.
- `data/`: datos organizados por etapa.
- `docs/`: metodología, fuentes y diccionario de datos.
- `reports/`: resultados y entregables finales.

## Alcance y precauciones
El análisis observacional permite estudiar asociaciones, pero no demuestra causalidad por sí solo. Las comparaciones entre países deberán considerar datos faltantes, cambios metodológicos, diferencias en definiciones y posibles sesgos de cobertura.

## Estado
Proyecto en fase inicial de organización y diseño del pipeline. Los indicadores, el periodo de estudio y los modelos se concretarán conforme se evalúen las fuentes.

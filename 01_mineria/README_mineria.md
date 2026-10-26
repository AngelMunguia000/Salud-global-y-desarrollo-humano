# Fase 1 — Minería de datos

## Propósito
Investigar, seleccionar y obtener los datasets necesarios para estudiar la relación entre salud y desarrollo humano. En esta fase se evalúan las fuentes antes de integrar o modificar los datos.

## Fuentes candidatas
- Our World in Data (OWID).
- OMS — Global Health Observatory (GHO).
- Banco Mundial — Datos Abiertos.

## Actividades
1. Definir las preguntas de investigación y los indicadores candidatos.
2. Localizar los archivos CSV, descargas oficiales o API pertinentes.
3. Registrar para cada indicador su nombre, definición, unidad, fuente, URL, frecuencia y cobertura temporal.
4. Revisar cobertura por país y año, valores ausentes, duplicados y posibles cambios metodológicos.
5. Documentar licencias, atribución y limitaciones de uso.
6. Guardar una copia sin modificar de cada archivo original en `03_data/00_raw/`.
7. Elaborar un inventario de fuentes y justificar la selección final.

## Variables candidatas
- Esperanza de vida al nacer.
- Mortalidad infantil.
- PIB per cápita.
- Gasto en salud, indicando si es per cápita o porcentaje del PIB.
- Años de escolaridad u otro indicador educativo comparable.
- País, código de país, región y año.

La lista es provisional: no se combinarán indicadores hasta comprobar que sus definiciones y unidades son compatibles.

## Entregables
- Inventario de fuentes e indicadores.
- Archivos originales conservados en `03_data/00_raw/`.
- Notebook de exploración inicial.
- Registro de cobertura, calidad, licencias y limitaciones.
- Justificación de los indicadores seleccionados.

## Criterios de salida
La fase termina cuando se conocen las fuentes disponibles, sus limitaciones y el conjunto de indicadores que razonablemente puede integrarse por país y año.

## Estructura sugerida
- `notebooks/`: exploración y evaluación de fuentes.
- `scripts/`: descarga reproducible cuando sea necesaria.
- `fuentes.md`: catálogo de fuentes, enlaces y notas metodológicas.

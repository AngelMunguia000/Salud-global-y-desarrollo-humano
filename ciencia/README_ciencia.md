# Fase 4 — Ciencia de datos y modelado

## Propósito
Construir y evaluar modelos estadísticos que estimen la esperanza de vida a partir de indicadores de desarrollo, y estudiar qué países quedan por encima de las predicciones.

## Objetivo de modelado
Variable objetivo candidata: esperanza de vida al nacer. Predictores candidatos: PIB per cápita, gasto en salud y educación, sujetos a disponibilidad, comparabilidad y análisis exploratorio.

## Actividades
1. Definir la población, el periodo y las variables del modelo.
2. Establecer un modelo base interpretable.
3. Evaluar transformaciones justificadas, por ejemplo logaritmo del PIB per cápita si la relación lo requiere.
4. Comparar regresión simple y regresión múltiple.
5. Separar entrenamiento y evaluación de manera coherente con la estructura temporal y por país, evitando fugas de información.
6. Evaluar con métricas como MAE, RMSE y R², junto con diagnósticos de residuos.
7. Revisar supuestos, colinealidad, observaciones influyentes y sensibilidad a la selección de países y años.
8. Calcular residuos: observado menos predicho.
9. Identificar países con residuos positivos persistentes o relevantes y comprobar la incertidumbre antes de destacarlos.
10. Documentar limitaciones y evitar atribuciones causales que el diseño observacional no permita.

## Interpretación de residuos
Un residuo positivo indica que la esperanza de vida observada supera la estimada por el modelo dadas las variables incluidas. No demuestra por sí mismo que las políticas de salud sean mejores ni que la diferencia sea causada por un factor concreto. Deben considerarse incertidumbre, variables omitidas, calidad de datos y efectos de año o región.

## Entregables
- Notebook de modelado reproducible.
- Modelo base y modelos comparados.
- Métricas y diagnósticos de evaluación.
- Tabla documentada de residuos por país y año.
- Visualizaciones de observado frente a predicho y análisis de residuos.
- Conclusiones, limitaciones y posibles siguientes pasos.

## Criterios de éxito
- Modelo evaluado con datos no utilizados para ajustar sus parámetros.
- Efectos y asociaciones comunicados con unidades e incertidumbre cuando corresponda.
- Países con residuos positivos identificados mediante criterios explícitos y análisis de robustez.
- Resultados reproducibles y limitaciones claramente explicadas.

## Nota
Esta fase no incluye por ahora una base de datos MongoDB ni despliegue de aplicaciones. La prioridad es un flujo de análisis reproducible.

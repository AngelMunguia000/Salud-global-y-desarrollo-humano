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

## Organización de la fase

- `scripts/`: código Python reproducible para construir y evaluar modelos.
- `notebooks/`: experimentación, comparación de especificaciones y visualización
  de resultados.
- `modelos/`: espacio para artefactos de modelos cuando se decida conservarlos.
- `evaluacion/`: métricas, predicciones y residuos generados por los scripts.

El modelo inicial está en `scripts/modelo_base.py`. Usa los últimos cinco años
como conjunto de prueba temporal para evitar entrenar con observaciones futuras.
Se ejecuta desde la raíz con:

```bash
python 05_ciencia/scripts/modelo_base.py
```

## Estado y contenido (implementado)
- `scripts/modelos.py` (`make modelos`): modelos M0–M5 (MCO con errores agrupados por país), M6 (gradient boosting), diagnósticos (VIF, Breusch–Pagan, RESET, Jarque–Bera, Cook), validación temporal y por países, criterio de sobre-desempeño con robustez (M3 y *leave-one-country-out*) y veredicto de H1–H4.
- Salidas: `resultados/*.csv|json` y 5 figuras en `figuras/`.
- `scripts/modelo_base.py` y `evaluacion/` son el modelo base inicial (con imputación por mediana); quedan como referencia y están superados por `modelos.py`.
- Metodología y decisiones: `docs/metodologia.md`, `docs/decisiones.md`.

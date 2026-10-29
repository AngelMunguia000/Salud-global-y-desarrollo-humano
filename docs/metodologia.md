# Metodología

Marco: **CRISP-DM** adaptado a 7 semanas. Detalle y criterios de aceptación: `01_mineria/CONTRATO_PROYECTO_SALUD_GLOBAL.md`.

## 1. Comprensión del problema
Pregunta central: ¿qué factores de desarrollo (ingreso, educación, gasto en salud) se asocian con la esperanza de vida y
qué países "rinden más" de lo que su riqueza predice? Preguntas P1 (ingreso–esperanza de vida), P2 (sobre-desempeño),
P3 (desigualdad regional). Hipótesis falsables H1–H4 en el contrato (§1.4).

## 2. Datos (minería e ingeniería)
1. **Extracción:** lectura de los CSV originales (WDI con `skiprows=4`) y verificación SHA-256.
2. **Transformación:** formato largo (`melt`), `iso3` normalizado, exclusión estricta de agregados del Banco Mundial
   (región vacía) y de OWID (códigos `OWID_*` o sin código).
3. **Integración:** unión por `(iso3, anio)` con esperanza de vida como tabla base y comprobación de que ninguna
   unión altera el número de filas.
4. **Carga:** panel en Parquet y CSV, y almacén DuckDB con esquema dimensional.
5. **Calidad:** pruebas automáticas (unicidad de llave, ausencia de agregados, rangos válidos).

## 3. Análisis exploratorio
Cobertura por variable y región; descriptivos; correlaciones de Pearson y Spearman sobre casos completos;
dispersión ingreso–esperanza de vida en escala logarítmica; series regionales; σ-convergencia (desviación estándar entre
países y entre medias regionales) y β-convergencia (ganancia anual 1990–2023 frente a nivel inicial).

## 4. Modelado
Muestra: casos completos de las variables de M3 en **2000–2023** (periodo común, limitado por el gasto en salud).

| Modelo | Especificación |
|---|---|
| M0 | Esperanza de vida ~ PIB (niveles) |
| M1 | ~ ln(PIB) |
| M2 | ~ ln(PIB) + ln(gasto en salud per cápita) |
| M3 | ~ ln(PIB) + ln(gasto pc) + escolaridad (**principal**) |
| M4 | M3 + efectos fijos de región y año |
| M5 | M3 + efectos fijos de país y año |
| M6 | Gradient boosting (solo chequeo de no linealidades; no se usa para inferencia) |

- **Inferencia:** MCO con errores estándar **agrupados por país** (las observaciones de un país no son independientes).
- **Diagnósticos:** VIF, Breusch–Pagan (Koenker), RESET de Ramsey, Jarque–Bera, apalancamiento y distancia de Cook.
- **Validación:** (a) temporal: entrena hasta 2017, prueba 2018–2023; (b) por países no vistos: `GroupKFold` de 5 pliegues.
  Los modelos con efectos fijos de país no pueden predecir países nuevos, por lo que solo M0–M3 (+ región) y M6 se validan así.

## 5. Países de sobre-desempeño (contrato §5.6)
1. Modelo de riqueza M1 con efectos fijos de año (1990–2023), para separar el desplazamiento global de la curva.
2. Residuo estandarizado `z = residuo / σ̂` por país-año; ventana **2015–2023**.
3. **Criterio:** `z` medio ≥ +1 y `z > 0` en ≥ 70 % de los años (mínimo 5 años).
4. **Robustez:** se exige además cumplir el criterio (a) con M3 más efectos de año, y (b) con M1 reajustado dejando
   fuera al propio país (*leave-one-country-out*). Robusto = cumple las tres.

## 6. Evaluación
Veredicto de H1–H4 con evidencia numérica (`05_ciencia/resultados/hipotesis.csv`) y síntesis en `reports/informe_final.md`.

## 7. Reproducibilidad
`make all` regenera, desde `03_data` y sin pasos manuales, el panel, el almacén, las pruebas, el EDA, los modelos y el
informe. Semilla fija (`random_state=42`).

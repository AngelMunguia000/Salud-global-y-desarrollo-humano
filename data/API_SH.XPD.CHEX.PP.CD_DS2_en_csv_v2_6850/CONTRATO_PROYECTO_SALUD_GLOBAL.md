# CONTRATO DE PROYECTO DE MINERÍA DE DATOS
## Salud global y desarrollo humano

| Campo | Detalle |
|---|---|
| **Proyecto** | Salud global y desarrollo humano |
| **Materia** | Optativa III · Ciencia de Datos (Ingeniería en Computación, UNE Plantel Centro) |
| **Equipo** | N.º 4 — Angel David Munguia Zuñiga, Luis Alberto Reyes Estrada, Gabriel Isaac Marquez Romo |
| **Dominio** | Salud pública / investigación |
| **Metodología** | CRISP-DM (adaptada a 7 semanas) |
| **Versión / fecha** | 1.0 · 2026-10-26 |
| **Estado** | Borrador para aprobación del equipo |

---

## 1. Propósito y alcance

### 1.1 Propósito
Este contrato define de forma vinculante **qué se va a hacer, con qué datos, con qué métodos, bajo qué criterios de calidad y cómo se entregará** el proyecto. Actúa como especificación técnica y acuerdo de trabajo entre los integrantes del equipo y el docente evaluador.

### 1.2 Problema de negocio / investigación
> Analizar qué factores de desarrollo (**ingreso, educación, gasto en salud**) se asocian con la **esperanza de vida**, e identificar países que **"rinden más" de lo que su riqueza predice**.

### 1.3 Preguntas de investigación

| ID | Pregunta | Tipo de análisis |
|---|---|---|
| **P1** | ¿Qué tan fuerte es la relación entre el ingreso de un país y su esperanza de vida? ¿Es lineal o se aplana? | Correlación, modelo log-lineal, comparación de formas funcionales |
| **P2** | ¿Qué países logran alta esperanza de vida con bajo ingreso y qué podemos aprender de ellos? | Análisis de residuos, perfilado de *outliers* positivos |
| **P3** | ¿Cómo ha evolucionado la desigualdad en salud entre regiones en las últimas décadas? | Series temporales, σ-convergencia / β-convergencia regional |

### 1.4 Hipótesis de trabajo (falsables)

- **H1.** La relación esperanza de vida ~ PIB per cápita es **cóncava** (rendimientos decrecientes): el ajuste con `ln(PIB)` supera significativamente al ajuste lineal en `PIB`.
- **H2.** El gasto en salud y los años de escolaridad aportan poder explicativo **adicional** al ingreso (ΔR² ajustado > 0 y coeficientes significativos tras controlar por multicolinealidad).
- **H3.** Existe un conjunto no vacío de países con residuo positivo sostenido (≥ 1 σ en varios años) que constituyen casos de "sobre-desempeño" robustos a la especificación.
- **H4.** La brecha de esperanza de vida entre regiones **converge** de 1990 a 2023 (disminución de la dispersión inter-regional).

### 1.5 Fuera de alcance
- Inferencia **causal** (el diseño es observacional; solo se reportan asociaciones).
- Modelos de predicción a futuro / pronósticos.
- Datos subnacionales o por sexo/edad.
- Despliegue de un servicio web productivo (la entrega es analítica + almacén consultable).

---

## 2. Fuentes de datos (inventario verificado)

Los siguientes archivos fueron **inspeccionados** antes de redactar este contrato.

| # | Variable | Código / archivo | Fuente | Cobertura temporal | Rol |
|---|---|---|---|---|---|
| 1 | Esperanza de vida al nacer (años) | `SP.DYN.LE00.IN` | Banco Mundial (UN WPP, Eurostat) | 1960–2024 | **Variable objetivo (Y)** |
| 2 | Mortalidad infantil (por 1,000 nacidos vivos) | `SP.DYN.IMRT.IN` | Banco Mundial (UN IGME) | 1960–2024 | Objetivo secundario / validación |
| 3 | PIB per cápita, PPA (US$ internacionales constantes 2021) | `NY.GDP.PCAP.PP.KD` | Banco Mundial (ICP) | 1990–2025 | Predictor (ingreso) |
| 4 | Gasto corriente en salud (% del PIB) | `SH.XPD.CHEX.GD.ZS` | OMS – GHED | 2000–2024 | Predictor (gasto) |
| 5 | Gasto corriente en salud per cápita, PPA (US$ internacionales corrientes) | `SH.XPD.CHEX.PP.CD` | OMS – GHED | 2000–2024 | Predictor (gasto) |
| 6 | Años promedio de escolaridad (adultos ≥ 25, ambos sexos) | `average-years-of-schooling-among-adults.csv` | Our World in Data / PNUD-HDR 2025 | 1990–2023 | Predictor (educación) |

Archivos auxiliares: `Metadata_Country_*.csv` (región y grupo de ingreso) y `Metadata_Indicator_*.csv` (definiciones y fuentes).

### 2.1 Hallazgos del perfilado inicial (hechos medidos, no supuestos)

| Hallazgo | Valor | Implicación |
|---|---|---|
| Formato de WDI | **Ancho** (una columna por año), con 4 filas de encabezado previas | Requiere `skiprows=4` y `melt` a formato largo |
| Filas por archivo WDI | 266 entidades (217 países + **48 agregados**) × 66 años | Los agregados (`WLD`, `EUU`, `LIC`, …) **deben excluirse** del modelado; se usan sólo como referencia |
| Distinción país/agregado | `Region` vacía en `Metadata_Country` ⇒ agregado | Regla de filtrado reproducible |
| Completitud de esperanza de vida | ≈ 98 % | Variable base muy sólida |
| Completitud de mortalidad infantil | ≈ 77 % | Aceptable |
| Completitud de PIB per cápita PPA | ≈ 49 % (datos desde 1990) | Limita el periodo del panel |
| Completitud de gasto en salud | ≈ 33 % (datos desde 2000) | **Restricción dominante** del periodo de análisis |
| Escolaridad (OWID) | 6,760 filas · 215 entidades · 1990–2023 | **340 filas sin código ISO** ⇒ agregados regionales de OWID a excluir |
| Cobertura del panel unido (países reales) | 14,322 filas país-año; **2000–2022 completo: 4,157 filas, 186 países** | Tamaño efectivo para regresión múltiple |
| Corte transversal completo | 2019: 185 · 2021: 185 · 2022: 185 · 2023: 184 países | Años candidatos para modelos transversales |

### 2.2 Riesgos de integración conocidos

1. **Llave de unión:** unir **exclusivamente por código ISO-3** (`Country Code` ↔ `Code`), **nunca por nombre** (hay divergencias de nomenclatura entre WDI y OWID).
2. **Unidades monetarias distintas:** el PIB está en dólares *constantes 2021* y el gasto per cápita en dólares *corrientes*. No se mezclarán en una misma razón sin documentar la limitación.
3. **Multicolinealidad esperada** entre PIB per cápita y gasto en salud per cápita (se prueba con VIF).
4. **Ausencia no aleatoria:** los países de menor ingreso tienen más datos faltantes ⇒ riesgo de **sesgo de selección** en el análisis de casos completos.
5. **Años posteriores a 2023** carecen de escolaridad; el último año con las 6 variables es 2023.

---

## 3. Entregables

| ID | Entregable | Formato | Semana |
|---|---|---|---|
| **E1** | Protocolo del proyecto (plantilla institucional) | `.docx` / PDF | 1 |
| **E2** | Diccionario de datos y reporte de calidad (EDA inicial) | `.md` + notebook | 2 |
| **E3** | Dataset maestro limpio (`panel_salud_global.parquet` / `.csv`) | Parquet + CSV | 4–6 |
| **E4** | Notebook de correlación y modelado (OLS simple y múltiple, diagnósticos, residuos) | `.ipynb` | 2–3 y 6 |
| **E5** | Pipeline reproducible ETL (`etl/` + `Makefile`/script único) | Python | 6–7 |
| **E6** | **Almacén consultable** por país/año (SQLite o DuckDB) + consultas de ejemplo | `.db` + `.sql` | 6–7 |
| **E7** | Visualizaciones finales (dispersión log, series, regionales, convergencia) | PNG/SVG + notebook | 5 |
| **E8** | Informe final con conclusiones, limitaciones y recomendaciones | PDF / `.docx` | 7 |
| **E9** | Presentación de resultados | `.pptx` / PDF | 7 |

---

## 4. Plan de trabajo (7 semanas)

El cronograma respeta los retos técnicos fijados en el enunciado del proyecto.

| Semana | Fase CRISP-DM | Actividades | Reto técnico asociado | Hito de salida |
|:---:|---|---|---|---|
| **1** | Comprensión del negocio | Definir preguntas e hipótesis, protocolo, descarga y validación de datasets, estructura del repositorio | — | E1 aprobado; datos descargados con *checksum* |
| **2** | Comprensión de datos | Perfilado, diccionario, EDA univariado y bivariado, primeras correlaciones | Correlación ingreso–esperanza de vida | E2 |
| **3** | Comprensión de datos / Modelado | Correlación (Pearson, Spearman), regresión simple, comparación lineal vs. log | Regresión múltiple y análisis de residuos (inicio) | Modelo base (H1) |
| **4** | Preparación | Transformar a formato largo, filtrar agregados, estandarizar ISO-3, reglas de datos faltantes | Combinar CSV por país y año; manejar años faltantes y países con datos incompletos | Primer panel unificado |
| **5** | Preparación / Visualización | Dispersión con escala logarítmica, series temporales, comparativas regionales | Gráficos con escala log, series y comparativas | E7 |
| **6** | Modelado / Despliegue | Regresión múltiple final, residuos y "sobre-desempeño", validación, carga al almacén | Pipeline que une y carga indicadores a un almacén consultable | E3, E4, E6 (v1) |
| **7** | Evaluación / Entrega | Pruebas de robustez, informe, presentación, congelar versión | Cierre del pipeline | E5, E6, E8, E9 |

---

## 5. Metodología técnica

### 5.1 Arquitectura del pipeline

```
data/raw/            ← archivos originales (solo lectura, con hash SHA-256)
   └─ ETL
data/interim/        ← formato largo por indicador (country_iso3, year, value)
   └─ MERGE + QA
data/processed/      ← panel maestro (parquet/csv)
   └─ LOAD
warehouse/salud.db   ← SQLite/DuckDB (tablas dimensionales + hechos)
   └─ ANALYSIS
notebooks/ · reports/ · figures/
```

### 5.2 Estructura de repositorio

```
salud-global/
├── README.md
├── CONTRATO.md                 # este documento
├── environment.yml | requirements.txt
├── Makefile                    # make etl | make model | make figures | make all
├── data/{raw,interim,processed}/
├── etl/
│   ├── extract.py              # lectura de zips y verificación de integridad
│   ├── transform.py            # melt, filtros, estandarización
│   ├── merge.py                # unión por (iso3, year)
│   └── load.py                 # carga al almacén
├── notebooks/                  # 01_eda, 02_correlacion, 03_modelo, 04_residuos, 05_convergencia
├── src/                        # funciones reutilizables
├── tests/                      # pruebas de calidad de datos y del pipeline
├── warehouse/
├── reports/
└── figures/
```

### 5.3 Preparación de datos (reglas obligatorias)

1. **Lectura WDI:** `pd.read_csv(..., skiprows=4)`, descartar columnas vacías (`Unnamed: *`).
2. **Transformación a largo:** `melt` con llaves `Country Code`, `year`, `value`.
3. **Exclusión de agregados:** conservar solo códigos con `Region` no nula en `Metadata_Country`. En OWID, excluir filas con `Code` nulo.
4. **Unión:** *inner/left join* por `(iso3, year)`; la tabla base es esperanza de vida.
5. **Variable derivada:** `ln_gdp = ln(PIB per cápita PPA)`; `ln_che_pc = ln(gasto per cápita)`.
6. **Datos faltantes — política escalonada:**
   - **Nivel A (principal):** análisis de **casos completos** en el periodo común.
   - **Nivel B (sensibilidad):** imputación **dentro de país** limitada a huecos ≤ 2 años (interpolación lineal), sin extrapolar extremos.
   - **Nivel C (robustez):** imputación múltiple (MICE) y comparación de coeficientes.
   - Se **reportará la matriz de ausencia** por país, región y grupo de ingreso para documentar el sesgo.
7. **Valores atípicos:** no se eliminan por defecto; se marcan (`|z| > 3` o regla IQR) y se evalúa el impacto con/sin ellos.
8. **Trazabilidad:** cada transformación queda registrada en código; ningún dato se edita a mano.

### 5.4 Análisis exploratorio (EDA)
- Estadísticos descriptivos por variable, región y grupo de ingreso.
- Distribuciones (histogramas, KDE), asimetría; justificar transformación logarítmica.
- Mapa de calor de correlaciones (Pearson y Spearman).
- Dispersión `esperanza de vida` vs. `PIB` en escala **logarítmica** (curva tipo *Preston*).

### 5.5 Modelado estadístico

| Modelo | Especificación | Propósito |
|---|---|---|
| **M0** | `LE ~ GDP` | Línea base |
| **M1** | `LE ~ ln(GDP)` | Contrastar H1 (concavidad) |
| **M2** | `LE ~ ln(GDP) + ln(GastoSalud_pc)` | Aporte del gasto |
| **M3** | `LE ~ ln(GDP) + ln(GastoSalud_pc) + Escolaridad` | **Modelo principal** (H2) |
| **M4** | M3 + efectos fijos de región (y/o año) | Control de heterogeneidad |
| **M5** | Panel con efectos fijos de país y año (errores agrupados por país) | Robustez temporal |
| **M6** (opcional) | Random Forest / Gradient Boosting + importancia por permutación y SHAP | Chequeo de no linealidades (no sustituye a M3 para inferencia) |

**Diagnósticos obligatorios para modelos OLS:** VIF (< 5 deseable, < 10 máximo), Breusch–Pagan (heterocedasticidad; usar errores robustos HC3 si aplica), Shapiro–Wilk / QQ-plot de residuos, distancia de Cook y apalancamiento, RESET de Ramsey (forma funcional).

### 5.6 Identificación de países "sobre-desempeño"
1. Ajustar el modelo de **riqueza** (M1: solo ingreso).
2. Calcular el **residuo estandarizado** por país-año; promediar en una ventana reciente (p. ej., 2015–2023).
3. Definir **sobre-desempeño** = residuo medio ≥ +1 σ **y** presente en ≥ 70 % de los años de la ventana.
4. Verificar **robustez**: que el país siga en la lista con M2/M3 y con validación cruzada *leave-one-country-out*.
5. Perfilar los casos (región, gasto en salud, escolaridad, mortalidad infantil) para extraer **lecciones** (P2).

### 5.7 Desigualdad regional y convergencia (P3)
- Serie anual de media y desviación estándar de esperanza de vida por región (ponderación opcional por población, documentando que no se dispone de ella en los archivos y, de usarse, su fuente).
- **σ-convergencia:** evolución del coeficiente de variación entre países.
- **β-convergencia:** regresión `ΔLE ~ LE_inicial` por décadas.
- Visualización: líneas por región con bandas de dispersión y año de inflexión.

### 5.8 Almacén consultable (E6)

Esquema relacional propuesto (SQLite/DuckDB):

```sql
CREATE TABLE dim_pais (
  iso3 TEXT PRIMARY KEY, nombre TEXT, region TEXT, grupo_ingreso TEXT
);
CREATE TABLE dim_indicador (
  codigo TEXT PRIMARY KEY, nombre TEXT, unidad TEXT, fuente TEXT
);
CREATE TABLE hechos_indicador (
  iso3 TEXT REFERENCES dim_pais(iso3),
  anio INTEGER,
  codigo TEXT REFERENCES dim_indicador(codigo),
  valor REAL,
  PRIMARY KEY (iso3, anio, codigo)
);
CREATE VIEW v_panel AS  -- vista ancha por país/año para análisis
SELECT iso3, anio,
  MAX(CASE WHEN codigo='SP.DYN.LE00.IN'     THEN valor END) AS esperanza_vida,
  MAX(CASE WHEN codigo='SP.DYN.IMRT.IN'     THEN valor END) AS mortalidad_infantil,
  MAX(CASE WHEN codigo='NY.GDP.PCAP.PP.KD'  THEN valor END) AS pib_pc_ppa,
  MAX(CASE WHEN codigo='SH.XPD.CHEX.GD.ZS'  THEN valor END) AS gasto_salud_pib,
  MAX(CASE WHEN codigo='SH.XPD.CHEX.PP.CD'  THEN valor END) AS gasto_salud_pc,
  MAX(CASE WHEN codigo='SCHOOLING'          THEN valor END) AS escolaridad
FROM hechos_indicador GROUP BY iso3, anio;
```

---

## 6. Métricas de éxito y criterios de aceptación

| ID | Criterio | Umbral de aceptación | Evidencia |
|---|---|---|---|
| **A1** | Modelo de regresión que cuantifica el efecto del ingreso y el gasto en salud sobre la esperanza de vida | M3 reportado con coeficientes, IC 95 %, R² ajustado y diagnósticos completos | E4 |
| **A2** | Mejora del ajuste log vs. lineal | ΔR² ajustado positivo y RESET aprobado en M1 | E4 |
| **A3** | Identificación **justificada** de países de sobre-desempeño | Lista con residuos, criterio explícito y chequeo de robustez (§5.6) | E4, E8 |
| **A4** | Visualización temporal que cuente la historia de convergencia/divergencia | Figura regional 1990–2023 con σ-convergencia calculada | E7 |
| **A5** | Pipeline reproducible | `make all` regenera dataset, almacén, modelos y figuras desde `data/raw` sin intervención manual | E5 |
| **A6** | Almacén consultable | Al menos 5 consultas SQL documentadas devuelven resultados correctos por país/año | E6 |
| **A7** | Calidad de datos | 0 duplicados en `(iso3, año)`; 0 agregados en el panel; rangos válidos (ej. `0 < LE < 100`) | `tests/` |

---

## 7. Gestión de calidad de datos

### 7.1 Pruebas automáticas (mínimas)
- Unicidad de la llave `(iso3, año)`.
- Todo `iso3` del panel existe en `dim_pais` con región asignada.
- Rangos plausibles: esperanza de vida (20–95), mortalidad infantil (≥ 0), gasto en salud (% PIB) (0–40), escolaridad (0–20), PIB per cápita (> 0).
- Conteo de filas por etapa (extracción → largo → unido → modelo) con **reporte de pérdidas**.
- Consistencia cruzada: mortalidad infantil y esperanza de vida correlacionadas negativamente.

### 7.2 Reproducibilidad
- Semillas fijas (`random_state=42`).
- Versionado de dependencias (`requirements.txt` con versiones).
- *Hash* SHA-256 de cada archivo crudo registrado en `data/raw/MANIFEST.md`.
- Control de versiones con **Git**; ramas por entregable; *commits* descriptivos.

---

## 8. Riesgos y mitigación

| ID | Riesgo | Prob. | Impacto | Mitigación |
|---|---|:---:|:---:|---|
| R1 | Escasez de datos de gasto en salud (solo desde 2000, ~33 % completo) | Alta | Alto | Periodo 2000–2023; reportar cobertura; análisis de sensibilidad con y sin gasto |
| R2 | Sesgo de selección por ausencia no aleatoria | Media | Alto | Matriz de ausencia por grupo de ingreso; comparación de muestra completa vs. total |
| R3 | Multicolinealidad PIB–gasto | Alta | Medio | VIF; modelos escalonados M1→M3; regularización (Ridge/Lasso) como contraste |
| R4 | Confusión entre asociación y causalidad | Media | Alto | Lenguaje cuidadoso; sección de limitaciones; sin afirmaciones causales |
| R5 | Falla de unión por códigos/nombres | Media | Medio | Unión solo por ISO-3; prueba de países huérfanos |
| R6 | Mezcla de unidades monetarias (constantes vs. corrientes) | Media | Medio | No combinar sin documentar; escoger un solo indicador de gasto por modelo |
| R7 | Concentración de carga en pocas semanas | Media | Medio | Hitos semanales y revisión cruzada entre integrantes |
| R8 | Dependencia de datos externos que cambian | Baja | Medio | Copia local inmutable de datos crudos + manifiesto con fecha |

---

## 9. Roles y responsabilidades

> Asignación sugerida; el equipo puede reasignarla de común acuerdo.

| Rol | Responsable | Responsabilidades principales |
|---|---|---|
| **Líder de proyecto / Integración** | *por definir* | Cronograma, repositorio, informe final, revisión de entregables |
| **Ingeniería de datos (ETL / almacén)** | *por definir* | `etl/`, pruebas de calidad, almacén (E3, E5, E6) |
| **Análisis y modelado** | *por definir* | EDA, regresión, residuos, convergencia (E2, E4) |
| **Visualización y comunicación** | *por definir* | Figuras, presentación, redacción (E7, E9) |

Toda pieza de código o análisis debe ser **revisada por al menos un integrante distinto del autor** antes de integrarse.

---

## 10. Convenciones técnicas

- **Lenguaje:** Python ≥ 3.10.
- **Librerías base:** `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`/`seaborn` (o `plotly`), `pyarrow`, `duckdb`/`sqlite3`, `pytest`.
- **Estilo:** PEP 8; funciones con *docstrings*; notebooks ejecutables de arriba abajo sin errores.
- **Nomenclatura de datos:** `snake_case`; llaves `iso3`, `anio`.
- **Gráficos:** títulos descriptivos, ejes con unidades, escala logarítmica rotulada, fuente citada al pie, paleta apta para daltonismo.
- **Idioma:** documentación y reportes en español; código y nombres de columnas técnicas en inglés/ISO cuando provenga de la fuente.

---

## 11. Gobernanza, ética y citación

- Se emplean **datos abiertos agregados a nivel país**; no se manejan datos personales.
- Citar siempre: Banco Mundial (WDI), OMS (GHED), UN IGME, UN WPP, PNUD (HDR 2025) vía Our World in Data.
- Declarar limitaciones: la escolaridad no mide **calidad** educativa; los promedios nacionales ocultan desigualdades internas; las estimaciones de países con baja capacidad estadística tienen mayor incertidumbre.
- Los resultados se presentarán como **asociaciones**, evitando juicios de valor sobre países.

---

## 12. Control de cambios

Todo cambio al alcance, hipótesis, métricas o cronograma requiere:
1. Registro en la tabla inferior con fecha y motivo.
2. Aprobación de la mayoría simple del equipo.
3. Notificación al docente si afecta entregables.

| Versión | Fecha | Cambio | Autor |
|:---:|---|---|---|
| 1.0 | 2026-10-26 | Versión inicial del contrato | Equipo 4 |

---

## 13. Aceptación

Con la firma de este documento, los integrantes se comprometen a cumplir lo aquí establecido.

| Nombre | Rol | Firma | Fecha |
|---|---|---|---|
| Angel David Munguia Zuñiga | | | |
| Luis Alberto Reyes Estrada | | | |
| Gabriel Isaac Marquez Romo | | | |

---

### Anexo A — Definiciones de indicadores

| Código | Definición oficial resumida |
|---|---|
| `SP.DYN.LE00.IN` | Años que viviría un recién nacido si los patrones de mortalidad actuales se mantuvieran toda su vida. |
| `SP.DYN.IMRT.IN` | Número de menores de un año fallecidos por cada 1,000 nacidos vivos en un año dado. |
| `NY.GDP.PCAP.PP.KD` | PIB por persona, convertido con paridad de poder adquisitivo, en dólares internacionales constantes de 2021. |
| `SH.XPD.CHEX.GD.ZS` | Gasto corriente en salud como porcentaje del PIB (excluye gasto de capital). |
| `SH.XPD.CHEX.PP.CD` | Gasto corriente en salud por persona, en dólares internacionales PPA corrientes. |
| Escolaridad (OWID/PNUD) | Años promedio de educación formal de adultos ≥ 25 (excluye años repetidos). |

### Anexo B — Lista de verificación previa a la entrega

- [ ] `make all` corre de principio a fin en un entorno limpio.
- [ ] Todas las pruebas de `tests/` pasan.
- [ ] El panel no contiene agregados ni duplicados.
- [ ] Cada figura cita fuente, unidades y periodo.
- [ ] Todos los coeficientes del informe coinciden con el notebook.
- [ ] Limitaciones y alcance (no causalidad) declarados en el informe.
- [ ] Citas de las fuentes completas.
- [ ] Revisión cruzada firmada por un integrante distinto del autor.

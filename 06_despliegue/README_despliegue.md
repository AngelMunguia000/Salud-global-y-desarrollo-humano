# 06_despliegue — Aplicación web (Streamlit)

**App publicada:** https://salud-global-equipo4.streamlit.app (rama `feature/despliegue-streamlit`).

Aplicación interactiva con **una vista por fase del proyecto** (Minería → Ingeniería → Análisis → Ciencia de
datos → MLOps). Cada gráfica incluye una caja **"¿Por qué?"** que justifica el dato, la variable o el método.

La app **solo lee resultados ya generados** (`make all`): no entrena modelos ni modifica datos. Así las cifras
coinciden con `reports/informe_final.md` y la app carga rápido en la nube.

## Estructura del código

```
06_despliegue/
├── app.py              punto de entrada: menú y navegación entre vistas
├── components.py       componentes visuales reutilizables (encabezado, caja "¿Por qué?", figuras)
├── services/
│   └── pipeline.py     capa de datos: carga de resultados con caché (st.cache_data)
├── views/              una vista por fase; cada módulo expone render()
│   ├── home.py         inicio: pregunta, cifras clave y respuesta corta
│   ├── mineria.py      fuentes, justificación y cobertura
│   ├── ingenieria.py   pipeline ETL, decisiones, panel y almacén DuckDB
│   ├── analisis.py     explorador interactivo, log vs. niveles, correlaciones, convergencia
│   ├── ciencia.py      modelos M0–M6, validación, sobre-desempeño y conclusiones
│   └── mlops.py        reproducibilidad, hashes SHA-256, pruebas, monitoreo y despliegue
└── requirements.txt    dependencias mínimas para Streamlit Cloud
```

Las vistas no leen archivos directamente: todo pasa por `services/pipeline.py`, así la interfaz y los datos quedan
separados.

## Despliegue en local

Requisitos: Python 3.10 o superior. Desde la raíz del repositorio:

```bash
pip install -r 06_despliegue/requirements.txt
python -m streamlit run 06_despliegue/app.py      # o: make app
```

Se abre en http://localhost:8501 (detener con Ctrl+C). Para otro puerto: `--server.port 8502`.
Prueba automática: `python -m pytest tests/test_app.py`.

## Vistas y criterio de la rúbrica que respaldan

| Vista | Criterio | Contenido |
|---|---|---|
| Inicio | 6. Comunicación | Pregunta central, preguntas de investigación, cifras clave, respuesta corta |
| 1 · Minería | 1. Justificación de los datos (25) | Fuentes, periodo 2000–2023, cobertura por región |
| 2 · Ingeniería | 2. Justificación del análisis (25) | Pipeline ETL, decisiones con su razón y alternativa descartada, almacén |
| 3 · Análisis | 2 y 3. Calidad del análisis (20) | Explorador interactivo, log vs. niveles, correlaciones, convergencia |
| 4 · Ciencia de datos | 3 y 4. Hallazgos y conclusiones (35) | Modelos, validación, sobre-desempeño, hipótesis, recomendación, limitaciones |
| 5 · MLOps | — | Pipeline reproducible, versionado de datos, pruebas, monitoreo y despliegue |

## Datos que usa

| Archivo | Vista |
|---|---|
| `03_data/processed/panel_salud_global.parquet` (vía `common/panel.py`) | Ingeniería, Análisis |
| `03_data/processed/source_hashes.json` | MLOps |
| `04_analisis/tablas/*.csv`, `resultados_eda.json` | Inicio, Minería, Análisis |
| `05_ciencia/resultados/*.csv`, `resumen_modelos.json` | Inicio, Ciencia de datos, MLOps |
| `reports/figuras/*.png` | Análisis, Ciencia de datos |

Si se regeneran los resultados (`make all`), la app muestra las cifras nuevas sin cambiar código.

## Despliegue en Streamlit Community Cloud

Requisito: el código debe estar en GitHub (rama `feature/despliegue-streamlit` o `main`) y la cuenta que despliega
debe ser **administradora** del repositorio `AngelMunguia000/Salud-global-y-desarrollo-humano` (en repos personales,
solo el dueño lo es; los colaboradores no pueden desplegar). El tema claro se fija en `.streamlit/config.toml`.

1. Entrar a https://share.streamlit.io e iniciar sesión con GitHub.
2. **Create app → Deploy a public app from GitHub**.
3. Llenar:
   - **Repository:** `AngelMunguia000/Salud-global-y-desarrollo-humano`
   - **Branch:** `feature/despliegue-streamlit` (o `main` después del merge)
   - **Main file path:** `06_despliegue/app.py`
   - **App URL:** `salud-global-equipo4`
4. En **Advanced settings**, elegir Python 3.10 o superior.
5. **Deploy**. Streamlit Cloud instala `06_despliegue/requirements.txt` (el de la carpeta de la app tiene
   prioridad sobre el de la raíz) y publica la app.
6. Copiar la URL pública al README principal.

Cada push a la rama configurada vuelve a desplegar la app automáticamente.

### Problemas comunes
- **`ModuleNotFoundError: common`**: la app agrega la raíz del repo al `sys.path`; verificar que `common/` esté en GitHub.
- **`FileNotFoundError` de un CSV o PNG**: faltan resultados en el repositorio; ejecutar `make all` y subir
  `04_analisis/tablas/`, `05_ciencia/resultados/` y `reports/figuras/`.
- **La app tarda en abrir**: las apps gratuitas se duermen sin uso; el primer acceso la despierta (≈ 30 s).

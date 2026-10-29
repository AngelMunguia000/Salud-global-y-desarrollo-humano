# 06_despliegue — Aplicación web (Streamlit)

Aplicación interactiva que presenta el proyecto siguiendo los cinco momentos de la rúbrica de presentación.
Cada gráfica incluye una caja **"¿Por qué?"** que justifica el dato, la variable o el método, porque los
criterios 1 y 2 de la rúbrica (50 puntos) dependen de esa justificación.

La app **solo lee resultados ya generados** (`make all`): no entrena modelos ni modifica datos. Así las cifras
coinciden con `reports/informe_final.md` y la app carga rápido en la nube.

## Ejecutar en local
Desde la raíz del repositorio:

```bash
pip install -r 06_despliegue/requirements.txt
streamlit run 06_despliegue/app.py      # o: make app
```

Se abre en http://localhost:8501. Prueba automática: `python -m pytest tests/test_app.py`.

## Páginas y criterio de la rúbrica que respaldan

| Página | Momento (min) | Criterio | Contenido |
|---|---|---|---|
| 1 · Problema y pregunta | 0–3 | 6. Comunicación | Pregunta central, preguntas de investigación, cifras clave |
| 2 · Los datos | 3–6 | 1. Justificación de los datos (25) | Fuentes, periodo 2000–2023, cobertura por región |
| 3 · Preparación | 6–10 | 2. Justificación del análisis (25) | Decisiones del ETL con su razón y alternativa descartada; R² niveles vs. logaritmo |
| 4 · Análisis y hallazgos | 9–16 | 2 y 3. Calidad del análisis (20) | Explorador interactivo, modelos M0–M6, validación, países de sobre-desempeño, convergencia |
| 5 · Conclusiones | 17–20 | 4. Conclusiones y limitaciones (15) | Matriz de hipótesis, recomendación accionable, limitaciones |
| Preguntas | — | 5. Respuesta a preguntas (10) | Banco de preguntas para practicar la defensa |

## Datos que usa

| Archivo | Página |
|---|---|
| `03_data/processed/panel_salud_global.parquet` (vía `common/panel.py`) | Explorador |
| `04_analisis/tablas/*.csv`, `resultados_eda.json` | Datos, Preparación, Convergencia |
| `05_ciencia/resultados/*.csv`, `resumen_modelos.json` | Modelos, Sobre-desempeño, Conclusiones |
| `reports/figuras/*.png` | Figuras estáticas del informe |

Si se regeneran los resultados (`make all`), la app muestra las cifras nuevas sin cambiar código.

## Despliegue en Streamlit Community Cloud

Requisito: el código debe estar en GitHub (rama `feature/despliegue-streamlit` o `main`) y la cuenta que despliega
debe tener acceso al repositorio `GabrielIMarquezRp/Salud-global-y-desarrollo-humano`.

1. Entrar a https://share.streamlit.io e iniciar sesión con GitHub.
2. **Create app → Deploy a public app from GitHub**.
3. Llenar:
   - **Repository:** `GabrielIMarquezRp/Salud-global-y-desarrollo-humano`
   - **Branch:** `feature/despliegue-streamlit` (o `main` después del merge)
   - **Main file path:** `06_despliegue/app.py`
   - **App URL:** por ejemplo `salud-global-equipo4`
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

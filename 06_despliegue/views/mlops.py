"""Fase 5 · MLOps: reproducibilidad, versionado de datos, pruebas, validación y despliegue."""
import pandas as pd
import streamlit as st

from components import encabezado, por_que
from services.pipeline import RESULTADOS, conteo_pruebas, csv, hashes


def render() -> None:
    encabezado("Fase 5 · MLOps", "Operación del proyecto",
               "Cómo garantizamos que los resultados se puedan reproducir, probar y desplegar.")
    t1, t2, t3, t4, t5 = st.tabs(["Pipeline", "Versionado de datos", "Pruebas", "Monitoreo del modelo", "Despliegue"])

    with t1:
        st.table(pd.DataFrame([
            ("make etl", "Ingeniería: panel + almacén DuckDB"),
            ("make analisis", "Tablas y figuras del EDA"),
            ("make modelos", "Modelos M0–M6, residuos e hipótesis"),
            ("make informe", "Informe .md/.docx y presentación"),
            ("make test", "Pruebas automáticas"),
            ("make app", "Esta aplicación en local"),
            ("make all", "Todo, de los datos originales al informe"),
        ], columns=["Comando", "Qué hace"]))
        por_que(
            "Un solo comando (`make all`) regenera todo **sin pasos manuales** y con semilla fija (`random_state=42`): "
            "cualquiera obtiene las mismas cifras."
        )

    with t2:
        h = hashes()
        st.metric("Archivos originales verificados", len(h))
        st.dataframe(h, hide_index=True, width="stretch")
        por_que(
            "El ETL calcula el **SHA-256** de cada archivo original. Si una fuente cambia, el hash cambia: "
            "así detectamos datos distintos antes de que alteren los resultados."
        )

    with t3:
        pruebas = conteo_pruebas()
        st.metric("Funciones de prueba (pytest)", int(pruebas["pruebas"].sum()))
        st.dataframe(pruebas, hide_index=True, width="stretch")
        st.caption("Algunas pruebas están parametrizadas, por lo que pytest ejecuta más casos que funciones.")
        por_que(
            "Las pruebas cubren las reglas de calidad del ETL (llave única, sin agregados, rango 20–95 años), "
            "el núcleo OLS contra scikit-learn, los modelos, los entregables y que cada vista de esta app cargue sin errores."
        )

    with t4:
        val = csv(RESULTADOS, "validacion_fuera_de_muestra.csv")
        st.dataframe(val.round(3), hide_index=True, width="stretch")
        por_que(
            "Las métricas fuera de muestra (MAE, RMSE, R²) son la línea base del modelo: si al actualizar los datos "
            "el error temporal sube de forma clara, el modelo debe re-entrenarse o revisarse."
        )

    with t5:
        st.table(pd.DataFrame([
            ("Plataforma", "Streamlit Community Cloud"),
            ("URL", "salud-global-equipo4.streamlit.app"),
            ("Repositorio", "AngelMunguia000/Salud-global-y-desarrollo-humano"),
            ("Rama", "feature/despliegue-streamlit"),
            ("Archivo principal", "06_despliegue/app.py"),
            ("Dependencias", "06_despliegue/requirements.txt"),
            ("Actualización", "Automática con cada push a la rama"),
            ("En local", "streamlit run 06_despliegue/app.py → http://localhost:8501"),
        ], columns=["Parámetro", "Valor"]))
        por_que(
            "La app **solo lee** resultados ya generados: no entrena en la nube, carga rápido y muestra exactamente "
            "las mismas cifras que el informe."
        )

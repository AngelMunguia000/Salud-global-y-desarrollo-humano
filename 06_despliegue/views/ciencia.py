"""Fase 4 · Ciencia de datos: modelos, validación, sobre-desempeño (P2) y conclusiones."""
import plotly.express as px
import streamlit as st

from common.panel import RECENT_WINDOW
from common.style import REGIONES_ES
from components import encabezado, figura, por_que
from services.pipeline import RESULTADOS, csv


def render() -> None:
    encabezado("Fase 4 · Ciencia de datos", "Modelos y conclusiones",
               "Regresión con errores agrupados por país, validación fuera de muestra y análisis de residuos.")
    t1, t2, t3, t4 = st.tabs(["Modelos", "Validación", "P2 · Sobre-desempeño", "Conclusiones"])

    with t1:
        ajuste = csv(RESULTADOS, "modelos_ajuste_diagnosticos.csv")
        st.dataframe(ajuste[["modelo", "descripcion", "r2_ajustado", "rmse"]].round(3)
                     .rename(columns={"descripcion": "Especificación", "r2_ajustado": "R² ajustado", "rmse": "RMSE (años)"}),
                     hide_index=True, width="stretch")
        por_que(
            "Construimos los modelos **de menor a mayor** (M0 → M5) para ver qué aporta cada variable. "
            "M3 es el principal; M4 y M5 agregan efectos fijos para comprobar si el resultado sobrevive "
            "a diferencias no observadas entre regiones, países y años."
        )
        figura("02_coeficientes_m3_m4_m5.png", "Coeficientes con IC 95 % (errores agrupados por país)")
        st.markdown(
            "**Hallazgo:** duplicar el PIB per cápita se asocia con **+4.2 años** de esperanza de vida. "
            "Gasto en salud y escolaridad aportan, pero de forma **frágil**: con efectos fijos de país solo el ingreso sigue siendo significativo."
        )
        vif = csv(RESULTADOS, "vif_m3.csv")
        st.caption("VIF de M3: " + ", ".join(f"{v} = {x:.1f}" for v, x in zip(vif["variable"], vif["vif"]))
                   + " → colinealidad alta entre PIB y gasto, por eso los coeficientes individuales son inestables.")
        figura("01_diagnosticos_m3.png", "Diagnósticos de residuos del modelo M3")

    with t2:
        val = csv(RESULTADOS, "validacion_fuera_de_muestra.csv")
        st.plotly_chart(px.bar(val, x="modelo", y="rmse", color="esquema", barmode="group",
                               labels={"rmse": "RMSE (años, menor es mejor)", "modelo": "Modelo", "esquema": "Esquema"}),
                        width="stretch")
        st.dataframe(val.round(3), hide_index=True, width="stretch")
        por_que(
            "Dos esquemas responden dos usos distintos: **temporal** (¿sirve para predecir el futuro?) y "
            "**países no vistos** (¿sirve para países sin datos?). El gradient boosting (M6) es solo un *benchmark*: "
            "que gane indica no linealidades que el modelo lineal no captura."
        )

    with t3:
        robustos = csv(RESULTADOS, "paises_sobre_desempeno.csv").query("robusto")
        perfil = csv(RESULTADOS, "perfil_sobre_desempeno.csv")
        tabla = robustos[["iso3", "pais", "region", "z_medio_M1", "residuo_medio_M1"]].merge(
            perfil[["iso3", "esperanza_vida", "pib_per_capita_ppp", "gasto_salud_per_capita_ppp"]], on="iso3")
        tabla["region"] = tabla["region"].map(REGIONES_ES)
        st.dataframe(tabla.drop(columns="iso3").round(2).rename(columns={
            "pais": "País", "region": "Región", "z_medio_M1": "z medio", "residuo_medio_M1": "Años sobre lo esperado",
            "esperanza_vida": "Esp. vida", "pib_per_capita_ppp": "PIB pc (US$)", "gasto_salud_per_capita_ppp": "Gasto salud pc (US$)"}),
            hide_index=True, width="stretch")
        por_que(
            f"Criterio: residuo medio **≥ +1σ** y positivo en **≥ 70 % de los años** ({RECENT_WINDOW[0]}–{RECENT_WINDOW[1]}). "
            "Así filtramos el ruido y exigimos que el país supere lo esperado **de forma persistente**, no un año suelto. "
            "Un país es *robusto* si además cumple con el modelo M3 y al excluir un país a la vez (leave-one-country-out)."
        )
        figura("04_sobre_desempeno_dispersion.png", "Países con sobre-desempeño resaltados sobre la curva ingreso–esperanza de vida")
        st.warning("Son economías pequeñas: sus estimaciones son más ruidosas. Los datos **no identifican causas**.")

    with t4:
        hip = csv(RESULTADOS, "hipotesis.csv")
        st.dataframe(hip.rename(columns={"hipotesis": "ID", "enunciado": "Hipótesis", "veredicto": "Veredicto", "evidencia": "Evidencia"}),
                     hide_index=True, width="stretch")
        st.success(
            "**Recomendación:** los tomadores de decisión no deberían enfocarse solo en el crecimiento del PIB. "
            "Proponemos estudiar las políticas de **atención primaria** de países como **Cabo Verde, Jordania o Albania**, "
            "que alcanzan alta esperanza de vida con recursos moderados, incorporando datos de cobertura de salud y vacunación (OMS-GHO)."
        )
        st.subheader("Limitaciones")
        st.markdown(
            "- **Observacional:** asociaciones, no causalidad.\n"
            "- **Cobertura desigual** del gasto en salud por región; no se imputaron faltantes.\n"
            "- **Colinealidad** PIB–gasto (VIF ≈ 8–9).\n"
            "- PIB en dólares constantes y gasto en corrientes: no se combinaron en razones.\n"
            "- Esperanza de vida **modelada** (UN WPP) en varios países; la escolaridad no mide calidad.\n"
            "- Medias regionales **sin ponderar** por población.\n"
            "- El umbral de sobre-desempeño (+1σ, 70 %) es una **convención** del equipo."
        )

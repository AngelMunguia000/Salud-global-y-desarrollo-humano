"""Pruebas de las fases de análisis, ciencia de datos, informe y consultas SQL."""
from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from common.panel import ROOT, WINDOW, add_derived, load_panel

modelos = importlib.import_module("05_ciencia.scripts.modelos")
eda = importlib.import_module("04_analisis.scripts.eda_completo")
consultas = importlib.import_module("02_ingenieria.etl.consultas")

RES = ROOT / "05_ciencia" / "resultados"
TABLAS = ROOT / "04_analisis" / "tablas"


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return add_derived(load_panel())


@pytest.fixture(scope="module")
def muestra(panel) -> pd.DataFrame:
    return modelos.muestra_modelo(panel)


# ---- panel y modelos -------------------------------------------------------- #
def test_muestra_modelo_es_completa_y_en_ventana(muestra):
    cols = ["esperanza_vida", "ln_pib", "ln_gasto_pc", "escolaridad_promedio"]
    assert muestra[cols].notna().all().all()
    assert muestra["anio"].between(*WINDOW).all()
    assert not muestra.duplicated(["iso3", "anio"]).any()


def test_m3_signos_y_ajuste_razonables(muestra):
    res = modelos.ajustar(muestra, modelos.MODELOS["M3"])
    coef = dict(zip(res.names, res.coef))
    assert coef["ln_pib"] > 0 and coef["ln_gasto_pc"] > 0
    assert 0.5 < res.r2 < 1.0


def test_log_supera_a_niveles(muestra):
    m0 = modelos.ajustar(muestra, modelos.MODELOS["M0"], cov="classic")
    m1 = modelos.ajustar(muestra, modelos.MODELOS["M1"], cov="classic")
    assert m1.adj_r2 > m0.adj_r2


def test_efectos_fijos_de_pais_aumentan_el_ajuste(muestra):
    m3 = modelos.ajustar(muestra, modelos.MODELOS["M3"], cov="classic")
    m5 = modelos.ajustar(muestra, modelos.MODELOS["M5"], cov="classic")
    assert m5.r2 > m3.r2


def test_criterio_sobre_desempeno_con_datos_sinteticos():
    rows = []
    for anio in range(2015, 2024):
        rows += [("AAA", "Alfa", "R", anio, 5.0, 1.5), ("BBB", "Beta", "R", anio, 5.0, 1.5),
                 ("CCC", "Gamma", "R", anio, -5.0, -1.5),
                 ("DDD", "Delta", "R", anio, 5.0 if anio % 2 else -1.0, 1.5 if anio % 2 else -0.2)]
    rz = pd.DataFrame(rows, columns=["iso3", "pais", "region", "anio", "residuo", "z"])
    ev = modelos.evaluar_paises(rz).set_index("iso3")
    assert ev.loc["AAA", "pasa_criterio"] and ev.loc["BBB", "pasa_criterio"]
    assert not ev.loc["CCC", "pasa_criterio"]
    assert not ev.loc["DDD", "pasa_criterio"]          # positivo solo ~56 % de los años


def test_residuos_de_m1_con_efectos_de_anio_tienen_media_cero(panel):
    res, d = modelos.modelo_riqueza_m1(panel)
    assert abs(res.resid.mean()) < 1e-8
    assert len(res.resid) == len(d)


def test_validacion_devuelve_metricas_validas(muestra):
    val = modelos.validacion(muestra)
    assert {"mae", "rmse", "r2"} <= set(val.columns)
    assert (val["rmse"] > 0).all() and (val["r2"] < 1).all()
    assert val["esquema"].str.contains("temporal").any()
    assert val["esquema"].str.contains("países no vistos").any()


# ---- EDA -------------------------------------------------------------------- #
def test_sigma_convergencia_decrece(panel):
    sig = eda.convergencia_sigma(panel)
    assert sig.loc[2023, "desv_est"] < sig.loc[1960, "desv_est"]


def test_beta_convergencia_negativo(panel):
    b = eda.convergencia_beta(panel, 1990, 2023)
    assert b["beta"] < 0 and b["p_valor"] < 0.05


def test_cobertura_en_rango(panel):
    cob = eda.cobertura(panel)
    assert ((cob >= 0) & (cob <= 1)).all().all()
    assert (cob["esperanza_vida"] == 1).all()


# ---- consultas SQL ---------------------------------------------------------- #
def test_consultas_ejemplo_son_al_menos_cinco():
    queries = consultas.split_queries(consultas.SQL_PATH.read_text(encoding="utf-8"))
    assert len(queries) >= 5
    assert all(q.lstrip().upper().startswith("SELECT") for _, q in queries)


# ---- artefactos generados (requieren `make analisis modelos informe`) ------- #
def _requiere(path: Path) -> Path:
    if not path.is_file():
        pytest.skip(f"Falta {path.name}: ejecuta `make all`.")
    return path


def test_hipotesis_tiene_h1_a_h4():
    hip = pd.read_csv(_requiere(RES / "hipotesis.csv"))
    assert list(hip["hipotesis"]) == ["H1", "H2", "H3", "H4"]
    assert hip["veredicto"].isin(["Respaldada", "Parcialmente respaldada", "No respaldada"]).all()


def test_sobre_desempeno_robusto_cumple_todas_las_pruebas():
    t = pd.read_csv(_requiere(RES / "paises_sobre_desempeno.csv"))
    rob = t[t["robusto"]]
    assert len(rob) > 0
    assert rob[["pasa_M1", "pasa_M3", "pasa_loco"]].all().all()
    assert (rob["z_medio_M1"] >= 1.0).all() and (rob["pct_positivo_M1"] >= 0.7).all()


def test_resultados_eda_json_consistente():
    data = json.loads(_requiere(TABLAS / "resultados_eda.json").read_text(encoding="utf-8"))
    assert data["sigma_2023"] < data["sigma_1990"]
    assert data["r2_log_mayor_en_anios"] == data["anios_evaluados"]


def test_informe_sin_marcas_sin_resolver():
    text = _requiere(ROOT / "reports" / "informe_final.md").read_text(encoding="utf-8")
    assert not re.search(r"\{[a-z_]+[\[\(']", text), "hay expresiones sin evaluar"
    assert "nan" not in re.findall(r"\b\w+\b", text.lower())
    for h in ("H1", "H2", "H3", "H4"):
        assert h in text
    figs = re.findall(r"!\[.*?\]\((figuras/[^)]+)\)", text)
    assert figs and all((ROOT / "reports" / f).is_file() for f in figs)


def test_entregables_finales_existen():
    for name in ("informe_final.docx", "presentacion_final.pptx"):
        assert _requiere(ROOT / "reports" / name).stat().st_size > 10_000

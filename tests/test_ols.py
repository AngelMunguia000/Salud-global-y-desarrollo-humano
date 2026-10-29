"""Pruebas del núcleo OLS contra implementaciones independientes."""
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

from common.ols import (breusch_pagan, cooks_distance, design_matrix, fit_ols,
                        reset_test, vif)


@pytest.fixture
def data():
    rng = np.random.default_rng(0)
    n = 300
    x1, x2 = rng.normal(size=n), rng.normal(size=n)
    y = 1.5 + 2.0 * x1 - 0.7 * x2 + rng.normal(scale=1 + abs(x1), size=n)
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2, "g": rng.integers(0, 30, n)})


def test_coeficientes_coinciden_con_sklearn(data):
    X, names = design_matrix(data, ["x1", "x2"])
    res = fit_ols(X, data["y"].to_numpy(), names, "classic")
    lr = LinearRegression().fit(data[["x1", "x2"]], data["y"])
    assert np.allclose(res.coef[1:], lr.coef_)
    assert np.isclose(res.coef[0], lr.intercept_)
    assert np.isclose(res.r2, lr.score(data[["x1", "x2"]], data["y"]))


def test_hc3_coincide_con_formula_explicita(data):
    X, names = design_matrix(data, ["x1", "x2"])
    y = data["y"].to_numpy()
    res = fit_ols(X, y, names, "HC3")
    inv = np.linalg.inv(X.T @ X)
    h = np.diag(X @ inv @ X.T)
    e = y - X @ (inv @ X.T @ y)
    meat = sum((e[i] / (1 - h[i])) ** 2 * np.outer(X[i], X[i]) for i in range(len(y)))
    assert np.allclose(res.cov, inv @ meat @ inv)


def test_ajuste_perfecto_da_r2_uno():
    x = np.arange(20.0)
    X, names = design_matrix(pd.DataFrame({"x": x}), ["x"])
    res = fit_ols(X, 3 + 2 * x, names, "classic")
    assert np.isclose(res.r2, 1.0)


def test_cluster_requiere_grupos(data):
    X, names = design_matrix(data, ["x1"])
    with pytest.raises(ValueError):
        fit_ols(X, data["y"].to_numpy(), names, "cluster")
    res = fit_ols(X, data["y"].to_numpy(), names, "cluster", groups=data["g"].to_numpy())
    assert res.df_resid == data["g"].nunique() - 1


def test_vif_alto_con_colinealidad(data):
    data = data.assign(x3=data["x1"] * 0.98 + 0.02 * data["x2"])
    assert vif(data, ["x1", "x3"])["vif"].min() > 10
    assert vif(data, ["x1", "x2"])["vif"].max() < 1.5


def test_breusch_pagan_detecta_heterocedasticidad():
    rng = np.random.default_rng(2)
    x = rng.uniform(0.1, 5, 500)
    y = 1 + 2 * x + rng.normal(scale=x, size=500)  # varianza crece con x
    X, names = design_matrix(pd.DataFrame({"x": x}), ["x"])
    assert breusch_pagan(fit_ols(X, y, names, "classic"))[1] < 0.01


def test_breusch_pagan_no_rechaza_homocedasticidad():
    rng = np.random.default_rng(3)
    x = rng.uniform(0.1, 5, 500)
    y = 1 + 2 * x + rng.normal(size=500)
    X, names = design_matrix(pd.DataFrame({"x": x}), ["x"])
    assert breusch_pagan(fit_ols(X, y, names, "classic"))[1] > 0.01


def test_reset_detecta_no_linealidad():
    rng = np.random.default_rng(1)
    x = rng.uniform(0, 3, 400)
    y = np.exp(x) + rng.normal(scale=0.2, size=400)
    X, names = design_matrix(pd.DataFrame({"x": x}), ["x"])
    assert reset_test(fit_ols(X, y, names, "classic"))[1] < 0.01


def test_cook_no_negativa(data):
    X, names = design_matrix(data, ["x1"])
    res = fit_ols(X, data["y"].to_numpy(), names, "classic")
    assert (cooks_distance(res) >= 0).all()

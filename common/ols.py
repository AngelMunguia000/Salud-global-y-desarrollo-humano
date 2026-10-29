"""Regresión OLS con inferencia robusta y diagnósticos, solo con numpy/scipy.

Implementa lo que el contrato exige para M0–M5: errores clásicos, HC3 y
agrupados por país, VIF, Breusch–Pagan, RESET de Ramsey, Jarque–Bera,
apalancamiento y distancia de Cook.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class OLSResult:
    """Resultado de un ajuste OLS."""

    names: list[str]
    coef: np.ndarray
    cov: np.ndarray
    df_resid: int
    cov_type: str
    n: int
    k: int
    r2: float
    adj_r2: float
    rmse: float
    fitted: np.ndarray
    resid: np.ndarray
    leverage: np.ndarray
    X: np.ndarray = field(repr=False)
    y: np.ndarray = field(repr=False)

    def table(self, level: float = 0.95) -> pd.DataFrame:
        """Coeficientes con error estándar, t, p e intervalo de confianza."""
        se = np.sqrt(np.diag(self.cov))
        t = self.coef / se
        p = 2 * stats.t.sf(np.abs(t), self.df_resid)
        crit = stats.t.ppf(0.5 + level / 2, self.df_resid)
        return pd.DataFrame({
            "variable": self.names, "coef": self.coef, "error_est": se, "t": t,
            "p_valor": p, "ic95_inf": self.coef - crit * se,
            "ic95_sup": self.coef + crit * se,
        })

    def predict(self, X_new: np.ndarray) -> np.ndarray:
        """Predice con una matriz de diseño que incluye la constante."""
        return X_new @ self.coef


def design_matrix(df: pd.DataFrame, columns: list[str],
                  dummies: list[str] | None = None) -> tuple[np.ndarray, list[str]]:
    """Construye X con constante, regresores y dummies (k-1 niveles)."""
    parts = [pd.Series(1.0, index=df.index, name="const"), df[columns].astype(float)]
    for col in dummies or []:
        parts.append(pd.get_dummies(df[col], prefix=col, drop_first=True, dtype=float))
    X = pd.concat(parts, axis=1)
    return X.to_numpy(), list(X.columns)


def fit_ols(X: np.ndarray, y: np.ndarray, names: list[str],
            cov_type: str = "HC3", groups: np.ndarray | None = None) -> OLSResult:
    """Ajusta OLS.

    Args:
        X: Matriz de diseño (con constante).
        y: Respuesta.
        names: Nombres de columnas de ``X``.
        cov_type: ``"classic"``, ``"HC3"`` o ``"cluster"`` (requiere ``groups``).
        groups: Etiquetas de grupo (país) para errores agrupados.
    """
    n, k = X.shape
    xtx_inv = np.linalg.pinv(X.T @ X)
    coef = xtx_inv @ X.T @ y
    fitted = X @ coef
    resid = y - fitted
    leverage = np.einsum("ij,jk,ik->i", X, xtx_inv, X)
    rank = int(np.linalg.matrix_rank(X))
    df_resid = n - rank
    rss = float(resid @ resid)
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - rss / tss
    adj = 1 - (1 - r2) * (n - 1) / df_resid

    if cov_type == "classic":
        cov = rss / df_resid * xtx_inv
    elif cov_type == "HC3":
        w = (resid / (1 - np.clip(leverage, None, 0.999999))) ** 2
        cov = xtx_inv @ (X.T * w) @ X @ xtx_inv
    elif cov_type == "cluster":
        if groups is None:
            raise ValueError("cov_type='cluster' requiere groups")
        meat = np.zeros((k, k))
        labels = pd.factorize(groups)[0]
        g_count = labels.max() + 1
        score = X * resid[:, None]
        for g in range(g_count):
            s = score[labels == g].sum(axis=0)
            meat += np.outer(s, s)
        scale = g_count / (g_count - 1) * (n - 1) / (n - rank)
        cov = scale * xtx_inv @ meat @ xtx_inv
        df_resid = g_count - 1
    else:
        raise ValueError(f"cov_type no soportado: {cov_type}")
    return OLSResult(names, coef, cov, df_resid, cov_type, n, k, r2, adj,
                     float(np.sqrt(rss / n)), fitted, resid, leverage, X, y)


def vif(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Factor de inflación de varianza de cada regresor."""
    out = []
    for col in columns:
        others = [c for c in columns if c != col]
        if not others:
            out.append((col, 1.0))
            continue
        X, names = design_matrix(df, others)
        res = fit_ols(X, df[col].to_numpy(float), names, "classic")
        out.append((col, 1.0 / max(1 - res.r2, 1e-12)))
    return pd.DataFrame(out, columns=["variable", "vif"])


def breusch_pagan(res: OLSResult) -> tuple[float, float]:
    """Prueba Breusch–Pagan (versión de Koenker): estadístico LM y p-valor."""
    u2 = res.resid ** 2
    aux = fit_ols(res.X, u2, res.names, "classic")
    lm = res.n * aux.r2
    dof = int(np.linalg.matrix_rank(res.X)) - 1
    return float(lm), float(stats.chi2.sf(lm, dof))


def reset_test(res: OLSResult) -> tuple[float, float]:
    """RESET de Ramsey con ŷ² y ŷ³: estadístico F y p-valor."""
    extra = np.column_stack([res.fitted ** 2, res.fitted ** 3])
    X2 = np.column_stack([res.X, extra])
    full = fit_ols(X2, res.y, res.names + ["f2", "f3"], "classic")
    rss_r = float(res.resid @ res.resid)
    rss_u = float(full.resid @ full.resid)
    q = 2
    df2 = res.n - np.linalg.matrix_rank(X2)
    f = ((rss_r - rss_u) / q) / (rss_u / df2)
    return float(f), float(stats.f.sf(f, q, df2))


def jarque_bera(res: OLSResult) -> tuple[float, float]:
    """Prueba de normalidad de residuos Jarque–Bera."""
    stat, p = stats.jarque_bera(res.resid)
    return float(stat), float(p)


def cooks_distance(res: OLSResult) -> np.ndarray:
    """Distancia de Cook de cada observación."""
    rank = int(np.linalg.matrix_rank(res.X))
    s2 = float(res.resid @ res.resid) / (res.n - rank)
    h = np.clip(res.leverage, None, 0.999999)
    return res.resid ** 2 / (rank * s2) * h / (1 - h) ** 2


def diagnostics(res: OLSResult) -> dict[str, float]:
    """Resumen de diagnósticos de un modelo."""
    bp, bp_p = breusch_pagan(res)
    rs, rs_p = reset_test(res)
    jb, jb_p = jarque_bera(res)
    cook = cooks_distance(res)
    return {
        "n": res.n, "r2": res.r2, "r2_ajustado": res.adj_r2, "rmse": res.rmse,
        "breusch_pagan_lm": bp, "breusch_pagan_p": bp_p,
        "reset_f": rs, "reset_p": rs_p, "jarque_bera": jb, "jarque_bera_p": jb_p,
        "cook_max": float(cook.max()),
        "n_cook_gt_4n": int((cook > 4 / res.n).sum()),
        "leverage_max": float(res.leverage.max()),
    }

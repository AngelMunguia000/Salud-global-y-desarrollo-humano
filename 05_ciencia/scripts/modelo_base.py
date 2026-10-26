"""Modelo base para estimar esperanza de vida."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[2]
PANEL_PATH = ROOT / "03_data" / "processed" / "panel_salud_global.parquet"
OUTPUT_DIR = ROOT / "05_ciencia" / "evaluacion"

TARGET = "esperanza_vida"
NUMERIC_FEATURES = [
    "pib_per_capita_ppp",
    "gasto_salud_pct_pib",
    "escolaridad_promedio",
]
CATEGORICAL_FEATURES = ["region"]


def load_model_data(path: Path = PANEL_PATH) -> pd.DataFrame:
    """Carga observaciones completas para el modelo base."""
    if not path.is_file():
        raise FileNotFoundError(
            f"No existe el panel consolidado: {path}. Ejecuta primero el ETL."
        )
    data = pd.read_parquet(path)
    columns = [TARGET, *NUMERIC_FEATURES, *CATEGORICAL_FEATURES, "anio", "iso3", "pais"]
    missing = set(columns).difference(data.columns)
    if missing:
        raise ValueError(f"Faltan columnas para el modelo: {sorted(missing)}")
    return data.dropna(subset=[TARGET, *NUMERIC_FEATURES, *CATEGORICAL_FEATURES]).copy()


def build_pipeline() -> Pipeline:
    """Construye un modelo lineal con imputación y codificación explícitas."""
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preparation = ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        [
            ("preparation", preparation),
            ("model", LinearRegression()),
        ]
    )


def temporal_split(data: pd.DataFrame, test_years: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa los últimos años para evaluar sin usar datos futuros en el ajuste."""
    cutoff = int(data["anio"].max()) - test_years + 1
    train = data.loc[data["anio"] < cutoff].copy()
    test = data.loc[data["anio"] >= cutoff].copy()
    if train.empty or test.empty:
        raise ValueError("La separación temporal no produjo train y test no vacíos.")
    return train, test


def fit_and_evaluate(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """Ajusta el modelo, calcula métricas y devuelve predicciones con residuos."""
    train, test = temporal_split(data)
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    pipeline = build_pipeline()
    pipeline.fit(train[features], train[TARGET])
    predictions = pipeline.predict(test[features])
    evaluated = test[["iso3", "pais", "anio", TARGET]].copy()
    evaluated["esperanza_vida_predicha"] = predictions
    evaluated["residuo"] = evaluated[TARGET] - evaluated["esperanza_vida_predicha"]
    metrics = {
        "mae": float(mean_absolute_error(test[TARGET], predictions)),
        "rmse": float(mean_squared_error(test[TARGET], predictions) ** 0.5),
        "r2": float(r2_score(test[TARGET], predictions)),
    }
    return evaluated, metrics


def main() -> None:
    """Ejecuta la evaluación y guarda resultados reproducibles."""
    evaluated, metrics = fit_and_evaluate(load_model_data())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    evaluated.to_csv(OUTPUT_DIR / "predicciones_modelo_base.csv", index=False)
    pd.Series(metrics, name="valor").to_csv(OUTPUT_DIR / "metricas_modelo_base.csv")
    print(metrics)


if __name__ == "__main__":
    main()

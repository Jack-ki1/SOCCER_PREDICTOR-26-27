"""
The ML model zoo — see build plan §5 for the full roster and reasoning.
Cheap/interpretable models first, expensive/opaque ones last. Every model
here is walk-forward validated by engine/benchmark_suite.py before it's
allowed to influence the live ensemble (engine/ensemble_predictor.py) —
more models in the zoo isn't automatically better; each has to earn its
place against the "Dixon-Coles alone" baseline.

XGBoost and LightGBM are optional dependencies — imported lazily so the
rest of the project still runs (with a smaller model roster) if you
haven't installed them yet.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

FEATURE_COLUMNS = [
    "dc_lambda_home", "dc_lambda_away", "dc_lambda_diff",
    "elo_home", "elo_away", "elo_diff",
    "home_form_ppg", "home_form_gf", "home_form_ga",
    "away_form_ppg", "away_form_gf", "away_form_ga",
    "h2h_home_win_rate", "h2h_draw_rate",
    "home_rest_days", "away_rest_days",
    "home_attack", "home_defense", "away_attack", "away_defense",
]


def _try_import_xgboost():
    try:
        from xgboost import XGBClassifier
        return XGBClassifier
    except ImportError:
        return None


def _try_import_lightgbm():
    try:
        from lightgbm import LGBMClassifier
        return LGBMClassifier
    except ImportError:
        return None


def _try_import_catboost():
    try:
        from catboost import CatBoostClassifier
        return CatBoostClassifier
    except ImportError:
        return None


@dataclass
class ModelSpec:
    name: str
    build: callable          # () -> sklearn-compatible estimator
    needs_scaling: bool = False


def model_registry() -> list[ModelSpec]:
    """
    The full roster. Anything whose optional dependency isn't installed is
    silently skipped (not an error) — call this to see what's actually
    available in the current environment.
    """
    specs = [
        ModelSpec("logistic_regression", lambda: LogisticRegression(max_iter=1000), needs_scaling=True),
        ModelSpec("random_forest", lambda: RandomForestClassifier(n_estimators=300, max_depth=6, random_state=42)),
        ModelSpec("gradient_boosting", lambda: GradientBoostingClassifier(n_estimators=200, max_depth=3, random_state=42)),
        ModelSpec("svm", lambda: SVC(probability=True, kernel="rbf", random_state=42), needs_scaling=True),
        ModelSpec("naive_bayes", lambda: GaussianNB()),
        ModelSpec("knn", lambda: KNeighborsClassifier(n_neighbors=15), needs_scaling=True),
        ModelSpec("mlp", lambda: MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=1000, random_state=42), needs_scaling=True),
    ]

    XGBClassifier = _try_import_xgboost()
    if XGBClassifier:
        specs.append(ModelSpec("xgboost", lambda: XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.05, eval_metric="mlogloss", random_state=42,
        )))

    LGBMClassifier = _try_import_lightgbm()
    if LGBMClassifier:
        specs.append(ModelSpec("lightgbm", lambda: LGBMClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.05, verbosity=-1, random_state=42,
        )))

    CatBoostClassifier = _try_import_catboost()
    if CatBoostClassifier:
        specs.append(ModelSpec("catboost", lambda: CatBoostClassifier(
            iterations=300, depth=4, learning_rate=0.05, verbose=False, random_state=42,
        )))

    return specs


class TrainedModel:
    """Wraps a fitted estimator + its scaler (if any) + the label encoding, for consistent predict_proba calls."""

    def __init__(self, name: str, estimator, scaler: StandardScaler | None, classes: list[str]):
        self.name = name
        self.estimator = estimator
        self.scaler = scaler
        self.classes = classes  # original string labels, in the order predict_proba's columns come out

    def predict_proba(self, X: pd.DataFrame) -> dict[str, float]:
        X_arr = X[FEATURE_COLUMNS].values
        if self.scaler is not None:
            X_arr = self.scaler.transform(X_arr)
        proba = self.estimator.predict_proba(X_arr)[0]
        return {cls: float(p) for cls, p in zip(self.classes, proba)}


def train_model(spec: ModelSpec, X: pd.DataFrame, y: pd.Series) -> TrainedModel:
    """
    Labels are encoded to integers before fitting (XGBoost/LightGBM require
    numeric class labels; the others tolerate strings but there's no harm
    in treating them all the same way). classes_ from the fitted encoder
    maps back to the original 'H'/'D'/'A' strings for predict_proba.
    """
    from sklearn.preprocessing import LabelEncoder

    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    X_arr = X[FEATURE_COLUMNS].values
    scaler = None
    if spec.needs_scaling:
        scaler = StandardScaler()
        X_arr = scaler.fit_transform(X_arr)
    estimator = spec.build()
    estimator.fit(X_arr, y_encoded)
    # estimator.classes_ is now integer-encoded (0..n-1) in the order predict_proba emits;
    # map back through the encoder to get the original string labels in the same order.
    original_order_classes = list(encoder.inverse_transform(estimator.classes_))
    return TrainedModel(spec.name, estimator, scaler, original_order_classes)


def train_all(X: pd.DataFrame, y: pd.Series) -> dict[str, TrainedModel]:
    """Train every available model in the registry on the same (X, y). Returns {name: TrainedModel}."""
    trained = {}
    for spec in model_registry():
        try:
            trained[spec.name] = train_model(spec, X, y)
        except Exception as exc:  # a single flaky model shouldn't take down the whole training run
            print(f"[ml_models] {spec.name} failed to train: {exc}")
    return trained

"""Tests for engine/ml_models.py — every registered model must train and
predict valid probability distributions."""
import numpy as np
import pandas as pd
import pytest

from engine.ml_models import FEATURE_COLUMNS, model_registry, train_all


@pytest.fixture
def synthetic_data():
    np.random.seed(42)
    n = 150
    X = pd.DataFrame({c: np.random.randn(n) for c in FEATURE_COLUMNS})
    y = pd.Series(np.random.choice(["H", "D", "A"], size=n, p=[0.45, 0.25, 0.30]))
    return X, y


def test_model_registry_has_multiple_models():
    specs = model_registry()
    assert len(specs) >= 7  # the sklearn-only baseline roster; more if xgboost/lightgbm/catboost installed


def test_all_registered_models_train_successfully(synthetic_data):
    X, y = synthetic_data
    trained = train_all(X, y)
    registry_names = {s.name for s in model_registry()}
    assert set(trained.keys()) == registry_names, "one or more models failed to train — check the console output"


def test_every_trained_model_predicts_valid_probabilities(synthetic_data):
    X, y = synthetic_data
    trained = train_all(X, y)
    row = X.iloc[[0]]
    for name, model in trained.items():
        proba = model.predict_proba(row)
        assert set(proba.keys()) == {"H", "D", "A"}, f"{name} returned unexpected classes: {proba.keys()}"
        assert sum(proba.values()) == pytest.approx(1.0, abs=1e-4), f"{name} probabilities don't sum to 1"
        assert all(0 <= p <= 1 for p in proba.values()), f"{name} produced an out-of-range probability"

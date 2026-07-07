"""Proper scoring rules and evaluation metrics."""

import numpy as np
from typing import Dict, List, Tuple


def ranked_probability_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Ranked Probability Score (RPS) - standard for soccer prediction."""
    n_samples = len(y_true)
    rps = 0.0
    for i in range(n_samples):
        true_cdf = np.zeros(3)
        true_cdf[y_true[i]:] = 1.0
        pred_cdf = np.cumsum(y_pred[i])
        rps += np.sum((pred_cdf - true_cdf) ** 2) / (3 - 1)
    return rps / n_samples


def log_loss(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-15) -> float:
    """Log loss (cross-entropy)."""
    y_pred_clipped = np.clip(y_pred, eps, 1 - eps)
    n_samples = len(y_true)
    loss = 0.0
    for i in range(n_samples):
        loss -= np.log(y_pred_clipped[i, y_true[i]])
    return loss / n_samples


def brier_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Brier score (mean squared error of probabilities)."""
    n_samples = len(y_true)
    n_classes = y_pred.shape[1]
    y_onehot = np.zeros((n_samples, n_classes))
    y_onehot[np.arange(n_samples), y_true] = 1.0
    return np.mean(np.sum((y_pred - y_onehot) ** 2, axis=1))


def calibration_error(y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = 10) -> Dict[str, float]:
    """Expected Calibration Error (ECE) per class and overall."""
    n_classes = y_pred.shape[1]
    ece_per_class = {}

    for c in range(n_classes):
        confidences = y_pred[:, c]
        accuracies = (y_true == c).astype(float)

        bin_edges = np.linspace(0, 1, n_bins + 1)
        ece = 0.0

        for i in range(n_bins):
            mask = (confidences >= bin_edges[i]) & (confidences < bin_edges[i + 1])
            if i == n_bins - 1:
                mask = (confidences >= bin_edges[i]) & (confidences <= bin_edges[i + 1])

            if mask.sum() > 0:
                avg_confidence = confidences[mask].mean()
                avg_accuracy = accuracies[mask].mean()
                ece += mask.sum() * np.abs(avg_confidence - avg_accuracy)

        ece_per_class[f"class_{c}"] = ece / len(y_true)

    ece_per_class["overall"] = np.mean(list(ece_per_class.values()))
    return ece_per_class


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Classification accuracy."""
    predictions = np.argmax(y_pred, axis=1)
    return np.mean(predictions == y_true)


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Comprehensive evaluation dictionary."""
    return {
        "rps": round(ranked_probability_score(y_true, y_pred), 4),
        "log_loss": round(log_loss(y_true, y_pred), 4),
        "brier_score": round(brier_score(y_true, y_pred), 4),
        "accuracy": round(accuracy(y_true, y_pred), 4),
        "calibration_error": round(calibration_error(y_true, y_pred)["overall"], 4),
    }


def reliability_diagram_data(y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = 10) -> List[Dict]:
    """Data for reliability diagram plotting."""
    data = []
    for c in range(3):
        confidences = y_pred[:, c]
        accuracies = (y_true == c).astype(float)
        bin_edges = np.linspace(0, 1, n_bins + 1)

        for i in range(n_bins):
            mask = (confidences >= bin_edges[i]) & (confidences < bin_edges[i + 1])
            if i == n_bins - 1:
                mask = (confidences >= bin_edges[i]) & (confidences <= bin_edges[i + 1])

            if mask.sum() > 0:
                data.append({
                    "class": ["Home", "Draw", "Away"][c],
                    "bin_lower": bin_edges[i],
                    "bin_upper": bin_edges[i + 1],
                    "confidence": confidences[mask].mean(),
                    "accuracy": accuracies[mask].mean(),
                    "count": int(mask.sum()),
                })
    return data

"""Model insights and architecture routes."""

from flask import Blueprint, render_template, jsonify

from src.soccer_predictor.services.prediction_service import get_prediction_service
from src.soccer_predictor.core.model_arena import ModelArena

bp = Blueprint("insights", __name__)
prediction_service = get_prediction_service()


@bp.route("/")
def insights_page():
    """Model architecture and performance insights."""
    feature_importance = prediction_service.get_feature_importance()
    weights = prediction_service.ensemble.get_weights()

    return render_template(
        "insights.html",
        feature_importance=feature_importance,
        weights=weights,
        model_info={
            "architecture": "ensemble",
            "components": ["poisson_dixon_coles", "elo_bradley_terry", "market_odds", "hybrid_rf"],
            "champion": "hybrid_rf",
        },
    )


@bp.route("/api/feature-importance")
def api_feature_importance():
    """API: feature importance ranking."""
    importance = prediction_service.get_feature_importance()
    sorted_features = sorted(
        importance.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:20]
    return jsonify({"features": [{"name": k, "importance": round(v, 4)} for k, v in sorted_features]})


@bp.route("/api/arena/status")
def arena_status():
    """Model arena leaderboard."""
    arena = ModelArena()
    return jsonify({
        "champion": arena.champion,
        "contenders": arena.CONTENDERS,
        "leaderboard": arena.leaderboard,
    })


@bp.route("/api/calibration-data")
def calibration_data():
    """Mock calibration data for visualization."""
    bins = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    return jsonify({
        "home": [{"bin": b, "predicted": b, "observed": b + 0.02} for b in bins],
        "draw": [{"bin": b, "predicted": b, "observed": b - 0.01} for b in bins],
        "away": [{"bin": b, "predicted": b, "observed": b + 0.015} for b in bins],
    })

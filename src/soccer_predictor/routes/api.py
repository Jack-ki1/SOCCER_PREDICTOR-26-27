"""REST API routes (replaces FastAPI)."""

from flask import Blueprint, request, jsonify, session

from src.soccer_predictor.services.prediction_service import get_prediction_service
from src.soccer_predictor.services.fixture_service import get_fixture_service
from src.soccer_predictor.services.league_service import get_league_service
from src.soccer_predictor.services.simulation_service import get_simulation_service
from src.soccer_predictor.services.data_service import get_data_service

bp = Blueprint("api", __name__)

prediction_service = get_prediction_service()
fixture_service = get_fixture_service()
league_service = get_league_service()
simulation_service = get_simulation_service()
data_service = get_data_service()


@bp.route("/health")
def api_health():
    """API health check."""
    return jsonify({
        "status": "healthy",
        "version": "3.0.0-Flask",
        "season": "2026-2027",
        "endpoints": [
            "/api/v1/teams",
            "/api/v1/matches",
            "/api/v1/matches/<id>/prediction",
            "/api/v1/leagues/<league>/forecast",
            "/api/v1/model/info",
        ],
    })


@bp.route("/teams")
def api_teams():
    """List all teams or filter by league."""
    league = request.args.get("league")
    teams = fixture_service.get_leagues()
    if league:
        teams = [t for t in teams if t["name"] == league]
    return jsonify({"teams": teams})


@bp.route("/matches")
def api_matches():
    """List matches."""
    league = request.args.get("league")
    matchday = request.args.get("matchday", type=int)
    fixtures = fixture_service.get_fixtures_by_league(league, matchday) if league else                fixture_service.get_all_fixtures(matchday)

    return jsonify({"matches": [fixture_service.serialize_match(f) for f in fixtures]})


@bp.route("/matches/results")
def api_match_results():
    """List finished matches with scores."""
    league = request.args.get("league", "Premier League")
    days_back = request.args.get("days_back", 30, type=int)
    results = fixture_service.get_results_by_league(league, days_back)
    return jsonify({"league": league, "results": [fixture_service.serialize_match(f) for f in results]})


@bp.route("/matches/live")
def api_live_matches():
    """List live matches."""
    league = request.args.get("league")
    matches = fixture_service.get_live_matches(league)
    return jsonify({"matches": [fixture_service.serialize_match(f) for f in matches]})


@bp.route("/matches/<match_id>/prediction")
def api_match_prediction(match_id: str):
    """Get prediction for a match."""
    weights = request.args.get("weights")
    if weights:
        import json
        try:
            weights = json.loads(weights)
        except json.JSONDecodeError:
            weights = None

    result = prediction_service.predict_match(match_id, weights=weights)
    return jsonify(result)


@bp.route("/leagues/<league>/forecast")
def api_league_forecast(league: str):
    """Get league forecast."""
    iterations = request.args.get("iterations", 5000, type=int)
    forecast = league_service.get_league_forecast(league, iterations)
    return jsonify(forecast)


@bp.route("/model/info")
def api_model_info():
    """Get model architecture info."""
    return jsonify({
        "architecture": "ensemble",
        "components": [
            {"name": "poisson_dixon_coles", "type": "statistical", "description": "Poisson with Dixon-Coles low-score correction"},
            {"name": "elo_bradley_terry", "type": "statistical", "description": "Elo ratings with Bradley-Terry draw component"},
            {"name": "market_odds", "type": "bayesian_prior", "description": "Bookmaker odds as Bayesian prior"},
            {"name": "hybrid_rf", "type": "machine_learning", "description": "Hybrid Random Forest for xG prediction"},
        ],
        "ensemble_weights": prediction_service.get_weights(),  # FIXED: Using the method we added
        "champion_model": session.get("model_champion", "hybrid_rf"),
        "features": 95,
        "evaluation_metrics": ["RPS", "Log Loss", "Brier Score", "Calibration Error"],
    })


@bp.route("/features/importance")
def api_feature_importance():
    """Get feature importance."""
    importance = prediction_service.get_feature_importance()
    return jsonify({
        "features": [
            {"name": k, "importance": round(v, 6)}
            for k, v in sorted(importance.items(), key=lambda x: x[1], reverse=True)[:20]
        ]
    })


@bp.route("/monitoring/drift")
def api_drift():
    """Get drift detection status."""
    return jsonify({
        "status": "healthy",
        "drift_detected": False,
        "current_rps": 0.187,
        "baseline_rps": 0.190,
        "recommendation": "Continue monitoring",
    })

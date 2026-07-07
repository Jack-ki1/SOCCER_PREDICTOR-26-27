"""Match prediction routes."""

from flask import Blueprint, render_template, jsonify, request, session

from src.soccer_predictor.services.prediction_service import get_prediction_service
from src.soccer_predictor.services.fixture_service import get_fixture_service

bp = Blueprint("predictions", __name__)
prediction_service = get_prediction_service()
fixture_service = get_fixture_service()


@bp.route("/")
def predictions_page():
    """Match prediction interface."""
    leagues = fixture_service.get_leagues()
    selected_league = session.get("selected_league", "Premier League")
    fixtures = fixture_service.get_fixtures_by_league(selected_league)
    
    # Check if API is configured
    api_configured = fixture_service.api_configured

    return render_template(
        "predictions.html",
        leagues=leagues,
        selected_league=selected_league,
        fixtures=fixtures,
        api_configured=api_configured
    )


@bp.route("/match/<match_id>")
def match_prediction(match_id: str):
    """Get prediction for a specific match."""
    if request.headers.get("Accept") == "application/json":
        weights = session.get("ensemble_weights")
        use_calibration = session.get("use_calibration", True)
        result = prediction_service.predict_match(
            match_id, weights=weights, use_calibration=use_calibration
        )
        return jsonify(result)

    # HTML page
    match = fixture_service.get_fixture_by_id(match_id)
    if match is None:
        # Check if API is configured
        api_configured = fixture_service.api_configured
        error_msg = f"Match {match_id} not found"
        if not api_configured:
            error_msg += ". API keys not configured. Visit Setup page to configure API keys."
        
        return render_template(
            "predictions.html", 
            error=error_msg,
            fixtures=fixture_service.get_fixtures_by_league(session.get("selected_league", "Premier League")),
            leagues=fixture_service.get_leagues(),
            api_configured=api_configured
        ), 404

    weights = session.get("ensemble_weights")
    use_calibration = session.get("use_calibration", True)
    prediction = prediction_service.predict_match(
        match_id, weights=weights, use_calibration=use_calibration
    )

    # Get fixtures for sidebar
    fixtures = fixture_service.get_fixtures_by_league(match.league)

    # Check if prediction contains an error
    if 'error' in prediction:
        return render_template(
            "predictions.html",
            match=match,
            prediction=prediction,
            fixtures=fixtures,
            leagues=fixture_service.get_leagues(),
            selected_league=match.league,
            api_configured=fixture_service.api_configured
        )

    return render_template(
        "predictions.html",
        match=match,
        prediction=prediction,
        fixtures=fixtures,
        leagues=fixture_service.get_leagues(),
        selected_league=match.league,
        api_configured=fixture_service.api_configured
    )


@bp.route("/api/predict", methods=["POST"])
def api_predict():
    """API endpoint for batch predictions."""
    data = request.get_json() or {}
    match_ids = data.get("match_ids", [])
    weights = data.get("weights", session.get("ensemble_weights"))

    if not match_ids:
        return jsonify({"error": "No match_ids provided"}), 400

    results = prediction_service.predict_batch(match_ids, weights=weights)
    return jsonify({"predictions": results})


@bp.route("/weights", methods=["GET", "POST"])
def weights():
    """Get or update ensemble weights."""
    if request.method == "POST":
        data = request.get_json() or {}
        new_weights = {
            "poisson": data.get("poisson", 0.50),
            "elo": data.get("elo", 0.30),
            "market": data.get("market", 0.20),
            "ml": data.get("ml", 0.0),
        }
        session["ensemble_weights"] = new_weights
        prediction_service.ensemble.set_weights(**new_weights)
        return jsonify({"weights": new_weights, "status": "updated"})

    return jsonify({"weights": session.get("ensemble_weights")})
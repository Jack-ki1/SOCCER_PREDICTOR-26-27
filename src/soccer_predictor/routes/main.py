"""Main/home routes."""

from flask import Blueprint, render_template, jsonify
from src.soccer_predictor.services.fixture_service import get_fixture_service
from src.soccer_predictor.services.prediction_service import get_prediction_service
from src.soccer_predictor.services.database import get_database

bp = Blueprint("main", __name__)
fixture_service = get_fixture_service()
prediction_service = get_prediction_service()
db = get_database()


@bp.route("/")
def index():
    """Dashboard home page."""
    # Get real data for the dashboard
    today_matches = fixture_service.get_fixtures_by_league("Premier League")  # Will get today's matches if any
    live_matches = fixture_service.get_live_matches()
    
    # Get data summary
    data_summary = fixture_service.get_data_summary()

    return render_template(
        "index.html",
        today_matches=today_matches,
        live_matches=live_matches,
        data_summary=data_summary,
        api_configured=fixture_service.api_configured
    )



@bp.route("/about")
def about():
    """About page with system info."""
    return render_template("about.html")


@bp.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "version": "3.0.0-Flask",
        "season": "2026-2027",
    })
"""Analytics and visualization routes."""

from flask import Blueprint, render_template, jsonify, request

from src.soccer_predictor.services.fixture_service import get_fixture_service

bp = Blueprint("analytics", __name__)
fixture_service = get_fixture_service()


@bp.route("/")
def analytics_page():
    """Analytics dashboard with pitch visualizations."""
    leagues = fixture_service.get_leagues()
    return render_template("analytics.html", leagues=leagues)


@bp.route("/team/<team_id>")
def team_analytics(team_id: str):
    """Team-specific analytics."""
    # TODO: Implement real team analytics using API data
    # For now, return basic info or error if team not found
    return jsonify({"error": "Team analytics not yet implemented with real data"})
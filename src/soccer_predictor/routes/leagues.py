"""League forecast and simulation routes."""

from flask import Blueprint, render_template, jsonify, request

from src.soccer_predictor.services.league_service import get_league_service
from src.soccer_predictor.services.simulation_service import get_simulation_service
from src.soccer_predictor.services.fixture_service import get_fixture_service

bp = Blueprint("leagues", __name__)
league_service = get_league_service()
simulation_service = get_simulation_service()
fixture_service = get_fixture_service()


@bp.route("/")
def leagues_page():
    """League overview page."""
    leagues = fixture_service.get_leagues()
    return render_template("leagues.html", leagues=leagues)


@bp.route("/forecast/<league_name>")
def league_forecast(league_name: str):
    """League forecast page."""
    iterations = request.args.get("iterations", 5000, type=int)

    if request.headers.get("Accept") == "application/json":
        forecast = league_service.get_league_forecast(league_name, iterations)
        return jsonify(forecast)

    return render_template(
        "league_forecast.html",
        league=league_name,
        iterations=iterations,
        leagues=fixture_service.get_leagues(),
    )


@bp.route("/forecast/<league_name>/start", methods=["POST"])
def start_forecast(league_name: str):
    """Start async simulation job."""
    data = request.get_json() or {}
    iterations = data.get("iterations", 5000)

    job_id = simulation_service.start_simulation(league_name, iterations)
    return jsonify({"job_id": job_id, "status": "started"})


@bp.route("/forecast/status/<job_id>")
def forecast_status(job_id: str):
    """Poll simulation status."""
    status = simulation_service.get_job_status(job_id)
    if status is None:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(status)


@bp.route("/api/forecast/<league_name>")
def api_forecast(league_name: str):
    """Synchronous API forecast (for smaller requests)."""
    iterations = request.args.get("iterations", 1000, type=int)
    forecast = league_service.get_league_forecast(league_name, iterations)
    return jsonify(forecast)

"""Fixture listing and management routes."""

from flask import Blueprint, render_template, jsonify, request

from src.soccer_predictor.services.fixture_service import get_fixture_service

bp = Blueprint("fixtures", __name__)
fixture_service = get_fixture_service()


@bp.route("/")
def fixtures_page():
    """All fixtures page."""
    league = request.args.get("league")
    matchday = request.args.get("matchday", type=int)

    if league:
        fixtures = fixture_service.get_fixtures_by_league(league, matchday)
    else:
        fixtures = fixture_service.get_all_fixtures(matchday)

    leagues = fixture_service.get_leagues()
    results = fixture_service.get_results_by_league(league or "Premier League")
    live_matches = fixture_service.get_live_matches(league)
    data_summary = fixture_service.get_data_summary(league)

    return render_template(
        "fixtures.html",
        fixtures=[fixture_service.serialize_match(f) for f in fixtures],
        results=[fixture_service.serialize_match(f) for f in results],
        live_matches=[fixture_service.serialize_match(f) for f in live_matches],
        data_summary=data_summary,
        leagues=leagues,
        selected_league=league,
        selected_matchday=matchday,
        api_configured=fixture_service.api_configured
    )


@bp.route("/league/<league_name>")
def league_fixtures(league_name: str):
    """Fixtures for a specific league."""
    matchday = request.args.get("matchday", type=int)
    fixtures = fixture_service.get_fixtures_by_league(league_name, matchday)
    matchdays = fixture_service.get_matchdays(league_name)
    results = fixture_service.get_results_by_league(league_name)
    live_matches = fixture_service.get_live_matches(league_name)
    data_summary = fixture_service.get_data_summary(league_name)

    return render_template(
        "fixtures.html",
        fixtures=[fixture_service.serialize_match(f) for f in fixtures],
        results=[fixture_service.serialize_match(f) for f in results],
        live_matches=[fixture_service.serialize_match(f) for f in live_matches],
        data_summary=data_summary,
        leagues=fixture_service.get_leagues(),
        selected_league=league_name,
        matchdays=matchdays,
        selected_matchday=matchday,
        api_configured=fixture_service.api_configured
    )


@bp.route("/api/list")
def api_fixtures():
    """API endpoint for fixtures."""
    league = request.args.get("league")
    matchday = request.args.get("matchday", type=int)

    fixtures = fixture_service.get_fixtures_by_league(league, matchday) if league else                fixture_service.get_all_fixtures(matchday)

    return jsonify({"fixtures": [fixture_service.serialize_match(f) for f in fixtures]})


@bp.route("/api/results")
def api_results():
    """API endpoint for finished match results."""
    league = request.args.get("league", "Premier League")
    days_back = request.args.get("days_back", 30, type=int)
    results = fixture_service.get_results_by_league(league, days_back)
    return jsonify({"league": league, "results": [fixture_service.serialize_match(f) for f in results]})


@bp.route("/api/live")
def api_live():
    """API endpoint for live matches."""
    league = request.args.get("league")
    live_matches = fixture_service.get_live_matches(league)
    return jsonify({"matches": [fixture_service.serialize_match(f) for f in live_matches]})


@bp.route("/api/standings/<league_name>")
def api_standings(league_name: str):
    """API endpoint for league standings."""
    standings = fixture_service.get_standings(league_name)
    return jsonify({"league": league_name, "standings": standings})
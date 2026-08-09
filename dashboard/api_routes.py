"""
JSON API blueprint — the endpoint spec from the build plan §8, implemented
as Flask routes (this is the "FastAPI-shaped" API from the earlier
prototype session, ported to Flask so there's one framework, not two).
Registered under /api/v1 by dashboard/app.py.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from config.feature_weights import DEFAULT_WEIGHTS, get_weights
from data.calendar_2026 import get_fixtures, total_matchweeks
from data.live_updater import cross_check_with_api_football, refresh_live_state
from data.team_data import get_all_teams, get_team
from engine.predictor import get_fpl_lab_data, get_prediction, get_season_projection

api_bp = Blueprint("api", __name__)


def _weights_from_query() -> dict:
    """Lets the frontend override home_advantage_weight / recent_form_weight / rho via
    query params, same three knobs as the React prototype's Model Lab sliders."""
    overrides = {}
    for key in ("home_advantage_weight", "recent_form_weight"):
        val = request.args.get(key, type=float)
        if val is not None:
            overrides[key] = val
    rho = request.args.get("dixon_coles_rho", type=float)
    if rho is not None:
        overrides["dixon_coles_rho"] = rho
    return get_weights(overrides) if overrides else DEFAULT_WEIGHTS


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@api_bp.get("/teams")
def teams():
    return jsonify({"teams": get_all_teams()})


@api_bp.get("/teams/<team_id>")
def team_detail(team_id: str):
    team = get_team(team_id)
    if not team:
        return jsonify({"error": f"Unknown team id {team_id!r}"}), 404
    return jsonify(team)


@api_bp.get("/fixtures")
def fixtures():
    matchweek = request.args.get("matchweek", type=int)
    return jsonify({
        "fixtures": get_fixtures(matchweek),
        "total_matchweeks": total_matchweeks(),
    })


@api_bp.get("/predict/<home_id>/<away_id>")
def predict(home_id: str, away_id: str):
    try:
        p = get_prediction(home_id, away_id, _weights_from_query())
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    return jsonify({
        "home_id": p.home_id, "away_id": p.away_id,
        "lambda_home": p.lambda_home, "lambda_away": p.lambda_away,
        "p_home": p.market.p_home, "p_draw": p.market.p_draw, "p_away": p.market.p_away,
        "p_btts": p.market.p_btts, "p_over_2_5": p.market.p_over_2_5, "p_under_2_5": p.market.p_under_2_5,
        "p_clean_sheet_home": p.market.p_clean_sheet_home, "p_clean_sheet_away": p.market.p_clean_sheet_away,
        "top_scorelines": p.market.top_scorelines,
        "grid": p.grid,
        "captain_score_home": p.captain_score_home, "captain_score_away": p.captain_score_away,
    })


@api_bp.post("/simulate-season")
def simulate_season_endpoint():
    body = request.get_json(silent=True) or {}
    n_sims = int(body.get("n_sims", 300))
    n_sims = max(50, min(2000, n_sims))  # guard against an accidental/malicious huge request blocking the process
    seed = str(body.get("seed", "season-v1"))
    projection = get_season_projection(_weights_from_query(), n_sims=n_sims, seed=seed)
    return jsonify({
        "n_sims": n_sims,
        "projection": [
            {
                "club_id": r.club_id, "title_prob": r.title_prob, "top4_prob": r.top4_prob,
                "releg_prob": r.releg_prob, "avg_points": r.avg_points, "avg_goal_diff": r.avg_goal_diff,
            }
            for r in projection
        ],
    })


@api_bp.get("/fpl/captain-picks")
def fpl_captain_picks():
    matchweek = request.args.get("matchweek", 1, type=int)
    rows = get_fpl_lab_data(matchweek, _weights_from_query())
    return jsonify({"matchweek": matchweek, "rows": rows})


@api_bp.get("/model/metadata")
def model_metadata():
    """The honesty/transparency panel from the React prototype's Model Lab tab, served as real data."""
    return jsonify({
        "engine_version": "v1 — Dixon-Coles + Monte Carlo",
        "roadmap": [
            {"version": "v1", "name": "Dixon-Coles + Monte Carlo", "status": "active"},
            {"version": "v2", "name": "Elo blend", "status": "planned"},
            {"version": "v3", "name": "ML ensemble (XGBoost / LightGBM / Random Forest / ...)", "status": "planned"},
            {"version": "v4", "name": "LLM-augmented explanations", "status": "planned"},
        ],
        "published_ceiling_note": (
            "Ensembles blending Dixon-Coles + market odds + text signals have reported ~63% "
            "match-result accuracy on the Premier League (Beal et al.) — treat any single-model "
            "claim meaningfully above that with suspicion."
        ),
        "current_weights": DEFAULT_WEIGHTS,
    })


@api_bp.post("/live-data/refresh")
def trigger_live_refresh():
    """Manually trigger the same refresh the scheduler runs periodically — useful for the
    (optional) Flask admin pages' 'refresh now' button, or just testing without waiting."""
    season = request.args.get("season", "2026-27")
    result = refresh_live_state(season)
    return jsonify(result), (200 if result["ok"] else 502)

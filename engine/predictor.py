"""
Prediction orchestrator — the single entry point dashboard/api_routes.py
calls. Wraps engine/probability_model.py, engine/monte_carlo.py, and
engine/ensemble_predictor.py behind a couple of simple functions so the
web layer doesn't need to know about Dixon-Coles internals at all.
"""
from __future__ import annotations

from config.constants import TEAMS, TEAMS_BY_ID
from config.feature_weights import DEFAULT_WEIGHTS
from engine.monte_carlo import ALL_FIXTURES, TeamProjection, simulate_season
from engine.probability_model import Prediction, predict_match


def get_prediction(home_id: str, away_id: str, weights: dict | None = None) -> Prediction:
    """Single-match prediction by club id — what dashboard/api_routes.py's
    /api/v1/predict/<fixture_id> route calls after resolving the fixture."""
    home = TEAMS_BY_ID.get(home_id)
    away = TEAMS_BY_ID.get(away_id)
    if not home or not away:
        raise ValueError(f"Unknown club id(s): {home_id!r}, {away_id!r}")
    return predict_match(home, away, weights)


def get_season_projection(weights: dict | None = None, n_sims: int = 300, seed: str = "season-v1") -> list[TeamProjection]:
    """Full-season Monte Carlo projection, sorted by average points descending."""
    return simulate_season(weights=weights or DEFAULT_WEIGHTS, n_sims=n_sims, seed=seed)


def get_matchweek_fixtures(matchweek: int) -> list[dict]:
    fixtures = [f for f in ALL_FIXTURES if f.round == matchweek]
    return [{"home": f.home, "away": f.away, "round": f.round} for f in fixtures]


def get_fpl_lab_data(matchweek: int, weights: dict | None = None) -> list[dict]:
    """
    Per-fixture captain-score and clean-sheet data for a whole gameweek —
    what dashboard's FPL Lab page/route calls. Mirrors the React
    prototype's FPLLabTab computation exactly (one row per side per
    fixture, not one row per fixture).
    """
    rows = []
    for fx in get_matchweek_fixtures(matchweek):
        pred = get_prediction(fx["home"], fx["away"], weights)
        home, away = TEAMS_BY_ID[fx["home"]], TEAMS_BY_ID[fx["away"]]
        rows.append({
            "club_id": home["id"], "club_name": home["name"], "opponent": away["name"], "venue": "H",
            "xg": pred.lambda_home, "win_prob": pred.market.p_home,
            "clean_sheet_prob": pred.market.p_clean_sheet_home, "captain_score": pred.captain_score_home,
        })
        rows.append({
            "club_id": away["id"], "club_name": away["name"], "opponent": home["name"], "venue": "A",
            "xg": pred.lambda_away, "win_prob": pred.market.p_away,
            "clean_sheet_prob": pred.market.p_clean_sheet_away, "captain_score": pred.captain_score_away,
        })
    return rows


def team_list() -> list[dict]:
    return TEAMS

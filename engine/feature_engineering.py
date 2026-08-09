"""
Feature engineering for the ML ensemble (engine/ml_models.py).

Builds the feature set specified in the build plan §6.2. Every feature
here is computable from data already modeled elsewhere in this codebase
(Dixon-Coles output, Elo, fixtures/results history) — nothing here assumes
a data source that isn't already accounted for in data/.

Historical results are expected as a chronologically-sorted list of dicts:
    {"date": date, "home_id": str, "away_id": str,
     "home_goals": int, "away_goals": int, "season": str}
— exactly the shape data/soccerdata_integration.py and
data/historical_loader-style ingestion should produce.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from engine.elo_calculator import elo_to_match_probabilities
from engine.fatigue_model import rest_days
from engine.probability_model import league_averages, match_lambdas


def _team_matches(history: list[dict], team_id: str, before: date) -> list[dict]:
    return [m for m in history if (m["home_id"] == team_id or m["away_id"] == team_id) and m["date"] < before]


def rolling_form(history: list[dict], team_id: str, before: date, window: int = 5, venue: str | None = None) -> dict:
    """
    Points-per-game and goals-for/against over the last `window` matches
    before `before`. venue='home'/'away' restricts to that venue only —
    teams perform differently by venue, so keep these separate rather than
    blending into one number (see build plan §6.2).
    """
    matches = _team_matches(history, team_id, before)
    if venue == "home":
        matches = [m for m in matches if m["home_id"] == team_id]
    elif venue == "away":
        matches = [m for m in matches if m["away_id"] == team_id]
    matches = matches[-window:]

    if not matches:
        return {"ppg": 1.3, "gf_per_game": 1.3, "ga_per_game": 1.3, "sample_size": 0}  # neutral prior for thin history

    pts, gf, ga = 0, 0, 0
    for m in matches:
        is_home = m["home_id"] == team_id
        team_goals = m["home_goals"] if is_home else m["away_goals"]
        opp_goals = m["away_goals"] if is_home else m["home_goals"]
        gf += team_goals
        ga += opp_goals
        if team_goals > opp_goals:
            pts += 3
        elif team_goals == opp_goals:
            pts += 1

    n = len(matches)
    return {"ppg": pts / n, "gf_per_game": gf / n, "ga_per_game": ga / n, "sample_size": n}


def head_to_head(history: list[dict], home_id: str, away_id: str, before: date, last_n: int = 5) -> dict:
    matches = [
        m for m in history
        if m["date"] < before
        and {m["home_id"], m["away_id"]} == {home_id, away_id}
    ][-last_n:]
    if not matches:
        return {"home_win_rate": 0.45, "draw_rate": 0.25, "sample_size": 0}  # roughly league-average prior

    home_wins = draws = 0
    for m in matches:
        # normalize to "was home_id the home side in that fixture"
        home_id_was_home = m["home_id"] == home_id
        if m["home_goals"] == m["away_goals"]:
            draws += 1
        elif (m["home_goals"] > m["away_goals"]) == home_id_was_home:
            home_wins += 1
    n = len(matches)
    return {"home_win_rate": home_wins / n, "draw_rate": draws / n, "sample_size": n}


def build_feature_row(
    home: dict, away: dict,
    history: list[dict],
    match_date: date,
    weights: dict | None = None,
    home_last_match_date: date | None = None,
    away_last_match_date: date | None = None,
    home_elo: float = 1500.0,
    away_elo: float = 1500.0,
) -> dict:
    """
    One row of engineered features for a single fixture, ready to hand to
    engine/ml_models.py. Combines the Dixon-Coles baseline's own output
    (feed the baseline INTO the ensemble, per build plan §6.1) with
    rolling form, H2H, rest days, and Elo.
    """
    lambdas = match_lambdas(home, away, weights)
    dc = elo_to_match_probabilities(home_elo, away_elo)  # placeholder call shape reused below

    home_form = rolling_form(history, home["id"], match_date, venue="home")
    away_form = rolling_form(history, away["id"], match_date, venue="away")
    h2h = head_to_head(history, home["id"], away["id"], match_date)

    return {
        # Dixon-Coles baseline output, fed forward as features (not discarded):
        "dc_lambda_home": lambdas.lambda_home,
        "dc_lambda_away": lambdas.lambda_away,
        "dc_lambda_diff": lambdas.lambda_home - lambdas.lambda_away,
        # Elo:
        "elo_home": home_elo,
        "elo_away": away_elo,
        "elo_diff": home_elo - away_elo,
        # Rolling form (venue-specific):
        "home_form_ppg": home_form["ppg"],
        "home_form_gf": home_form["gf_per_game"],
        "home_form_ga": home_form["ga_per_game"],
        "away_form_ppg": away_form["ppg"],
        "away_form_gf": away_form["gf_per_game"],
        "away_form_ga": away_form["ga_per_game"],
        # Head-to-head:
        "h2h_home_win_rate": h2h["home_win_rate"],
        "h2h_draw_rate": h2h["draw_rate"],
        # Rest / fixture congestion:
        "home_rest_days": rest_days(match_date, home_last_match_date) or 7,
        "away_rest_days": rest_days(match_date, away_last_match_date) or 7,
        # Raw ratings, for models that want them directly:
        "home_attack": home["attack"], "home_defense": home["defense"],
        "away_attack": away["attack"], "away_defense": away["defense"],
    }


def build_training_frame(fixtures_with_results: list[dict], history: list[dict], teams_by_id: dict) -> pd.DataFrame:
    """
    Builds a full training DataFrame from a list of finished fixtures
    (each needs date/home_id/away_id/home_goals/away_goals) plus the same
    history list used as the lookback window. Walks chronologically so no
    fixture's features are built using data from after it was played —
    the single most important discipline for not leaking future
    information into a supposedly historical prediction (see build plan
    §6.3 on walk-forward validation; this is the row-level version of the
    same principle).
    """
    rows = []
    for fx in fixtures_with_results:
        home = teams_by_id.get(fx["home_id"], {"id": fx["home_id"], "attack": 60, "defense": 60, "home_adv": 55, "form": None})
        away = teams_by_id.get(fx["away_id"], {"id": fx["away_id"], "attack": 60, "defense": 60, "home_adv": 55, "form": None})
        row = build_feature_row(home, away, history, fx["date"])
        row["result"] = (
            "H" if fx["home_goals"] > fx["away_goals"]
            else "A" if fx["home_goals"] < fx["away_goals"]
            else "D"
        )
        row["home_goals"] = fx["home_goals"]
        row["away_goals"] = fx["away_goals"]
        rows.append(row)
    return pd.DataFrame(rows)

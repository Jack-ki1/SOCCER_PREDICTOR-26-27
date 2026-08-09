"""
Elo rating system.

Complements Dixon-Coles: the fitted attack/defense ratings in
config/constants.py (or, once Phase 2 is done, ratings fitted from real
historical results) are relatively slow-moving, updated on a training
cadence. Elo updates after every single match, so it captures momentum/
current form more responsively — the standard reason most serious football-
prediction pipelines carry both signals rather than picking one.

This is v2 in the build plan's model progression (§6.1) — not wired into
the live ensemble by default yet (see config/feature_weights.py's
ensemble_blend, which starts at 100% Dixon-Coles / 0% Elo). Bring it in
gradually once you've backtested that blending actually helps.
"""
from __future__ import annotations

DEFAULT_ELO = 1500.0
DEFAULT_K = 20.0          # standard chess/Elo update-speed constant; football implementations
                           # commonly use something in the 15-40 range depending on how reactive
                           # you want ratings to be — 20 is a reasonable, well-tested starting point
HOME_ELO_BONUS = 60.0      # a typical home-advantage adjustment in football Elo implementations
GOAL_DIFF_MULTIPLIER = True  # scale the K-factor update by margin of victory, not just win/loss


def expected_score(rating_a: float, rating_b: float) -> float:
    """Standard Elo expected-score formula: P(A beats B), continuous in [0, 1]."""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def _margin_multiplier(goal_diff: int) -> float:
    """
    Bigger wins move the rating more than a 1-0 squeaker — a common
    football-Elo refinement (used by, e.g., the World Football Elo
    Ratings project) over the plain chess formula, which only sees
    win/draw/loss.
    """
    if not GOAL_DIFF_MULTIPLIER:
        return 1.0
    gd = abs(goal_diff)
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11 + gd) / 8  # matches the commonly-cited World Football Elo formula shape


def update_ratings(
    home_rating: float, away_rating: float, home_goals: int, away_goals: int, k: float = DEFAULT_K,
) -> tuple[float, float]:
    """One match's Elo update. Returns (new_home_rating, new_away_rating)."""
    adjusted_home = home_rating + HOME_ELO_BONUS
    expected_home = expected_score(adjusted_home, away_rating)

    if home_goals > away_goals:
        actual_home = 1.0
    elif home_goals < away_goals:
        actual_home = 0.0
    else:
        actual_home = 0.5

    margin_mult = _margin_multiplier(home_goals - away_goals)
    delta = k * margin_mult * (actual_home - expected_home)

    return home_rating + delta, away_rating - delta


def elo_to_match_probabilities(home_rating: float, away_rating: float, draw_factor: float = 0.28) -> dict:
    """
    Rough 1X2 probabilities from Elo alone. Elo natively only gives a win
    probability for one side vs. the other (no draw concept) — draw_factor
    is a simple, commonly-used approximation that carves out a draw
    probability proportional to how close the two ratings are. This is
    intentionally cruder than the Dixon-Coles market_probabilities() output;
    Elo's value here is as an ensemble *input*, not a replacement.
    """
    p_home_or_away = expected_score(home_rating + HOME_ELO_BONUS, away_rating)
    # Closer ratings -> higher draw probability; scale by draw_factor.
    closeness = 1 - abs(p_home_or_away - 0.5) * 2  # 1.0 when evenly matched, 0.0 when a mismatch
    p_draw = draw_factor * closeness
    remaining = 1 - p_draw
    p_home = remaining * p_home_or_away
    p_away = remaining * (1 - p_home_or_away)
    return {"p_home": p_home, "p_draw": p_draw, "p_away": p_away}


def initialize_ratings(team_ids: list[str], base: float = DEFAULT_ELO) -> dict[str, float]:
    return {tid: base for tid in team_ids}


def run_elo_over_history(matches: list[dict], initial_ratings: dict[str, float] | None = None, k: float = DEFAULT_K) -> dict[str, float]:
    """
    Batch-process a chronologically-ordered list of finished matches
    (each a dict with home_id, away_id, home_goals, away_goals) into final
    Elo ratings. This is what scripts/fetch_historical_data.py +
    data/soccerdata_integration.py feed once real historical results are
    loaded — order matters here, so make sure `matches` is sorted by date
    before calling this.
    """
    ratings = dict(initial_ratings) if initial_ratings else {}
    for m in matches:
        h, a = m["home_id"], m["away_id"]
        ratings.setdefault(h, DEFAULT_ELO)
        ratings.setdefault(a, DEFAULT_ELO)
        ratings[h], ratings[a] = update_ratings(ratings[h], ratings[a], m["home_goals"], m["away_goals"], k=k)
    return ratings

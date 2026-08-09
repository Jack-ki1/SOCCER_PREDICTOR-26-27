"""
Dixon-Coles bivariate Poisson model.

This is a direct port of the validated engine from the React prototype
(matchLambdas / scoreMatrix / dcTau / marketProbs in the original
EPLPredictorDashboard.jsx) — same maths, same constants, ported to Python
so the exact same numbers come out of both, given the same inputs. That
was checked by hand during the prototype phase (probabilities summing to
1 across all 380 fixtures, clean-sheet probabilities in range, etc.) — see
`tests/test_probability_model.py` for the same checks as real pytest tests.

Reference: Dixon, M. & Coles, S. (1997), "Modelling Association Football
Scores and Inefficiencies in the Football Betting Market."
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, factorial

from config.constants import TEAMS
from config.feature_weights import DEFAULT_WEIGHTS

MAX_GOALS = 6  # grid is (MAX_GOALS+1) x (MAX_GOALS+1); tail beyond this renormalized in


def _avg(values: list[float]) -> float:
    return sum(values) / len(values)


def league_averages(teams: list[dict] | None = None) -> tuple[float, float]:
    """Mean attack/defense rating across the league — recompute whenever ratings change
    (e.g. after a live-data refresh), don't treat this as a frozen constant."""
    teams = teams or TEAMS
    return _avg([t["attack"] for t in teams]), _avg([t["defense"] for t in teams])


def alpha(team: dict, avg_attack: float) -> float:
    """Attack strength multiplier, relative to league average."""
    return team["attack"] / avg_attack


def beta(team: dict, avg_defense: float) -> float:
    """Defensive leakiness multiplier — higher beta = concedes more. Inverse relationship
    to the defense rating by design (a defense rating of 100 should suppress goals, not add them)."""
    return avg_defense / team["defense"]


def form_multiplier(team: dict, weight: float) -> float:
    """Recent-form nudge, ±15% at full weight for a team on a perfect run, neutral (1.0)
    for teams with no form history yet (newly promoted sides)."""
    form = team.get("form")
    if not form:
        return 1.0
    pts = sum(3 if r == "W" else 1 if r == "D" else 0 for r in form)
    score = pts / (3 * len(form))
    return 1 + (score - 0.5) * 0.3 * (weight / 100)


def dc_tau(x: int, y: int, lam: float, mu: float, rho: float) -> float:
    """Dixon-Coles low-score correlation adjustment — lifts/dampens the four
    low-scoring cells (0-0, 1-0, 0-1, 1-1) relative to plain independent Poisson."""
    if x == 0 and y == 0:
        return 1 - lam * mu * rho
    if x == 0 and y == 1:
        return 1 + lam * rho
    if x == 1 and y == 0:
        return 1 + mu * rho
    if x == 1 and y == 1:
        return 1 - rho
    return 1.0


def poisson_pmf(lam: float, k: int) -> float:
    return (lam ** k) * exp(-lam) / factorial(k)


@dataclass
class MatchLambdas:
    lambda_home: float
    lambda_away: float


def match_lambdas(
    home: dict, away: dict, weights: dict | None = None,
    teams: list[dict] | None = None,
    league_avgs: tuple[float, float] | None = None,
) -> MatchLambdas:
    """
    Expected goals for each side, given current ratings and engine weights.

    `league_avgs`, if given, pins (avg_attack, avg_defense) instead of
    recomputing from `teams`/module default — this matters for Monte Carlo:
    each simulated season perturbs individual teams' attack rating, but the
    *league-wide* average should stay fixed to the real baseline ratings for
    that to behave as "this team over/underperforms its true level," not
    "the whole league's average quietly drifts with the noise." See
    engine/monte_carlo.py.
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    avg_attack, avg_defense = league_avgs if league_avgs else league_averages(teams)

    home_boost = 1 + (w["home_advantage_weight"] / 100) * w["global_home_bonus"] * (0.6 + (home["home_adv"] / 100) * 0.8)
    away_damp = 1 - (w["home_advantage_weight"] / 100) * 0.05

    lam_home = (
        w["league_avg_home_goals"] * alpha(home, avg_attack) * beta(away, avg_defense)
        * home_boost * form_multiplier(home, w["recent_form_weight"])
    )
    lam_away = (
        w["league_avg_away_goals"] * alpha(away, avg_attack) * beta(home, avg_defense)
        * away_damp * form_multiplier(away, w["recent_form_weight"])
    )
    return MatchLambdas(
        lambda_home=min(4.2, max(0.15, lam_home)),
        lambda_away=min(4.2, max(0.15, lam_away)),
    )


def score_matrix(lambda_home: float, lambda_away: float, rho: float, max_goals: int = MAX_GOALS) -> list[list[float]]:
    """(max_goals+1) x (max_goals+1) grid of P(home=x, away=y), Dixon-Coles adjusted, renormalized to sum to 1."""
    grid = [[0.0] * (max_goals + 1) for _ in range(max_goals + 1)]
    total = 0.0
    for x in range(max_goals + 1):
        for y in range(max_goals + 1):
            p = max(0.0, dc_tau(x, y, lambda_home, lambda_away, rho) * poisson_pmf(lambda_home, x) * poisson_pmf(lambda_away, y))
            grid[x][y] = p
            total += p
    return [[p / total for p in row] for row in grid]


@dataclass
class MarketProbabilities:
    p_home: float
    p_draw: float
    p_away: float
    p_btts: float
    p_over_2_5: float
    p_under_2_5: float
    p_clean_sheet_home: float
    p_clean_sheet_away: float
    top_scorelines: list[tuple[str, float]] = field(default_factory=list)


def market_probabilities(grid: list[list[float]]) -> MarketProbabilities:
    p_home = p_draw = p_away = p_btts = p_over = cs_home = cs_away = 0.0
    scorelines: list[tuple[str, float]] = []
    for x, row in enumerate(grid):
        for y, p in enumerate(row):
            if x > y:
                p_home += p
            elif x == y:
                p_draw += p
            else:
                p_away += p
            if x > 0 and y > 0:
                p_btts += p
            if x + y >= 3:
                p_over += p
            if y == 0:
                cs_home += p
            if x == 0:
                cs_away += p
            scorelines.append((f"{x}-{y}", p))
    scorelines.sort(key=lambda s: s[1], reverse=True)
    return MarketProbabilities(
        p_home=p_home, p_draw=p_draw, p_away=p_away,
        p_btts=p_btts, p_over_2_5=p_over, p_under_2_5=1 - p_over,
        p_clean_sheet_home=cs_home, p_clean_sheet_away=cs_away,
        top_scorelines=scorelines[:5],
    )


@dataclass
class Prediction:
    home_id: str
    away_id: str
    lambda_home: float
    lambda_away: float
    grid: list[list[float]]
    market: MarketProbabilities
    captain_score_home: float  # FPL-style: expected goals weighted toward the more-likely winner
    captain_score_away: float


def predict_match(home: dict, away: dict, weights: dict | None = None, teams: list[dict] | None = None) -> Prediction:
    """End-to-end single-match prediction — the Python equivalent of the JSX's predictMatch()."""
    lambdas = match_lambdas(home, away, weights, teams)
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    grid = score_matrix(lambdas.lambda_home, lambdas.lambda_away, w["dixon_coles_rho"])
    market = market_probabilities(grid)
    captain_home = lambdas.lambda_home * (0.4 + 0.6 * market.p_home)
    captain_away = lambdas.lambda_away * (0.4 + 0.6 * market.p_away)
    return Prediction(
        home_id=home["id"], away_id=away["id"],
        lambda_home=lambdas.lambda_home, lambda_away=lambdas.lambda_away,
        grid=grid, market=market,
        captain_score_home=captain_home, captain_score_away=captain_away,
    )

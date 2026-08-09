"""
Monte Carlo season simulation.

When this engine was ported from the original React/JS prototype, that
prototype had a real, measured bug: without any season-level jitter, its
Monte Carlo simulation gave the strongest team ~98%+ title "certainty",
which is unrealistically overconfident for a pre-season model.

Porting it here surfaced something worth recording rather than quietly
fixing and moving on: **this Python engine's un-jittered Monte Carlo
average already converges to the closed-form expected-points value**
(verified directly — sum of per-fixture P(win)*3 + P(draw)*1 across a
season matches the simulated average almost exactly, see the test suite).
That's the correctness property a Monte Carlo simulator is supposed to
have. The JS prototype's simulate-season code path likely diverged from
its own single-match prediction code path in some way that wasn't fully
tracked down before this rewrite — this port uses one shared
`match_lambdas()` for both, which structurally can't drift apart the same
way.

Net effect: this version needed much lighter jitter (0.12 vs the
prototype's 0.25) to land in a realistic range. The jitter itself is kept
regardless, because real pre-season uncertainty (injuries, new signings
bedding in, a summer of hype that doesn't translate) is worth modeling on
its own merits, not just as a patch for a bug that isn't present here.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from config.constants import REAL_MATCHWEEK_1, SCHEDULE_ORDER, SEASON_ROUNDS, TEAMS, TEAMS_BY_ID
from config.feature_weights import DEFAULT_WEIGHTS
from engine.probability_model import league_averages, match_lambdas, poisson_pmf


def seeded_random(key: str) -> float:
    """Deterministic pseudo-random float in [0, 1), reproducible across runs
    given the same key — same approach as the JS prototype's seededRandom()."""
    h = hashlib.sha256(key.encode()).hexdigest()
    return (int(h[:8], 16) % 100000) / 100000


def poisson_sample_from_uniform(lam: float, u: float) -> int:
    """Inverse-CDF Poisson sampling from a single uniform draw — avoids pulling
    in a full RNG dependency chain, and stays deterministic given the same u."""
    p = poisson_pmf(lam, 0)
    cum = p
    k = 0
    while u > cum and k < 25:
        k += 1
        p *= lam / k
        cum += p
    return k


@dataclass
class Fixture:
    home: str
    away: str
    round: int


def generate_schedule(order: list[str] | None = None) -> list[Fixture]:
    """
    Standard double round-robin (circle method), seeded so round 1 reproduces
    the real confirmed Matchweek 1 fixtures. Produces 38 rounds x 10 matches
    = 380 fixtures, every pair meeting exactly twice (once each venue).
    """
    order = order or SCHEDULE_ORDER
    n = len(order)
    half = n // 2
    arr = list(order)
    rounds: list[list[tuple[str, str]]] = []

    for r in range(n - 1):
        matches = []
        for i in range(half):
            a, b = arr[i], arr[n - 1 - i]
            matches.append((a, b) if r % 2 == 0 else (b, a))
        rounds.append(matches)
        arr = [arr[0], arr[-1]] + arr[1:-1]

    second_leg = [[(away, home) for home, away in rd] for rd in rounds]
    all_rounds = rounds + second_leg

    fixtures = []
    for round_idx, matches in enumerate(all_rounds):
        for home, away in matches:
            fixtures.append(Fixture(home=home, away=away, round=round_idx + 1))
    return fixtures


ALL_FIXTURES = generate_schedule()

SEASON_JITTER_DEFAULT = DEFAULT_WEIGHTS["season_jitter"]


@dataclass
class TeamProjection:
    club_id: str
    title_prob: float
    top4_prob: float
    releg_prob: float
    avg_points: float
    avg_goal_diff: float


def simulate_season(
    weights: dict | None = None,
    n_sims: int = 300,
    seed: str = "season-v1",
    teams: list[dict] | None = None,
    fixtures: list[Fixture] | None = None,
) -> list[TeamProjection]:
    """
    Simulate the full 380-fixture season n_sims times. Applies a seeded
    per-team attack-strength jitter once per simulated season (not per
    match) to represent real pre-season uncertainty (injuries, new signings
    bedding in, a summer of hype that doesn't translate) that a pure
    match-to-match Poisson model can't see on its own — see the module
    docstring for why this matters.
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    teams = teams or TEAMS
    fixtures = fixtures or ALL_FIXTURES
    team_ids = [t["id"] for t in teams]
    by_id = {t["id"]: t for t in teams}

    position_counts = {tid: [0] * len(team_ids) for tid in team_ids}
    points_sum = {tid: 0 for tid in team_ids}
    gd_sum = {tid: 0 for tid in team_ids}

    jitter_pct = w.get("season_jitter", SEASON_JITTER_DEFAULT)
    # Pin the league-wide average to the BASE ratings, held fixed for the whole
    # simulation — only individual teams' attack jitters, not the shared baseline.
    # See the note on match_lambdas(league_avgs=...) for why this matters.
    base_league_avgs = league_averages(teams)

    for s in range(n_sims):
        jittered_teams = {}
        for tid in team_ids:
            u = seeded_random(f"{seed}-{s}-{tid}-jitter")
            base = by_id[tid]
            jittered_teams[tid] = {**base, "attack": base["attack"] * (1 + (u - 0.5) * 2 * jitter_pct)}

        pts = {tid: 0 for tid in team_ids}
        gf = {tid: 0 for tid in team_ids}
        ga = {tid: 0 for tid in team_ids}

        for idx, fx in enumerate(fixtures):
            home, away = jittered_teams[fx.home], jittered_teams[fx.away]
            lambdas = match_lambdas(home, away, w, league_avgs=base_league_avgs)
            u_h = seeded_random(f"{seed}-{idx}-{s}-h")
            u_a = seeded_random(f"{seed}-{idx}-{s}-a")
            g_h = poisson_sample_from_uniform(lambdas.lambda_home, u_h)
            g_a = poisson_sample_from_uniform(lambdas.lambda_away, u_a)

            gf[fx.home] += g_h; ga[fx.home] += g_a
            gf[fx.away] += g_a; ga[fx.away] += g_h
            if g_h > g_a:
                pts[fx.home] += 3
            elif g_h < g_a:
                pts[fx.away] += 3
            else:
                pts[fx.home] += 1; pts[fx.away] += 1

        ranking = sorted(
            team_ids,
            key=lambda tid: (pts[tid], gf[tid] - ga[tid], gf[tid]),
            reverse=True,
        )
        for pos, tid in enumerate(ranking):
            position_counts[tid][pos] += 1
            points_sum[tid] += pts[tid]
            gd_sum[tid] += gf[tid] - ga[tid]

    results = []
    for tid in team_ids:
        pc = position_counts[tid]
        results.append(TeamProjection(
            club_id=tid,
            title_prob=pc[0] / n_sims,
            top4_prob=sum(pc[:4]) / n_sims,
            releg_prob=sum(pc[17:20]) / n_sims,
            avg_points=points_sum[tid] / n_sims,
            avg_goal_diff=gd_sum[tid] / n_sims,
        ))
    results.sort(key=lambda r: r.avg_points, reverse=True)
    return results

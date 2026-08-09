"""
Regression tests for engine/monte_carlo.py — schedule integrity (the
double round-robin must produce exactly 380 fixtures with every pair
meeting exactly twice) and calibration sanity (no team should show
unrealistic title-probability overconfidence — this is the specific
regression test for the ~98% overconfidence bug found and fixed during
this project's build, see the module's docstring).
"""
import pytest

from config.constants import REAL_MATCHWEEK_1
from engine.monte_carlo import ALL_FIXTURES, simulate_season


def test_schedule_has_380_fixtures():
    assert len(ALL_FIXTURES) == 380


def test_every_pair_meets_exactly_twice():
    pair_counts = {}
    for f in ALL_FIXTURES:
        key = tuple(sorted([f.home, f.away]))
        pair_counts[key] = pair_counts.get(key, 0) + 1
    assert len(pair_counts) == 190
    assert all(count == 2 for count in pair_counts.values())


def test_every_team_plays_19_home_19_away():
    home_counts, away_counts = {}, {}
    for f in ALL_FIXTURES:
        home_counts[f.home] = home_counts.get(f.home, 0) + 1
        away_counts[f.away] = away_counts.get(f.away, 0) + 1
    assert all(count == 19 for count in home_counts.values())
    assert all(count == 19 for count in away_counts.values())


def test_matchweek_1_matches_real_confirmed_fixtures():
    mw1 = [(f.home, f.away) for f in ALL_FIXTURES if f.round == 1]
    assert sorted(mw1) == sorted(REAL_MATCHWEEK_1)


def test_title_probabilities_sum_to_one_across_league():
    results = simulate_season(n_sims=100, seed="test-sum")
    total = sum(r.title_prob for r in results)
    assert total == pytest.approx(1.0, abs=0.02)


def test_no_team_shows_unrealistic_title_overconfidence():
    """
    Regression test for the calibration bug found during this project's
    build: without season-level jitter, the strongest team showed ~98%+
    title probability, which is unrealistic for a pre-season model. This
    test fails loudly if that regresses.
    """
    results = simulate_season(n_sims=300, seed="test-calibration")
    top_team = results[0]
    assert top_team.title_prob < 0.85, (
        f"{top_team.club_id} shows {top_team.title_prob:.1%} title probability — "
        "this is the exact overconfidence pattern the season_jitter fix addresses. "
        "Check config/feature_weights.py's season_jitter hasn't been reset to 0."
    )


def test_relegation_probabilities_favour_weaker_teams():
    results = simulate_season(n_sims=300, seed="test-releg")
    # the three promoted/weakest sides should show meaningfully higher relegation risk
    # than the top of the table
    top_team = results[0]
    weakest_by_rating = min(results, key=lambda r: r.avg_points)
    assert weakest_by_rating.releg_prob > top_team.releg_prob

"""
Regression tests for engine/probability_model.py — codifies the manual
validation done while building this engine (probabilities summing to 1
across all 380 fixture combinations, clean-sheet probabilities in range).
"""
import pytest

from config.constants import TEAMS
from engine.probability_model import predict_match


def test_single_prediction_matches_known_values():
    """Arsenal vs Coventry — cross-checked by hand against the original
    prototype during development. If this changes, something in the
    engine's maths has changed, intentionally or not."""
    ars = next(t for t in TEAMS if t["id"] == "ars")
    cov = next(t for t in TEAMS if t["id"] == "cov")
    p = predict_match(ars, cov)

    assert p.lambda_home == pytest.approx(3.18, abs=0.01)
    assert p.lambda_away == pytest.approx(0.69, abs=0.01)
    assert p.market.p_home == pytest.approx(0.84, abs=0.01)


@pytest.mark.parametrize("home", TEAMS)
@pytest.mark.parametrize("away", TEAMS)
def test_all_fixture_combinations_are_valid(home, away):
    if home["id"] == away["id"]:
        pytest.skip("a team doesn't play itself")
    p = predict_match(home, away)

    total = p.market.p_home + p.market.p_draw + p.market.p_away
    assert total == pytest.approx(1.0, abs=1e-6)
    assert 0 < p.lambda_home < 5
    assert 0 < p.lambda_away < 5
    assert 0 <= p.market.p_clean_sheet_home <= 1
    assert 0 <= p.market.p_clean_sheet_away <= 1
    assert 0 <= p.market.p_btts <= 1


def test_score_matrix_sums_to_one():
    home, away = TEAMS[0], TEAMS[1]
    p = predict_match(home, away)
    grid_sum = sum(sum(row) for row in p.grid)
    assert grid_sum == pytest.approx(1.0, abs=1e-6)


def test_home_favourite_gets_higher_win_probability():
    """Arsenal (best-rated) at home vs a promoted side should be a clear favourite."""
    ars = next(t for t in TEAMS if t["id"] == "ars")
    cov = next(t for t in TEAMS if t["id"] == "cov")
    p = predict_match(ars, cov)
    assert p.market.p_home > p.market.p_away
    assert p.market.p_home > 0.5

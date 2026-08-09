"""
Fixture-congestion / squad-fatigue model.

Analogous to the F1 project's tire_model.py — a degradation curve applied
over "distance," except the distance here is measured in days-since-last-
match and midweek-European-fixture load rather than laps. This is the
concrete implementation of the "9 clubs in Europe, rotation risk" factor
that was flagged as unmodeled throughout the React prototype — it's built
here, in a project structure that can actually carry a rest-days feature
through to the ML ensemble (engine/feature_engineering.py).
"""
from __future__ import annotations

from datetime import date


def rest_days(match_date: date, previous_match_date: date | None) -> int | None:
    if previous_match_date is None:
        return None
    return (match_date - previous_match_date).days


def fatigue_multiplier(days_rest: int | None, played_midweek_european_fixture: bool = False) -> float:
    """
    Multiplicative dampener on attack rating. Calibrated loosely against
    the general finding in sports-science / football-analytics literature
    that short rest (<= 3 days) measurably increases injury risk and
    reduces high-intensity output — treat the exact numbers here as
    reasonable illustrative defaults, tune via
    scripts/calibrate_probabilities.py once you have enough real
    congested-fixture results to check against.
    """
    if days_rest is None:
        mult = 1.0
    elif days_rest <= 2:
        mult = 0.90
    elif days_rest == 3:
        mult = 0.94
    elif days_rest <= 5:
        mult = 0.98
    else:
        mult = 1.0

    if played_midweek_european_fixture:
        mult *= 0.97  # additional travel/intensity load on top of pure rest-days

    return mult


def apply_fatigue(team: dict, days_rest: int | None, played_midweek_european_fixture: bool = False) -> dict:
    mult = fatigue_multiplier(days_rest, played_midweek_european_fixture)
    return {**team, "attack": team["attack"] * mult}

"""
Injury / squad-disruption model.

Analogous to the F1 project's safety_car_model.py in spirit — modeling a
disruptive event that shifts win probability mid-context — but the soccer
version is about known pre-match information (injuries, suspensions, red
cards) rather than an in-race random event. There is no free, reliable,
structured injury-data API wired in by default; this module defines the
adjustment mechanism so that once you have a source (manually curated,
or a scraped team-news page), it has somewhere to plug in.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SquadAvailability:
    """
    key_players_out: count of first-team-regulars missing (however you
    define "key" — simplest is top-11-by-minutes-played last season).
    Weight the goalkeeper/defensive-line absences separately from
    attacking ones, since they affect different sides of the Poisson
    model differently.
    """
    key_attackers_out: int = 0
    key_defenders_out: int = 0
    key_midfielders_out: int = 0
    suspensions: int = 0
    notes: list[str] = field(default_factory=list)


def availability_adjustment(availability: SquadAvailability) -> tuple[float, float]:
    """
    Returns (attack_multiplier, defense_multiplier) to apply to a team's
    ratings before feeding them into engine/probability_model.py. Kept
    deliberately conservative — a single missing player rarely swings a
    match as much as fans expect; these are per-absence percentage nudges,
    capped so a chaotic team-news day can't produce an absurd rating.
    """
    attack_mult = 1.0 - min(0.25, 0.04 * availability.key_attackers_out + 0.015 * availability.key_midfielders_out)
    defense_mult = 1.0 - min(0.25, 0.05 * availability.key_defenders_out + 0.03 * availability.suspensions)
    return attack_mult, defense_mult


def apply_to_team(team: dict, availability: SquadAvailability) -> dict:
    """Returns a shallow-copied team dict with adjusted attack/defense — doesn't mutate the input."""
    attack_mult, defense_mult = availability_adjustment(availability)
    return {
        **team,
        "attack": team["attack"] * attack_mult,
        "defense": team["defense"] * defense_mult,
    }

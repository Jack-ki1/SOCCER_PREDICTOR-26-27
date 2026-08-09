"""
Tunable engine weights — the Python-side equivalents of the three sliders
in the React dashboard's Model Lab tab, plus the ensemble blend weights
that get used once engine/ensemble_predictor.py has more than one model
to blend.

Keeping these in one file (rather than scattered magic numbers across
engine/*.py) is what makes scripts/optimize_weights.py possible — it can
import this module, try different values, and re-run
engine/benchmark_suite.py without touching any model code.
"""

DEFAULT_WEIGHTS = {
    # --- Dixon-Coles / v1 engine ---
    "home_advantage_weight": 55,   # 0-100, same scale/meaning as the JSX slider
    "recent_form_weight": 50,      # 0-100
    "dixon_coles_rho": -0.11,      # low-score correlation adjustment, literature-typical range -0.25..0.05

    # --- Season simulation ---
    "season_jitter": 0.12,         # ± attack-strength wobble per simulated season, representing
                                    # real pre-season uncertainty (injuries, new signings, etc.)
                                    # NOTE: this is lighter than the prototype's 0.25. When this
                                    # engine was ported from the original JS prototype, testing
                                    # showed the Python version's un-jittered Monte Carlo average
                                    # already converges exactly to the closed-form expected-points
                                    # value (verified: sum of per-fixture P(win)*3+P(draw)*1 across
                                    # a season matches the simulated average to within noise) — the
                                    # ~98% title-probability overconfidence bug found in the JS
                                    # prototype does not reproduce here, most likely because that
                                    # version had lambdas diverge between its season-simulation and
                                    # single-match code paths in a way this port's shared
                                    # match_lambdas() call can't. A modest jitter is kept anyway,
                                    # because real pre-season uncertainty is a legitimate thing to
                                    # model on its own merits — see scripts/calibrate_probabilities.py
                                    # before changing this further.

    # --- Ensemble blend (v2+, once Elo/ML models exist) ---
    "ensemble_blend": {
        "dixon_coles": 1.0,        # v1: 100% Dixon-Coles, others at 0 until they're validated
        "elo": 0.0,
        "ml_ensemble": 0.0,
    },

    # --- League-average goal baselines (illustrative until fitted from real data) ---
    "league_avg_home_goals": 1.55,
    "league_avg_away_goals": 1.30,
    "global_home_bonus": 0.20,
}


def get_weights(overrides: dict | None = None) -> dict:
    """Merge overrides on top of DEFAULT_WEIGHTS without mutating the default."""
    weights = {**DEFAULT_WEIGHTS}
    if overrides:
        weights.update({k: v for k, v in overrides.items() if k != "ensemble_blend"})
        if "ensemble_blend" in overrides:
            weights["ensemble_blend"] = {**DEFAULT_WEIGHTS["ensemble_blend"], **overrides["ensemble_blend"]}
    return weights

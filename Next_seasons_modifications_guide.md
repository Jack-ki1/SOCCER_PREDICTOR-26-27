# Next Season's Modifications Guide

This file is meant to be filled in progressively as you actually run this
project through the 2026/27 season — it's a placeholder structure now,
not speculative advice, because the real lessons only exist after Phase
0-5 of the build plan have actually run against a live season. Update
each section as you learn the specific thing, rather than trying to guess
it all upfront.

## 1. Fixture data

- [ ] Once the 2026/27 official fixture list is fully released (in stages
      through the season), replace `engine/monte_carlo.py`'s generated
      round-robin for Matchweeks 2-38 with the real released fixtures.
- [ ] Record here whether FPL's `/fixtures/` endpoint shape held stable
      all season, or changed — this determines how defensive
      `data/fpl_client.py`'s `_require_keys` checks need to be next season.

## 2. Ratings

- [ ] Note here once `scripts/fetch_historical_data.py` has pulled a full
      season of real results: did the Dixon-Coles fit
      (`engine/probability_model.py`) meaningfully outperform the
      illustrative `config/constants.py` ratings on
      `scripts/measure_accuracy.py`? By how much?
- [ ] Record the final `config/feature_weights.py` values
      `scripts/optimize_weights.py` converged on, and whether they held
      stable across the season or needed mid-season re-tuning.

## 3. ML ensemble

- [ ] Which models in `engine/ml_models.py`'s zoo actually beat the
      Dixon-Coles-alone baseline on `engine/benchmark_suite.py`'s
      walk-forward check? Record win/loss per model — the roster should
      shrink to what's proven, not just accumulate more models.
- [ ] Record the final `ensemble_blend` weights
      (`config/feature_weights.py`) once v3 is actually promoted to live.

## 4. Season-jitter calibration

- [ ] `engine/monte_carlo.py`'s `season_jitter` default (0.12) was chosen
      from a pre-season sanity check, not a full season of validation.
      Once real results exist, check whether the simulated title/top-4/
      relegation probabilities from early in the season tracked reality
      reasonably, or need retuning.

## 5. Data source reliability

- [ ] FPL API: any outages, shape changes, or rate-limiting encountered?
- [ ] API-Football: did the 100 req/day free tier prove sufficient as a
      cross-check, or did you need to upgrade / reduce its usage?
- [ ] soccerdata (FBref): any scrape breakages across the season? FBref
      occasionally changes page structure, which soccerdata's maintainers
      usually patch quickly, but note any gaps here.

## 6. What broke, and how it was fixed

Keep a running log here — this is the single most useful section for
whoever (including future you) works on this project for 2027/28.

| Date | What broke | Root cause | Fix |
|---|---|---|---|
| | | | |

## 7. New free data sources worth evaluating

Revisit `EPL_PREDICTOR_2026_BUILD_PLAN.md` §2's verdict table each
off-season — API landscapes shift. In particular:
- [ ] Re-check whether Sportmonks' free tier covers the EPL (unconfirmed
      as of this build — see build plan §2).
- [ ] Check whether any new free, no-key APIs have emerged.

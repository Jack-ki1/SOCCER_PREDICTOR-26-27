"""
CLI: one-time (+ yearly top-up) historical data backfill via soccerdata
(FBref). See data/soccerdata_integration.py and build plan §2/§4 for why
this is the primary historical/training data source.

Usage: python scripts/fetch_historical_data.py [--seasons 2223 2324 2425 2526]

Requires network access to fbref.com (not available in every sandboxed
environment — this is expected to run on your own machine/server, not
necessarily in CI).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.api_settings import SOCCERDATA_TRAIN_SEASONS  # noqa: E402
from data.soccerdata_integration import (  # noqa: E402
    SoccerdataError, get_schedule, schedule_to_history_format,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seasons", nargs="+", default=SOCCERDATA_TRAIN_SEASONS)
    parser.add_argument("--out", default="historical_matches.json")
    args = parser.parse_args()

    print(f"Fetching FBref schedule for seasons {args.seasons}...")
    try:
        schedule_df = get_schedule(args.seasons)
    except SoccerdataError as exc:
        print(f"Failed: {exc}")
        print("This needs real network access to fbref.com — expected to fail in a sandboxed CI environment.")
        sys.exit(1)

    history = schedule_to_history_format(schedule_df)
    print(f"Parsed {len(history)} finished matches.")

    import json
    with open(args.out, "w") as f:
        json.dump([{**row, "date": row["date"].isoformat()} for row in history], f, indent=2)
    print(f"Wrote {args.out} — feed this into engine/feature_engineering.py's training pipeline "
          "or database/models.py via a small loader script.")


if __name__ == "__main__":
    main()

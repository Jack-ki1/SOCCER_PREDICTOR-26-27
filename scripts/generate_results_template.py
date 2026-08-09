"""
CLI: generates a blank results-entry spreadsheet (one row per fixture) for
manually tracking real scores if you're not relying on automated ingestion
for a given stretch — e.g. filling in gaps, or bootstrapping before
data/live_updater.py has run for the first time.

Usage: python scripts/generate_results_template.py [--matchweek 1] [--out results_template.xlsx]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import openpyxl  # noqa: E402

from data.calendar_2026 import get_fixtures  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matchweek", type=int, default=None, help="Omit for the full season")
    parser.add_argument("--out", default="results_template.xlsx")
    args = parser.parse_args()

    fixtures = get_fixtures(args.matchweek)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Results"
    ws.append(["Matchweek", "Home", "Away", "Home Goals", "Away Goals", "Notes"])
    for f in fixtures:
        ws.append([f["round"], f["home_name"], f["away_name"], "", "", ""])

    for col, width in zip("ABCDEF", [11, 22, 22, 12, 12, 30]):
        ws.column_dimensions[col].width = width

    wb.save(args.out)
    print(f"Wrote {len(fixtures)} fixture row(s) to {args.out}")
    print("Fill in Home Goals / Away Goals, then load back in via a small script against "
          "data.season_2026.record_result() — or extend this script to read the file back in directly.")


if __name__ == "__main__":
    main()

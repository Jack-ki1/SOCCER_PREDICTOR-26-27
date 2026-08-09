"""
CLI: initialize/migrate the database and seed illustrative data.
Usage: python scripts/migrate_db.py [--force]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.migrations import run_migrations, seed  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Re-seed even if data already exists")
    args = parser.parse_args()

    print("Running migrations...")
    run_migrations()
    print("Seeding clubs, ratings, and Matchweek 1 fixtures...")
    summary = seed(force=args.force)
    print(f"Done: {summary}")


if __name__ == "__main__":
    main()

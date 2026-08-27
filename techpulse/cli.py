"""
cli.py
------
Command-line entrypoint to run the pipeline without the API.

Usage:
    python -m techpulse.cli --limit 20 --db techpulse.db
"""

from __future__ import annotations

import argparse
import logging
import sys

from techpulse.pipeline import run_pipeline


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch, summarize, and store top Hacker News stories.")
    parser.add_argument(
        "--limit", type=int, default=20, help="Number of top stories to process (default: 20)"
    )
    parser.add_argument("--db", type=str, default="techpulse.db", help="Path to the SQLite database file")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    processed = run_pipeline(limit=args.limit, db_path=args.db)
    print(f"Done. Processed {processed} stories into '{args.db}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
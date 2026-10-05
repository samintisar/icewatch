"""Command-line entry point: `icewatch <command>`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from icewatch.moneypuck import download_shots
from icewatch.nhl_api import NHLClient
from icewatch.parse import parse_events

DATA_DIR = Path("data")


def cmd_moneypuck(args: argparse.Namespace) -> None:
    for season in args.seasons:
        path = download_shots(season, DATA_DIR / "raw" / "moneypuck")
        print(f"{season}: {path}")


def cmd_game(args: argparse.Namespace) -> None:
    with NHLClient() as client:
        pbp = client.play_by_play(args.game_id)
    if pbp is None:
        raise SystemExit(f"game {args.game_id} not found")
    events = parse_events(pbp)
    print(events.to_string(max_rows=args.rows))


def cmd_backfill(args: argparse.Namespace) -> None:
    """Save raw play-by-play JSON and a parsed events parquet for one season."""
    raw_dir = DATA_DIR / "raw" / "pbp" / str(args.season)
    raw_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    with NHLClient() as client:
        for game_id, pbp in client.iter_season_play_by_play(args.season, limit=args.limit):
            (raw_dir / f"{game_id}.json").write_text(json.dumps(pbp))
            frames.append(parse_events(pbp))
            print(f"\r{len(frames)} games", end="", flush=True)
    print()
    if not frames:
        raise SystemExit("no games found")
    out = DATA_DIR / "processed" / f"events_{args.season}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(frames, ignore_index=True).to_parquet(out, index=False)
    print(f"wrote {out}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="icewatch")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("moneypuck", help="download MoneyPuck shot data")
    p.add_argument("seasons", nargs="+", type=int, help="season start years, e.g. 2023 2024")
    p.set_defaults(func=cmd_moneypuck)

    p = sub.add_parser("game", help="print parsed play-by-play for one game")
    p.add_argument("game_id", type=int, help="e.g. 2024020001")
    p.add_argument("--rows", type=int, default=40)
    p.set_defaults(func=cmd_game)

    p = sub.add_parser("backfill", help="download and parse a full regular season")
    p.add_argument("season", type=int, help="season start year, e.g. 2024")
    p.add_argument("--limit", type=int, help="only the first N games (for testing)")
    p.set_defaults(func=cmd_backfill)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

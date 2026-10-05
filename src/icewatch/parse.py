"""Turn raw NHL play-by-play JSON into flat event rows for modeling."""

from __future__ import annotations

import pandas as pd

PERIOD_SECONDS = 20 * 60
FINAL_STATES = {"FINAL", "OFF"}


def clock_to_seconds(clock: str) -> int:
    minutes, seconds = clock.split(":")
    return int(minutes) * 60 + int(seconds)


def game_seconds_elapsed(period: int, time_in_period: str) -> int:
    """Seconds since puck drop. Overtime continues from 3600."""
    return (period - 1) * PERIOD_SECONDS + clock_to_seconds(time_in_period)


def home_won(pbp: dict) -> bool | None:
    """Final outcome, or None if the game isn't finished."""
    if pbp.get("gameState") not in FINAL_STATES:
        return None
    return pbp["homeTeam"]["score"] > pbp["awayTeam"]["score"]


def parse_events(pbp: dict) -> pd.DataFrame:
    """One row per play, carrying the running score so each row is a game state."""
    home_id = pbp["homeTeam"]["id"]
    home_score = away_score = 0
    rows = []
    for play in sorted(pbp.get("plays", []), key=lambda p: p.get("sortOrder", 0)):
        details = play.get("details", {})
        period = play["periodDescriptor"]["number"]
        if play["typeDescKey"] == "goal":
            home_score = details.get("homeScore", home_score)
            away_score = details.get("awayScore", away_score)
        owner = details.get("eventOwnerTeamId")
        rows.append(
            {
                "game_id": pbp["id"],
                "event_id": play["eventId"],
                "period": period,
                "period_type": play["periodDescriptor"].get("periodType"),
                "seconds_elapsed": game_seconds_elapsed(period, play["timeInPeriod"]),
                "event_type": play["typeDescKey"],
                "team_id": owner,
                "is_home_event": None if owner is None else owner == home_id,
                "home_score": home_score,
                "away_score": away_score,
                "situation_code": play.get("situationCode"),
                "x": details.get("xCoord"),
                "y": details.get("yCoord"),
                "shot_type": details.get("shotType"),
            }
        )
    df = pd.DataFrame(rows)
    df["home_won"] = home_won(pbp)
    return df

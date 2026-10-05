import json
from pathlib import Path

import pytest

from icewatch.parse import game_seconds_elapsed, home_won, parse_events

FIXTURE = Path(__file__).parent / "fixtures" / "pbp_2024020001.json"


@pytest.fixture
def pbp():
    return json.loads(FIXTURE.read_text())


def test_game_seconds_elapsed():
    assert game_seconds_elapsed(1, "00:00") == 0
    assert game_seconds_elapsed(2, "05:30") == 1530
    assert game_seconds_elapsed(4, "01:00") == 3660


def test_home_won(pbp):
    # NJD (away) beat BUF 4-1.
    assert home_won(pbp) is False
    assert home_won({**pbp, "gameState": "LIVE"}) is None


def test_parse_events(pbp):
    events = parse_events(pbp)
    assert len(events) == len(pbp["plays"])
    assert events["seconds_elapsed"].is_monotonic_increasing
    assert set(events["home_won"]) == {False}

    first_goal = events[events["event_type"] == "goal"].iloc[0]
    assert (first_goal["away_score"], first_goal["home_score"]) == (1, 0)
    assert first_goal["is_home_event"] == False  # noqa: E712 (numpy bool)

    # The score carries forward to later events.
    assert events.iloc[-1]["away_score"] >= 1

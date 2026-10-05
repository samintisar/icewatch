"""Client for the public NHL web API (api-web.nhle.com).

The API is unofficial and undocumented, so keep requests polite: one client,
retries with backoff, and a small delay between bulk requests.
"""

from __future__ import annotations

import time
from datetime import date

import httpx

BASE_URL = "https://api-web.nhle.com/v1"
REGULAR_SEASON = 2
# 32 teams x 82 games / 2 = 1312 regular-season games per season.
GAMES_PER_SEASON = 1312


class NHLClient:
    def __init__(self, timeout: float = 20.0, retries: int = 3, delay: float = 0.25):
        self._http = httpx.Client(
            base_url=BASE_URL,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "icewatch (github.com/samintisar/icewatch)"},
        )
        self.retries = retries
        self.delay = delay

    def __enter__(self) -> NHLClient:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def _get(self, path: str) -> dict | None:
        """GET a JSON endpoint. Returns None on 404 (e.g. a game id that doesn't exist)."""
        for attempt in range(self.retries):
            try:
                resp = self._http.get(path)
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                return resp.json()
            except (httpx.TransportError, httpx.HTTPStatusError):
                if attempt == self.retries - 1:
                    raise
                time.sleep(2**attempt)
        return None

    def schedule(self, day: date | None = None) -> dict:
        """The week of games starting at `day` (today if omitted)."""
        return self._get(f"/schedule/{day.isoformat() if day else 'now'}") or {}

    def play_by_play(self, game_id: int) -> dict | None:
        return self._get(f"/gamecenter/{game_id}/play-by-play")

    def iter_season_play_by_play(self, season_start_year: int, limit: int | None = None):
        """Yield (game_id, play_by_play) for every regular-season game of a season.

        Game ids follow {start_year}{game_type:02d}{game_number:04d}, e.g. 2024020001.
        """
        last = min(limit or GAMES_PER_SEASON, GAMES_PER_SEASON)
        for number in range(1, last + 1):
            game_id = int(f"{season_start_year}{REGULAR_SEASON:02d}{number:04d}")
            pbp = self.play_by_play(game_id)
            if pbp is not None:
                yield game_id, pbp
            time.sleep(self.delay)

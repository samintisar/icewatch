"""Download MoneyPuck's historical shot data.

MoneyPuck data is free for non-commercial use and must be credited to
MoneyPuck.com wherever it is shown. Files are never committed to this repo.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import httpx

SHOTS_URL = "https://peter-tanner.com/moneypuck/downloads/shots_{season}.zip"


def download_shots(season: int, out_dir: Path) -> Path:
    """Download and unzip one season of shots (season = start year, e.g. 2024)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"shots_{season}.zip"
    with httpx.stream(
        "GET", SHOTS_URL.format(season=season), timeout=120, follow_redirects=True
    ) as r:
        r.raise_for_status()
        with zip_path.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(out_dir)
    zip_path.unlink()
    return out_dir / f"shots_{season}.csv"

# icewatch

Live NHL win probability. icewatch follows every play of a game as it happens, updates the
chance each team wins, and watches its own model for drift over the season.

It is built as a production ML system, not a notebook: streaming ingestion, a tracked and
versioned model, a served prediction API, and monitoring.

## Status

**Phase 1: data layer** (in progress)

## Quickstart

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest

# One game, parsed into event rows
uv run icewatch game 2024020001

# Historical shot data from MoneyPuck
uv run icewatch moneypuck 2023 2024

# A full season of play-by-play (about 1,312 games, roughly 10 minutes)
uv run icewatch backfill 2024
```

Data is written to `data/` and is never committed.

## Roadmap

| Phase | What | Stack |
|---|---|---|
| 1 | Ingest historical and live play-by-play into clean event tables | Python, httpx, pandas, Parquet |
| 2 | Baseline win-probability model, calibrated, with experiment tracking | XGBoost, scikit-learn, MLflow |
| 3 | Serve predictions over an API | FastAPI, Docker |
| 4 | Live pipeline: stream plays during games and score each one | Redpanda (Kafka API), PostgreSQL |
| 5 | Monitoring: latency, calibration, and drift across the season | Prometheus, Grafana |
| 6 | Deploy to the cloud | AWS or GCP, Terraform, GitHub Actions |
| 7 | Dashboard: live win-probability chart for every game | React |

## Data sources

- **NHL web API** (`api-web.nhle.com`): live and historical play-by-play. Unofficial and
  undocumented, so requests are rate-limited and retried.
- **[MoneyPuck](https://moneypuck.com/data.htm)**: historical shot data, 2007 onward.
  Data courtesy of MoneyPuck.com, used for non-commercial purposes.

## License

MIT

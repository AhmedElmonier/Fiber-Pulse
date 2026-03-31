# Quickstart: Phase 2 — Logistics, Macro & Feedstock

## Goal

Bootstrap Phase 2 ingestion for freight and macro feeds, validate persistence, and confirm source health behavior.

## Prerequisites

- Python 3.12 installed
- Poetry installed
- PostgreSQL instance available (version 14+ recommended)
- `pgvector` extension installed or installable for future support
- Access to or configuration for the target feed endpoints

## Environment

Create a `.env` file with values similar to the following:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/fiberpulse
TIMEZONE=Africa/Cairo
LOG_LEVEL=INFO
# Add any source credential values required by the new freight and macro scrapers
# e.g. CCFI_API_KEY=...
```

## Setup

### Install dependencies

```bash
poetry install
```

### Create the database and extensions

```bash
createdb fiberpulse
psql fiberpulse -c "CREATE EXTENSION IF NOT EXISTS pgvector;"
```

### Create or update database tables

```bash
poetry run python -c "from db.schema import create_tables; import os; from dotenv import load_dotenv; load_dotenv(); create_tables(os.getenv('DATABASE_URL'))"
```

> If Phase 2 adds a dedicated `freight_rates` table, extend `db/schema.py` before running this command.

## Run the Phase 2 ingestion flow

### Python API usage

```python
import asyncio
from dotenv import load_dotenv
from db.repository import Repository
from agents.data_fetcher import DataFetcher
from agents.normalizer import Normalizer
from agents.source_health import get_evaluator

load_dotenv()

def main():
    repo = Repository()
    fetcher = DataFetcher(repository=repo, normalizer=Normalizer(), health_evaluator=get_evaluator())
    return asyncio.run(fetcher.ingest_source("ccfi_med"))

if __name__ == "__main__":
    result = main()
    print(result.to_dict())
```

### Run a full sample ingestion cycle

Use the existing ingestion orchestrator and add the new source names once they are implemented:

```python
import asyncio
from db.repository import Repository
from agents.data_fetcher import DataFetcher

async def run_all():
    repo = Repository()
    fetcher = DataFetcher(repository=repo)
    for source in ["ccfi_med", "drewry_wci", "fx_usd_inr", "fx_usd_cny", "oil_spot", "electricity"]:
        result = await fetcher.ingest_source(source)
        print(source, result.success, result.records_ingested, result.fallback_used)

asyncio.run(run_all())
```

## Validation

### Verify freight ingestion

```sql
SELECT source_name, route, COUNT(*) AS records, MIN(timestamp_utc), MAX(timestamp_utc)
FROM freight_rates
GROUP BY source_name, route;
```

### Verify macro ingestion

```sql
SELECT source_name, commodity, COUNT(*) AS records, MIN(timestamp_utc), MAX(timestamp_utc)
FROM price_history
WHERE source_type = 'macro'
GROUP BY source_name, commodity;
```

### Verify source health

```sql
SELECT source_name, status, last_success_at, fallback_active, stale_duration_minutes
FROM source_health;
```

### Run tests

```bash
poetry run pytest tests/unit -v
poetry run pytest tests/integration -v
```

## Notes

- Phase 2 is intentionally focused on backend ingestion, normalization, and health semantics.
- Downstream forecasting and alerting will consume these new signals in a later phase.

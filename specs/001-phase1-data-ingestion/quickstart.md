# Quickstart: Phase 1 — Foundation & Data Ingestion

## Goal

Get the Phase 1 data ingestion foundation running locally, with PostgreSQL persistence and a minimal ingestion pipeline.

## Prerequisites

- Python 3.12 installed
- Poetry installed (or pip with venv)
- PostgreSQL instance available (version 14+ recommended)
- `pgvector` extension installed or installable for future embedding support
- Access to the target data sources or sample feed payloads

## Environment

Create a `.env` file with the following values:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/fiberpulse
CURRENCY_RATE_API_KEY=your_currency_api_key
TIMEZONE=Africa/Cairo
LOG_LEVEL=INFO
```

Additional configuration values:

- `DATA_SOURCE_CREDENTIALS` for any authenticated scraper feeds
- `TELEGRAM_BOT_TOKEN` for later integration phases (optional)

## Setup

### Option 1: Using Poetry (Recommended)

1. Install dependencies:

```bash
poetry install
```

2. Create the database and enable required extensions:

```bash
createdb fiberpulse
psql fiberpulse -c "CREATE EXTENSION IF NOT EXISTS pgvector;"
```

3. Create database tables:

```bash
poetry run python -c "from db.schema import create_tables; import os; from dotenv import load_dotenv; load_dotenv(); create_tables(os.getenv('DATABASE_URL'))"
```

Or run directly:

```bash
poetry run python db/schema.py
```

### Option 2: Using pip with virtual environment

1. Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

2. Create the database:

```bash
createdb fiberpulse
psql fiberpulse -c "CREATE EXTENSION IF NOT EXISTS pgvector;"
```

3. Create database tables:

```bash
python -c "from db.schema import create_tables; import os; from dotenv import load_dotenv; load_dotenv(); create_tables(os.getenv('DATABASE_URL'))"
```

## Run the ingestion foundation

### Run a single ingestion cycle

Execute the one-shot ingestion flow:

```bash
poetry run python -m agents.data_fetcher --run-once
# Or with venv:
python -m agents.data_fetcher --run-once
```

### Run with custom sources

```python
import asyncio
from db.repository import Repository
from agents.data_fetcher import run_ingestion

async def main():
    repo = Repository("postgresql://user:password@localhost:5432/fiberpulse")
    results = await run_ingestion(repo, sources=["cai_spot", "mcx_futures"])
    for source, result in results.items():
        print(f"{source}: {result.records_ingested} records, success={result.success}")

asyncio.run(main())
```

## Validation

### Run unit tests

```bash
poetry run pytest tests/unit -v
# Or with venv:
pytest tests/unit -v
```

### Run integration tests

```bash
poetry run pytest tests/integration -v
# Or with venv:
pytest tests/integration -v
```

### Run all tests

```bash
poetry run pytest -v
```

### Validate ingestion results

Check the database for expected records:

```sql
-- Verify price_history records contain normalized_usd
SELECT source_name, COUNT(*), MIN(normalized_usd), MAX(normalized_usd)
FROM price_history
GROUP BY source_name;

-- Verify source_health records reflect current source status
SELECT source_name, status, last_success_at, fallback_active
FROM source_health;

-- Verify raw payload metadata is persisted
SELECT source_name, timestamp_utc, raw_price, record_metadata
FROM price_history
LIMIT 5;
```

## Project Structure

```
agents/
├── base_scraper.py          # Base scraper interface
├── cai_spot_scraper.py      # CAI cotton spot adapter
├── mcx_futures_scraper.py   # MCX cotton futures adapter
├── ccfgroup_scraper.py      # CCFGroup fallback adapter
├── fibre2fashion_scraper.py # Fibre2Fashion fallback adapter
├── iea_scraper.py           # IEA utility adapter
├── data_fetcher.py          # Ingestion orchestrator
├── normalizer.py            # Payload validation and USD normalization
└── source_health.py         # Health state evaluation

db/
├── schema.py                # SQLAlchemy table definitions
└── repository.py            # Async persistence layer

models/
├── price_history.py         # PriceHistoryRecord model
├── source_health.py         # SourceHealthRecord model
├── currency_conversion.py   # CurrencyConversionRecord model
└── ingestion_source.py      # IngestionSource model

utils/
└── usd_converter.py         # Currency conversion utilities

tests/
├── unit/                    # Unit tests
│   ├── test_data_model.py
│   ├── test_repository.py
│   └── test_source_health.py
└── integration/             # Integration tests
    └── test_daily_ingestion.py
```

## Troubleshooting

### Database connection errors

Ensure PostgreSQL is running and the `DATABASE_URL` in `.env` is correct:

```bash
psql $DATABASE_URL -c "SELECT 1"
```

### Import errors

Make sure you're in the virtual environment and have installed the package:

```bash
# With Poetry
poetry install

# With pip
pip install -e .
```

### Test failures

Some tests require a running database. Set up the test database:

```bash
createdb fiberpulse_test
psql fiberpulse_test -c "CREATE EXTENSION IF NOT EXISTS pgvector;"
```

## Notes

- This quickstart is intentionally lightweight and focused on Phase 1 deliverables.
- Forecasting, Telegram alerts, and production deployment are planned for later phases.
- The ingestion pipeline supports both primary and fallback sources with automatic health tracking.
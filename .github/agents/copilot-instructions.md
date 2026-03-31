# Cotton - PSF Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-30

## Active Technologies
- Python 3.12 + Poetry, SQLAlchemy, asyncpg, python-dotenv, pytest (002-phase2-logistics-macro-feedstock)
- PostgreSQL with `pgvector` support for future embeddings; existing `price_history`, `source_health`, `ingestion_source`, `currency_conversion`; planned freight log table or freight ingestion extension (002-phase2-logistics-macro-feedstock)

- Python 3.12 + Poetry, HTTPX, SQLAlchemy, asyncpg, python-dotenv, pytest (001-phase1-data-ingestion)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12: Follow standard conventions

## Recent Changes
- 002-phase2-logistics-macro-feedstock: Added Python 3.12 + Poetry, SQLAlchemy, asyncpg, python-dotenv, pytest

- 001-phase1-data-ingestion: Added Python 3.12 + Poetry, HTTPX, SQLAlchemy, asyncpg, python-dotenv, pytest

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

# Cotton - PSF Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-01

## Active Technologies
- Python 3.12 + `python-telegram-bot` (v20+), `matplotlib`, `APScheduler`, `SQLAlchemy`, `asyncpg` (004-interface-alerts)
- PostgreSQL with `pgvector` (existing) (004-interface-alerts)

- Python 3.12 + XGBoost, Scikit-learn, NLTK/TextBlob, SQLAlchemy, asyncpg, click (for CLI) (003-baseline-ai-sentiment)

## Project Structure

```text
src/
tests/
```

## Commands

.venv/bin/python -m pytest && .venv/bin/python -m ruff check .

## Code Style

Python 3.12: Follow standard conventions

## Recent Changes
- 004-interface-alerts: Added Python 3.12 + `python-telegram-bot` (v20+), `matplotlib`, `APScheduler`, `SQLAlchemy`, `asyncpg`

- 003-baseline-ai-sentiment: Added Python 3.12 + XGBoost, Scikit-learn, NLTK/TextBlob, SQLAlchemy, asyncpg, click (for CLI)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

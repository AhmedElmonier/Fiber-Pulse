# FiberPulse AI

FiberPulse AI is a data-driven procurement intelligence system for Egypt-bound textile supply chains. It combines upstream feedstock pricing, raw cotton markets, logistics indices, macroeconomic signals, and sentiment to generate actionable 90-day price outlooks for yarn, PSF, and freight.

## Project Purpose

- Predict yarn and fiber price movements 90 days in advance.
- Normalize global commodity data into USD for consistent decision support.
- Provide operational alerts and Telegram-based reporting for procurement teams.
- Protect production quality with baseline-first forecasting and a gated model promotion process.

## What This Repo Contains

- `FiberPulse.md`: the primary PRD with full technical architecture, data model, and roadmap.
- `plan.md`: the implementation plan that breaks the project into phased delivery milestones.
- `.specify/`: SpecKit metadata and constitution for project governance.
- Python project layout for agents, scrapers, models, telemetry, and bot integration.

## Architecture Overview

The system is built around a multi-agent pipeline:

- `DataFetcherAgent`: retrieves raw market, freight, and macro feeds.
- `NormalizerAgent`: converts prices to USD, applies validation, and logs source health.
- `ForecastAgent`: runs baseline forecasts first, then evaluates TFT promotion.
- `SentimentAgent`: scores news/headlines using keyword rules and optional FinBERT.
- `AlertAgent`: applies a 3-filter volatility shield and sends operational alerts.
- `ReporterAgent`: assembles Telegram messages, charts, and summaries.

Storage is designed for auditability:

- PostgreSQL with `pgvector` for embeddings and forecast storage.
- `price_history`, `freight_rates`, `forecasts`, `sentiment_events`, `alert_log`, and `source_health` tables.

## Key Principles

1. **Data Integrity First**: every feed is validated, health-scored, and normalized before use.
2. **Baseline-First Forecasting**: deliver explainable forecasts before enabling complex models.
3. **Transparent Confidence**: show confidence bounds, decay status, and alert rationale.
4. **Operational Delivery**: support commands, reports, and feedback-driven workflows.
5. **Phased, Maintainable Delivery**: build incrementally with modular, testable code.

## Repository Structure

```text
fiberpulse/
├── agents/          # orchestrators and agent workflows
├── data/            # scrapers, fallbacks, health monitoring
├── models/          # baseline and TFT forecasting components
├── nlp/             # sentiment scoring logic
├── db/              # schema, migrations, repository access
├── bot/             # Telegram bot handlers and scheduling
├── charts/          # visualization generation
├── utils/           # normalization, alert suppression, confidence handling
├── config.py        # settings and environment loading
├── main.py          # runtime entry point
├── pyproject.toml   # dependency definitions
├── FiberPulse.md    # product requirements document
└── plan.md          # delivery plan
```

## Recommended Stack

- Python 3.12
- Poetry for dependency management
- PostgreSQL + pgvector
- Async HTTP via `httpx`
- `pytorch-forecasting` / `pytorch-lightning`
- `plotly` for chart generation
- `python-telegram-bot` for bot integration
- `apscheduler` for Cairo-time scheduling
- `pydantic` for validation

## Setup Instructions

1. Clone or initialize the repository.
2. Install dependencies using Poetry:

   ```bash
   poetry install
   ```

3. Create a `.env` file containing required secrets and service keys:

   ```text
   TELEGRAM_BOT_TOKEN=...
   TELEGRAM_CHAT_ID=...
   POSTGRES_URL=postgresql://user:pass@localhost:5432/fiberpulse
   CCF_API_KEY=...
   IEX_API_KEY=...
   ALPHA_VANTAGE_KEY=...
   OPENAI_KEY=...
   TZ=Africa/Cairo
   ```

4. Provision PostgreSQL and enable `pgvector`:

   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

5. Apply the schema from `db/schema.sql`.
6. Run the application entrypoint once environment variables are configured:

   ```bash
   poetry run python main.py
   ```

## Development Notes

- The earliest deliverables include data ingestion, USD normalization, feed health tracking, and baseline forecasting.
- The first production interface is a Telegram bot with commands like `/outlook`, `/freight`, `/buy`, and `/history`.
- Model promotion is gated: TFT only goes live if it beats the baseline by 15% MAE improvement.
- Confidence decay logic ensures stale data does not produce overconfident forecasts.

## Delivery Roadmap

- **Phase 1**: Foundation and data ingestion
- **Phase 2**: Freight, macro, and fallback handling
- **Phase 3**: Baseline forecasting and sentiment
- **Phase 4**: Telegram interface and alerting
- **Phase 5**: TFT upgrade, promotion gate, and production hardening

For full phase details, see `plan.md`.

## How to Contribute

- Use `FiberPulse.md` as the authoritative PRD for product and architecture decisions.
- Keep changes small, modular, and aligned with the constitution in `.specify/memory/constitution.md`.
- Document schema or contract changes clearly in the implementation plan.
- Add tests for new ingestion paths, forecast behavior, alert rules, and bot commands.

## Notes

- This repository is designed as a research-driven implementation for textile procurement intelligence.
- The Telegram bot is expected to be the first production-facing delivery channel.
- All scheduling and reporting is aligned to Cairo market hours.

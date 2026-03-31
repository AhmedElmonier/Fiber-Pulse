# FiberPulse AI Implementation Plan

## Overview
Build the end-to-end FiberPulse AI system from data ingestion through forecasting and Telegram reporting. Start with a production baseline using XGBoost, then promote TFT after validation.

## Phase 1 — Foundation & Data Ingestion (Week 1)

1. Setup environment
   - create `pyproject.toml`
   - configure `.env`
   - provision PostgreSQL + `pgvector`
   - run DB schema

2. Build core infrastructure
   - `config.py` / settings
   - `db/repository.py`
   - `utils/usd_converter.py`

3. Implement data source health tracking
   - `source_health` table
   - health updater / dashboard logic

4. Build primary data ingestion
   - CAI cotton spot scraper
   - MCX cotton futures scraper
   - CCFGroup PSF/PTA/MEG integration
   - fallback scrapers: Fibre2Fashion, IEA
   - upsert to `price_history`

5. Validate end-to-end daily ingest
   - confirm prices normalized to USD
   - confirm DB writes and source health statuses

## Phase 2 — Logistics, Macro & Feedstock (Week 2)

1. Freight ingestion
   - CCFI Mediterranean route scraper
   - Drewry WCI scraper
   - store in `freight_rates`

2. Macro feeds
   - FX rates (`USD/INR`, `USD/CNY`)
   - oil spot prices
   - IEX electricity

3. Fallback / confidence handling
   - stale/live/dead states
   - fallback activation logic
   - confidence decay detection

4. Integrate into unified fetch pipeline
   - `agents/data_fetcher.py`
   - `agents/normalizer.py`
   - ensure all sources feed same repository

## Phase 3 — Baseline AI + Sentiment (Week 3)

1. Tier-1 sentiment engine
   - `nlp/keyword_scorer.py`
   - ingest headlines
   - store in `sentiment_events`

2. Historical data onboarding
   - `/history` CSV ingest flow
   - prepare training dataset

3. Baseline model
   - implement `models/baseline_model.py`
   - train XGBoost
   - validate MAE target (< 5%)

4. Forecast pipeline
   - `agents/forecast.py`
   - persist forecasts to `forecasts`
   - attach confidence intervals and decay flags

5. Confidence decay
   - `utils/confidence_decay.py`
   - widen CIs when feeds stale >48h

## Phase 4 — Interface & Alerts (Week 4)

1. Telegram bot skeleton
   - `bot/telegram_bot.py`
   - `bot/commands.py`

2. Bot commands
   - `/buy`
   - `/outlook`
   - `/freight`
   - `/history`

3. Chart generation
   - `charts/fan_chart.py`
   - `charts/freight_bar.py`
   - attach charts to bot replies

4. Alerting
   - `utils/alert_suppressor.py`
   - 3% volatility filter
   - store alerts in `alert_log`

5. Scheduler
   - `bot/scheduler.py`
   - 4x daily Cairo-time reports

## Phase 5 — TFT Upgrade & Model Promotion (Weeks 5–6)

1. Build TFT pipeline
   - `models/tft_model.py`
   - `TimeSeriesDataSet`
   - training / validation

2. Promotion gate
   - `models/model_registry.py`
   - compare TFT MAE vs baseline
   - enable TFT only if >15% improvement

3. FinBERT evaluation
   - `nlp/finbert_scorer.py`
   - zero-shot accuracy check
   - decide whether to fine-tune

4. Production hardening
   - active model selection
   - alert fatigue monitoring
   - weekly performance dashboard

## Immediate next steps

1. create project skeleton and `pyproject.toml`
2. initialize database schema
3. implement `db/repository.py` + `utils/usd_converter.py`
4. build first data fetchers for CAI / MCX / CCFGroup

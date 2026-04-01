# Implementation Plan: Phase 3 — Baseline AI + Sentiment

**Branch**: `003-baseline-ai-sentiment` | **Date**: 2026-03-31 | **Spec**: /specs/003-baseline-ai-sentiment/spec.md
**Input**: Feature specification from `/specs/003-baseline-ai-sentiment/spec.md`

## Summary

Build the first production predictive layer for FiberPulse. This phase implements a keyword-based sentiment scoring engine, a historical data onboarding flow via CLI, and an XGBoost-based baseline forecasting model with uncertainty-aware confidence intervals that decay when data feeds are stale.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: XGBoost, Scikit-learn, NLTK/TextBlob, SQLAlchemy, asyncpg, click (for CLI)  
**Storage**: PostgreSQL + `pgvector` (tables: `sentiment_events`, `forecasts`, `historical_onboarding_log`)  
**Testing**: pytest  
**Target Platform**: Linux server  
**Project Type**: Python backend service with CLI  
**Performance Goals**: Ingest 1,000+ records < 60s (SC-004); assign sentiment score within 5m of ingestion (SC-002)  
**Constraints**: Baseline MAE < 5% (SC-001); automatic 20% CI widening for stale data (SC-003); Africa/Cairo timezone  
**Scale/Scope**: Support daily cotton market headlines and daily price forecasts for primary indices

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Data Integrity**: Inputs treated as contracts. Historical data must be validated for integrity (FR-001).
- **Baseline-First**: Implementing XGBoost baseline (models/baseline_model.py) before attempting TFT in Phase 5.
- **Transparency**: Forecasts must include interval bounds and confidence status (FR-004).
- **Actionable Delivery**: CLI command `fiberpulse ingest-history` provided for operational data management.
- **Incremental Delivery**: Phase 3 focuses strictly on baseline AI and sentiment signals as defined in the Week 3 roadmap.

## Project Structure

### Documentation (this feature)

```text
specs/003-baseline-ai-sentiment/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
nlp/
└── keyword_scorer.py    # Tier-1 sentiment engine

models/
└── baseline_model.py    # XGBoost implementation

agents/
├── forecast.py          # Forecast orchestrator
└── historical_onboarding.py # CLI logic for CSV ingestion

utils/
└── confidence_decay.py  # Uncertainty scaling logic

tests/
├── unit/
│   ├── test_sentiment.py
│   └── test_decay.py
├── integration/
│   └── test_forecast_pipeline.py
└── contract/
    └── test_forecast_schema.py
```

**Structure Decision**: Single project structure focusing on `nlp/`, `models/`, and `agents/` extensions to the core repository.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

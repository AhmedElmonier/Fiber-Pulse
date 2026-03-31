# Implementation Plan: Phase 1 — Foundation & Data Ingestion

**Branch**: `001-phase1-data-ingestion` | **Date**: 2026-03-28 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-phase1-data-ingestion/spec.md`

**Note**: This plan is written to establish the ingestion foundation, normalize cotton price feeds to USD, and enforce explicit source health contracts.

## Summary

Phase 1 builds the FiberPulse ingestion foundation by collecting primary cotton price feeds, normalizing every record to USD, preserving raw audit metadata, and recording source health state. The objective is a reliable data contract for downstream forecasting and operational reporting while keeping the scope strictly bounded to ingestion, persistence, and health tracking.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Poetry, HTTPX, SQLAlchemy, asyncpg, python-dotenv, pytest
**Storage**: PostgreSQL with planned `pgvector` readiness for future embedding work
**Testing**: pytest with unit and integration coverage for ingestion, normalization, and health rules
**Target Platform**: Linux server / container runtime
**Project Type**: backend data pipeline service
**Performance Goals**: daily ingestion of the configured Phase 1 source set within 30 minutes, source health update latency below 5 minutes after completion
**Constraints**: no public UI in Phase 1, maintain explicit audit trails, operate on Africa/Cairo time for scheduled jobs, ensure stale/fallback handling
**Scale/Scope**: support hundreds of historical price records and scale to thousands of daily entries once the feed set expands

## Constitution Check

- **Data Integrity as First-Class Product**: PASS — Plan preserves raw payload metadata, enforces USD normalization, and records fallback/stale state.
- **Baseline-First Forecasting**: NOT APPLICABLE — Phase 1 stops before forecasting and focuses on ingestion foundation.
- **Transparency and Confidence**: PASS — Source health state and metadata contracts are defined clearly.
- **Operationally Actionable Delivery**: PASS — Ingestion contracts and health records provide the operational foundation for later alerting and reports.
- **Incremental, Maintainable Delivery**: PASS — Scope is explicitly bounded to ingestion and health tracking only.

## Project Structure

### Documentation (this feature)

```text
specs/001-phase1-data-ingestion/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── data-contracts.md
└── tasks.md
```

### Source Code (planned layout)

```text
agents/
├── data_fetcher.py
├── normalizer.py
├── source_health.py

db/
├── repository.py
├── schema.py

models/
├── price_history.py
├── source_health.py
├── currency_rate.py

utils/
├── usd_converter.py
├── timezone.py
├── retry_helpers.py

tests/
├── unit/
└── integration/
```

**Structure Decision**: A single Python backend service is the correct structure for Phase 1 because the work centers on data ingestion, persistence, and normalization rather than a multi-project UI stack.

## Complexity Tracking

No constitution violations require justification for this phase: the architecture remains intentionally narrow and aligned with the data ingestion foundation.

# Implementation Plan: Phase 2 — Logistics, Macro & Feedstock

**Branch**: `002-phase2-logistics-macro-feedstock` | **Date**: 2026-03-30 | **Spec**: /specs/002-phase2-logistics-macro-feedstock/spec.md
**Input**: Feature specification from /specs/002-phase2-logistics-macro-feedstock/spec.md

## Summary

Extend the existing backend ingestion pipeline to support Phase 2 logistics freight and macroeconomic feedstock sources. Freight records are persisted to `freight_rates`, macro records are persisted to `price_history` with `source_type = macro`, and source health logic must detect stale and fallback conditions within a 48-hour window.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: SQLAlchemy, asyncpg, pytest, PostgreSQL drivers
**Storage**: PostgreSQL (`freight_rates`, `price_history`, `source_health`)
**Testing**: pytest
**Target Platform**: Linux backend service
**Project Type**: Single Python service
**Performance Goals**: reliable daily ingestion for freight and macro feeds; accurate staleness detection and fallback handling for daily sources
**Constraints**: preserve existing Phase 1 ingestion conventions, avoid introducing UI work in this phase, keep persistence and health metadata compatible with downstream consumers, and schedule daily ingestion and health evaluation jobs in Africa/Cairo timezone
**Scale/Scope**: support daily logistics and macro sources plus fallback provenance and unified repository schema for downstream forecasting

## Constitution Check

- Align with the existing repository structure: `agents/`, `db/`, `models/`, `tests/`, `utils/`
- Phase 2 is backend-only; no frontend or UI work is included
- Keep the feature focused on ingestion, normalization, persistence, and source health as described in the spec

## Architecture

- Reuse `agents/data_fetcher.py` as the core ingestion orchestrator
- Add source-specific scrapers for freight and macro feeds under `agents/`
- Extend `agents/normalizer.py` with dedicated freight and macro normalization functions producing a unified normalized record shape
- Persist freight records to `freight_rates` and macro records to `price_history` with `source_type = macro`
- Use `agents/source_health.py` and `db/repository.py` to evaluate, persist, and expose source health and fallback metadata
- Schedule ingestion and health checks in Africa/Cairo timezone
- Enforce stale detection at 48 hours for daily logistics and macro publications

## Project Structure

Single Python service layout:
- `agents/`
- `db/`
- `models/`
- `tests/`
- `utils/`

## Phases

1. Setup: data models, schema updates, and repository persistence methods
2. Foundational: normalization and source health logic plus contract tests
3. US1: freight and macro ingestion implementation and validation
4. US2: source health, stale/fallback handling, and confidence metadata
5. US3: unified repository integration and query consistency
6. Polish: documentation, type hints, tests, and config validation

## Implementation details

- `agents/normalizer.py`: add `normalize_freight()` and `normalize_macro()` functions
- `agents/data_fetcher.py`: route freight and macro sources to the correct normalization and persistence targets
- `agents/source_health.py`: implement `evaluate_source_health()`, `activate_fallback()`, and fallback chain resolution
- `db/schema.py`: ensure `freight_rates`, `price_history`, and `source_health` schemas support metadata, quality flags, and timestamp indexes
- `db/repository.py`: add persistence methods for freight, macro, and source health records
- `tests/`: create focused unit and integration tests for ingestion, normalization, health transitions, unified schema consistency, and ingestion quality validation for SC-001

## Dependencies & Execution Order

- Setup first: models, schema, repository methods
- Foundational next: normalization and source health
- US1 next: ingestion scraper integration and persistence
- US2 next: fallback logic and health state handling
- US3 last: unify repository semantics and consumer-facing query patterns
- Polish last: docs, tests, type hints, and validation

## Risks / Open Questions

- Source formats and credentials for CCFI, Drewry, FX, oil, and electricity feeds must be confirmed before implementation
- Currency normalization rules should preserve original currency and also expose USD-equivalent values for downstream consumers
- Existing Phase 1 fetch and persistence conventions must remain compatible with new Phase 2 record shapes

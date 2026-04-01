---

description: "Task list for Phase 2 — Logistics, Macro & Feedstock implementation"

---

# Tasks: Phase 2 — Logistics, Macro & Feedstock

**Input**: Design documents from `/specs/002-phase2-logistics-macro-feedstock/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story (US1, US2, US3) to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project structure**: `src/` contains models, services, agents, etc. at repository root
- Core project paths: `agents/`, `db/`, `models/`, `utils/`, `tests/`
- Paths are relative to repository root: `/mnt/4EDC012BDC010EC1/Projects/Cotton - PSF`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database schema updates and shared data structures needed by all downstream work

- [X] T001 Create `FreightRate` data model in `models/freight_rate.py` (SQLAlchemy entity for freight_rates table with all fields from data-model.md)
- [X] T002 [P] Create `MacroFeedRecord` data model in `models/macro_feed_record.py` (SQLAlchemy entity for price_history records with source_type=macro)
- [X] T003 [P] Create `SourceHealthRecord` data model in `models/source_health_record.py` (enhancement to existing SourceHealthRecord with new status enums: live, stale, dead, degraded, failed)
- [X] T004 [P] Create `IngestionSource` configuration model in `models/ingestion_source.py` (configuration entity for managing source metadata, priority, category, and fallback relationships)
- [X] T005 Update `db/schema.py` to create `freight_rates`, `macro_feed_record`, and `source_health` tables with proper indexes on source_name, timestamp_utc, and status
- [X] T006 Create database migration script `db/migrations/001_add_phase2_tables.py` to safely provision freight_rates and enhanced source_health schema
- [X] T007 Update `db/repository.py` to add repository methods: `persist_freight_rate()`, `persist_macro_feed()`, `update_source_health()`, and query methods for health status

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and shared normalization logic that MUST complete before user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Extend `agents/normalizer.py` with `normalize_freight()` method to handle raw freight payloads: extract route, convert raw_currency to USD using existing conversion logic, apply quality flags
- [X] T009 [P] Extend `agents/normalizer.py` with `normalize_macro()` method to handle raw macro payloads: extract commodity, normalize currency to USD, preserve metadata and source provenance
- [X] T010 [P] Create `agents/source_health.py` health evaluator with methods: `evaluate_source_health()` (returns live/stale/degraded/failed status based on 48-hour threshold), `activate_fallback()` (records fallback state), and `get_stale_duration_minutes()` (calculates elapsed time since fresh data)
- [X] T011 Update `agents/data_fetcher.py` to integrate health evaluator: add health check before persistence, mark records with quality flags for stale/fallback status, update source health after each ingest
- [X] T012 Create contract test suite in `tests/contract/test_data_contracts.py` to validate all incoming payloads conform to Raw Source Payload Contract, Normalized Freight Record Contract, Normalized Macro Record Contract, and Source Health Contract
- [X] T013 [P] Create integration test fixture in `tests/integration/test_fixtures.py` with sample CCFI Mediterranean, Drewry WCI, FX, oil, and electricity payloads to support Phase 2 testing

**Checkpoint**: Foundational infrastructure ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Logistics and macro feed ingestion (Priority: P1) 🎯 MVP

**Goal**: Collect freight and macroeconomic inputs reliably with source metadata and normalized values

**Independent Test**: Run the ingestion pipeline and verify that new freight and macro records are written into the repository with source metadata and normalized values.

### Tests for User Story 1 ⚠️

> **NOTE: These tests MUST FAIL before implementation begins**

- [X] T014 [P] [US1] Create integration test in `tests/integration/test_freight_ingestion.py` that executes `ingest_source('ccfi_med')` and verifies freight_rates contains records with correct source_name, route, timestamp_utc, and USD normalization
- [X] T015 [P] [US1] Create integration test in `tests/integration/test_macro_ingestion.py` that executes macro ingestion for fx_usd_inr, fx_usd_cny, oil_spot, electricity and verifies price_history contains records with source_type=macro and normalized_usd values
- [X] T016 [P] [US1] Create unit test in `tests/unit/test_normalizer_freight.py` testing `normalize_freight()` with sample CCFI and Drewry payloads, validating route extraction, currency conversion, and quality flag assignment
- [X] T051 [P] [US1] Create integration test in `tests/integration/test_ingestion_quality.py` that validates at least 95% of sample daily freight and macro records are ingested and normalized successfully.
- [X] T052 [P] [US2] Create a timezone validation test in `tests/integration/test_timezone_alignment.py` that verifies ingestion schedules and health evaluation windows use Africa/Cairo timezone.

### Implementation for User Story 1

- [X] T017 [P] [US1] Create CCFI Mediterranean scraper in `agents/ccfi_mediterranean_scraper.py` (extends base_scraper.py) that fetches daily rate data and emits raw payload conforming to Raw Source Payload Contract
- [X] T018 [P] [US1] Create Drewry WCI scraper in `agents/drewry_wci_scraper.py` (extends base_scraper.py) that fetches freight indices by route and emits normalized payloads with route metadata
- [X] T019 [P] [US1] Create macro feed scraper factory in `agents/macro_feed_scraper.py` supporting fx_usd_inr, fx_usd_cny, oil_spot, and electricity sources; each endpoint returns raw payload with commodity label and currency code
- [X] T020 [US1] Register new scrapers in `agents/__init__.py` and update `DataFetcher.ingest_source()` to recognize source names: 'ccfi_med', 'drewry_wci', 'fx_usd_inr', 'fx_usd_cny', 'oil_spot', 'electricity'
- [X] T021 [US1] Update `agents/data_fetcher.py` method `ingest_source()` to route freight and macro sources to appropriate normalization and persist to correct table (freight_rates or price_history with source_type=macro)
- [X] T022 [US1] Add logging in `agents/data_fetcher.py` for each ingestion step: fetch start, payload received, normalization success, persistence outcome, and source health update (include source_name, record_count, timestamp, stale status)

**Checkpoint**: User Story 1 should be fully functional and testable independently. Run tests and verify freight/macro records are persisted.

---

## Phase 4: User Story 2 - Source health and fallback handling (Priority: P2)

**Goal**: Detect stale or dead sources and automatically switch to fallback data where appropriate

**Independent Test**: Simulate a primary source outage and verify that fallback activation, stale/dead state tagging, and confidence metadata are recorded correctly.

### Tests for User Story 2 ⚠️

> **NOTE: These tests MUST FAIL before implementation begins**

- [X] T023 [P] [US2] Create unit test in `tests/unit/test_source_health.py` testing health evaluator state transitions: verify source transitions from live→stale after 48 hours, stale→degraded when fallback activated, degraded→live when primary recovers
- [X] T024 [P] [US2] Create integration test in `tests/integration/test_fallback_activation.py` that mocks a source returning stale data, executes pipeline, and verifies fallback_active flag is set, fallback_source is recorded, and quality_flags contain fallback metadata
- [X] T025 [P] [US2] Create integration test in `tests/integration/test_source_staleness.py` that simulates missing data for 48+ hours, runs health evaluator, and verifies stale status is recorded and stale_duration_minutes is calculated

### Implementation for User Story 2

- [X] T026 [P] [US2] Enhance `IngestionSource` model with fallback chain: add `fallback_to` field to link primary sources to fallback sources (e.g., 'ccfi_med' fallback_to 'drewry_wci')
- [X] T027 [P] [US2] Implement fallback resolver in `agents/source_health.py` method `resolve_fallback_chain()` that returns ordered list of fallback sources for a given primary source
- [X] T028 [US2] Update `agents/data_fetcher.py` method `ingest_source()` to catch fetch failures and invoke fallback resolver; if primary fails, automatically attempt fallback sources in priority order
- [X] T029 [US2] Enhance quality_flags logic in normalization: add `fallback: boolean` and `fallback_source: string` fields; set fallback=true and record fallback_source when data comes from non-primary source
- [X] T030 [US2] Update `agents/source_health.py` with stale detection logic: query last_success_at for a source, compare to now(), mark stale if >48 hours, calculate and store stale_duration_minutes
- [X] T031 [US2] Implement `agents/source_health.py` method `activate_fallback()` to set fallback_active=true, record fallback_source, and transition status from stale→degraded
- [X] T032 [US2] Update source health persistence in `db/repository.py` method `update_source_health()` to record: status, last_success_at, last_checked_at, fallback_active, stale_duration_minutes, and remarks
- [X] T033 [US2] Add logging for fallback activation in `agents/data_fetcher.py`: log primary source failure, fallback activation, and which fallback source is now in use (include source_name, reason for fallback, new status)

**Checkpoint**: User Story 2 should handle source failures and fallback seamlessly. Verify fallback activation and health state transitions work correctly.

---

## Phase 5: User Story 3 - Unified repository integration (Priority: P3)

**Goal**: Logistics and macro feeds arrive through a common fetch and normalization pipeline with unified repository schema

**Independent Test**: Execute the unified fetch pipeline against sample freight and macro sources and confirm the results are stored with normalized fields and health metadata in the repository.

### Tests for User Story 3 ⚠️

> **NOTE: These tests MUST FAIL before implementation begins**

- [X] T034 [P] [US3] Create integration test in `tests/integration/test_unified_pipeline.py` that ingests both freight (ccfi_med, drewry_wci) and macro (fx_usd_inr, fx_usd_cny, oil_spot, electricity) sources in sequence and verifies all records persist with consistent schema
- [X] T035 [P] [US3] Create unit test in `tests/unit/test_unified_schema.py` that validates normalized records from freight and macro sources conform to a unified contract: source_name, timestamp_utc, normalized_usd, quality_flags, metadata presence
- [X] T036 [P] [US3] Create integration test in `tests/integration/test_schema_consistency.py` that queries freight_rates and price_history (with source_type=macro) and verifies field compatibility and query patterns work uniformly

### Implementation for User Story 3

- [X] T037 [US3] Create unified query interface in `db/repository.py` methods: `get_normalized_records()` (returns both freight and macro with filters by source_type, timestamp range, source_name) and `get_records_by_health_status()` (returns records filtered by stale/live/fallback status)
- [X] T038 [P] [US3] Standardize schema for freight_rates and price_history (macro) in `db/schema.py`: ensure identical fields for source_name, timestamp_utc, raw_price, normalized_usd, conversion_rate, quality_flags, metadata
- [X] T039 [P] [US3] Update `agents/normalizer.py` to use unified normalization path: both `normalize_freight()` and `normalize_macro()` produce records with identical output schema for downstream consumers
- [X] T040 [P] [US3] Create orchestrator in `agents/unified_ingestion_orchestrator.py` that accepts a list of source_names (e.g., ['ccfi_med', 'fx_usd_inr', 'oil_spot']) and executes `DataFetcher.ingest_source()` for each, collecting results and reporting aggregated success/failure metrics
- [X] T041 [US3] Document unified repository API in `docs/unified_repository_api.md`: query patterns, example code for consuming normalized records, schema documentation, and how downstream consumers use unified interface
- [X] T042 [US3] Add integration test runner in `tests/integration/run_unified_pipeline.py` that executes orchestrator against all Phase 2 sources and reports ingestion summary: records_ingested, fallback_usage, stale_records, and errors

**Checkpoint**: All three user stories should now be independently functional. Verify unified pipeline works end-to-end.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple stories, final validation, and production readiness

- [X] T043 [P] Run `quickstart.md` validation: execute all Python example code blocks, create sample database, ingest Phase 2 sources, run SQL validation queries to confirm table schemas and data persistence
- [X] T044 [P] Add comprehensive docstrings to all new modules: `agents/ccfi_mediterranean_scraper.py`, `agents/drewry_wci_scraper.py`, `agents/macro_feed_scraper.py`, `agents/source_health.py`, all new model files
- [X] T045 [P] Update API documentation in `docs/` with examples: Phase 2 ingestion usage, fallback behavior, health status queries, unified repository patterns
- [X] T046 [P] Add unit tests for edge cases in `tests/unit/test_edge_cases.py`: partial macro data, out-of-order timestamps, currency mismatches, null/missing values in optional fields
- [X] T047 Create end-to-end test in `tests/integration/test_e2e_phase2.py` that simulates full workflow: schedule ingestion for all sources, simulate source failures, verify fallback activation, check final state of freight_rates and price_history
- [X] T048 [P] Code cleanup: remove debug logging, ensure consistent naming conventions, add type hints to all function signatures in agents/ and models/
- [X] T049 [P] Performance review in `tests/performance/test_ingestion_performance.py`: benchmark normalization speed for bulk records, verify source health queries are indexed efficiently, confirm persistence latency is acceptable
- [X] T050 Add configuration validation in `config.py`: verify all required ingestion sources are configured with credentials and endpoints before pipeline execution

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T001-T007) - **BLOCKS** all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion - MUST complete before US2 testing (independent of other stories)
- **User Story 2 (Phase 4)**: Depends on Foundational + US1 completion - enhances existing ingestion with health/fallback
- **User Story 3 (Phase 5)**: Depends on Foundational + US1 + US2 completion - unifies all into single pipeline
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (Logistics/macro ingestion)**: Can start after Foundational (Phase 2) - No dependencies on US2/US3
- **US2 (Source health/fallback)**: Can start after US1 is testable - Depends on US1 ingestion being established
- **US3 (Unified integration)**: Can start after US1+US2 complete - Builds on top of existing pipelines

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Scrapers before integration with DataFetcher (US1)
- Health evaluator before fallback logic (US2)
- Individual pipelines before unified orchestration (US3)

### Parallel Opportunities

**Phase 1 (Setup)**: All model creation [T001-T004] can run in parallel; db work [T005-T007] must follow
  
**Phase 2 (Foundational)**: 
- Normalizer enhancements [T008-T009] can run in parallel
- Health evaluator [T010] runs independently
- Contract tests [T012] can run in parallel with integration fixtures [T013]

**Phase 3 (US1)**:
- Tests [T014-T016] can all run in parallel
- Scrapers [T017-T019] can all be developed in parallel
- Final integration [T020-T022] follows scraper completion

**Phase 4 (US2)**:
- Tests [T023-T025] can run in parallel
- Health model enhancements [T026-T027] can run in parallel
- Pipeline updates [T028-T033] follow model enhancements

**Phase 5 (US3)**:
- Tests [T034-T036] can run in parallel
- Schema standardization [T037-T039] can run in parallel
- Orchestration [T040-T042] follows schema work

**Phase 6 (Polish)**: All polish tasks [T043-T050] marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Phase 1 Setup - Can run in parallel:
Task: "Create FreightRate data model in models/freight_rate.py" [T001]
Task: "Create MacroFeedRecord data model in models/macro_feed_record.py" [T002]
Task: "Create SourceHealthRecord data model in models/source_health_record.py" [T003]
Task: "Create IngestionSource configuration model in models/ingestion_source.py" [T004]

# Phase 1 Database - Must follow models:
Task: "Update db/schema.py to create freight_rates table" [T005]
Task: "Create database migration script" [T006]
Task: "Update db/repository.py with persistence methods" [T007]

# Phase 2 Foundational - Can run in parallel:
Task: "Extend normalizer with normalize_freight()" [T008]
Task: "Extend normalizer with normalize_macro()" [T009]
Task: "Create source_health.py health evaluator" [T010]

# US1 Tests - Can run in parallel:
Task: "Create freight ingestion integration test" [T014]
Task: "Create macro ingestion integration test" [T015]
Task: "Create normalizer unit test" [T016]

# US1 Scrapers - Can run in parallel:
Task: "Create CCFI Mediterranean scraper" [T017]
Task: "Create Drewry WCI scraper" [T018]
Task: "Create macro feed scraper factory" [T019]

# US1 Integration - Must follow scrapers:
Task: "Register scrapers in DataFetcher" [T020]
Task: "Update DataFetcher routing logic" [T021]
Task: "Add logging to DataFetcher" [T022]
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. **Complete Phase 1**: Setup (models, schema, repository)
2. **Complete Phase 2**: Foundational (normalization, health evaluator, contracts)
3. **Complete Phase 3**: User Story 1 (freight and macro scraping and ingestion)
4. **STOP and VALIDATE**: 
   - Run integration tests for US1
   - Verify freight_rates and price_history have records
   - Run quickstart.md examples
5. Deploy/demo if ready

**Estimated scope**: 20-25 tasks, 3-4 weeks for one developer

### Incremental Delivery

1. Setup + Foundational → Foundation ready (all core infrastructure)
2. Add US1 → Test independently → Deploy/Demo (MVP! Can ingest freight and macro)
3. Add US2 → Test independently → Deploy/Demo (Now with health and fallback)
4. Add US3 → Test independently → Deploy/Demo (Unified pipeline complete)
5. Polish → Production ready

Each phase adds value without breaking previous work.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (1 week)
2. Once Foundational is done:
   - Developer A: US1 Scrapers [T017-T019] + Integration [T020-T022]
   - Developer B: US1 Tests [T014-T016] (write tests first, ensure they fail)
   - Developer C: Documentation and preparation for US2
3. US1 testing + integration validates scrapers
4. Then proceed to US2 (health/fallback) with full team
5. Finally US3 (unified pipeline) once US1+US2 stable

---

## Validation & Testing

### Independent Test Criteria for Each User Story

**User Story 1 - Logistics and macro ingestion**:
- [X] Run `pytest tests/integration/test_freight_ingestion.py -v` → All tests pass
- [X] Run `pytest tests/integration/test_macro_ingestion.py -v` → All tests pass
- [X] Query `SELECT COUNT(*) FROM freight_rates WHERE source_name IN ('ccfi_med', 'drewry_wci')` → Count > 0
- [X] Query `SELECT COUNT(*) FROM price_history WHERE source_type = 'macro'` → Count > 0
- [X] Verify source_health table shows all sources with status recorded

**User Story 2 - Source health and fallback handling**:
- [X] Run `pytest tests/integration/test_fallback_activation.py -v` → All tests pass
- [X] Simulate source outage: Set source to unavailable, run ingestion, verify fallback_active=true
- [X] Query records with fallback flag: `SELECT COUNT(*) FROM freight_rates WHERE quality_flags->>'fallback' = 'true'` → Count > 0
- [X] Verify stale detection: records >48 hours old marked with stale=true

**User Story 3 - Unified repository integration**:
- [X] Run `pytest tests/integration/test_unified_pipeline.py -v` → All tests pass
- [X] Execute orchestrator: `python agents/unified_ingestion_orchestrator.py` → Reports success for all sources
- [X] Query unified interface: `db.get_normalized_records(source_types=['freight', 'macro'])` → Returns records from both tables
- [X] Verify schema consistency across freight_rates and price_history records

---

## Notes

- **[P] tasks** = different files with no dependencies on incomplete tasks
- **[Story] label** maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **Tests are OPTIONAL** but strongly recommended for Phase 2 critical ingestion logic
- Verify tests **FAIL before implementing** (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same-file conflicts that prevent parallelization, cross-story dependencies that break independence


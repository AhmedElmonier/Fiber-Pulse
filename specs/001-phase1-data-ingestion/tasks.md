# Tasks: Phase 1 — Foundation & Data Ingestion

**Input**: Design documents from `/specs/001-phase1-data-ingestion/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the project foundation, environment configuration, and folder layout before any feature implementation.

- [X] T001 Create project skeleton directories at `agents/`, `db/`, `models/`, `utils/`, `tests/unit/`, and `tests/integration/`
- [X] T002 Create `pyproject.toml` with Poetry-managed dependencies for Python 3.12, HTTPX, SQLAlchemy, asyncpg, python-dotenv, and pytest
- [X] T003 Create `.env.example` and `config.py` to load database and environment settings
- [X] T004 Create `specs/001-phase1-data-ingestion/quickstart.md` with local bootstrap instructions for Phase 1
- [X] T005 [P] Create `specs/001-phase1-data-ingestion/contracts/data-contracts.md` documenting the ingestion and health payload contracts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement core data structures, schema, persistence, and shared services required by all user stories.

- [X] T006 Create `db/schema.py` defining PostgreSQL tables for `price_history`, `source_health`, `ingestion_source`, and `currency_conversion`
- [X] T007 Create `db/repository.py` with persistence methods for price records, health records, source metadata, and currency conversion records
- [X] T008 Create `models/price_history.py`, `models/source_health.py`, `models/currency_conversion.py`, and `models/ingestion_source.py` with the Phase 1 data model definitions
- [X] T009 Create `utils/usd_converter.py` to normalize raw currency values into USD using exchange rate data
- [X] T010 Create `agents/normalizer.py` to validate incoming source payloads, apply USD conversion, annotate audit metadata, and prepare normalized records for persistence
- [X] T011 [P] Create `agents/source_health.py` to evaluate source state transitions and determine `live`, `stale`, `degraded`, or `failed` statuses
- [X] T012 [P] Create `tests/unit/test_data_model.py` to verify entity definitions, required fields, and unique constraints
- [X] T013 [P] Create `tests/unit/test_repository.py` to verify persistence operations for the core ingestion tables

---

## Phase 3: User Story 1 - Daily data ingestion success (Priority: P1)

**Goal**: Implement the primary ingestion pipeline for CAI spot and MCX futures and persist normalized prices into `price_history`.

**Independent Test**: Trigger the ingestion pipeline and confirm normalized `price_history` records are written with raw metadata and source health updates.

- [X] T014 Create `agents/cai_spot_scraper.py` implementing the CAI cotton spot adapter contract for Phase 1 (FR-001)
- [X] T015 Create `agents/mcx_futures_scraper.py` implementing the MCX cotton futures adapter contract for Phase 1 (FR-001)
- [X] T016 Create `agents/data_fetcher.py` to orchestrate primary source ingestion, normalization, and persistence
- [X] T017 [US1] Implement fallback activation logic in `agents/data_fetcher.py` so secondary sources are used when primary feeds fail (FR-002)
- [X] T033 [US1] Create fallback source adapters for CCFGroup, Fibre2Fashion, and IEA in `agents/` and integrate them into the ingestion flow (FR-002)
- [X] T018 [US1] Persist normalized price records via `db/repository.py` into `price_history` (FR-003, FR-007)
- [X] T019 [US1] Add end-to-end ingestion verification in `agents/data_fetcher.py` to confirm new records and health updates after each run (FR-005)
- [X] T032 [US1] Create `tests/integration/test_daily_ingestion.py` to validate end-to-end ingestion, normalization, and source health state
- [X] T034 [US1] Add validation tests that assert the 95% primary source ingestion baseline and 95% USD normalization coverage thresholds (SC-001, SC-003)

---

## Phase 4: User Story 2 - Source health monitoring (Priority: P2)

**Goal**: Implement source health tracking so operators can detect failed, stale, degraded, and recovered ingestion sources.

**Independent Test**: Execute the health updater against simulated source outcomes and verify `source_health` records reflect the correct state.

- [X] T020 [US2] Implement health state evaluation rules in `agents/source_health.py` for `live`, `stale`, `degraded`, and `failed` (FR-004)
- [X] T021 [US2] Persist health state transitions via `db/repository.py` into `source_health` (FR-004)
- [X] T022 [US2] Update `agents/data_fetcher.py` to record `fallback_active` and `details` for each source ingestion attempt
- [X] T023 [US2] Create `tests/unit/test_source_health.py` covering health transitions, fallback activation, and stale detection

---

## Phase 5: User Story 3 - Data validation and normalization (Priority: P3)

**Goal**: Ensure raw price payloads are validated, currency converted, and deduplicated before storage.

**Independent Test**: Ingest sample raw payloads with foreign currency and duplicate scenarios, then verify the final `price_history` output and deduplication behavior.

- [X] T024 [US3] Implement `utils/usd_converter.py` currency normalization rules and conversion lookup behavior for foreign values (FR-003)
- [X] T025 [US3] Implement `models/currency_conversion.py` and persistence support in `db/repository.py` (FR-003)
- [X] T026 [US3] Add raw payload validation and duplicate detection to `agents/normalizer.py` (FR-006, FR-007)
- [X] T027 [US3] Enforce deduplication in `db/repository.py` with a unique constraint on `(source_name, timestamp_utc, raw_price)` (FR-006)


---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, documentation, and consistency work across Phase 1.

- [X] T028 [P] Update `specs/001-phase1-data-ingestion/quickstart.md` with any new setup or run commands discovered during implementation
- [X] T029 [P] Update `specs/001-phase1-data-ingestion/contracts/data-contracts.md` with actual payload fields and implementation notes
- [X] T030 [P] Add any missing integration tests to `tests/integration/test_daily_ingestion.py`
- [X] T031 [P] Review and polish `db/schema.py`, `agents/data_fetcher.py`, and `agents/normalizer.py` for maintainability

---

## Dependencies & Execution Order

### Phase Dependencies

- `Phase 1: Setup` can start immediately
- `Phase 2: Foundational` depends on completion of Setup
- `Phase 3+` User stories depend on completion of Foundational
- `Phase 6: Polish` depends on one or more completed user stories

### User Story Dependencies

- **US1 (P1)**: Requires foundational schema, repository, normalizer, and config support
- **US2 (P2)**: Requires source health infrastructure from Phase 2 and the ingestion orchestration in US1
- **US3 (P3)**: Requires normalization and currency conversion utilities from Phase 2 and the ingestion pipeline from US1

### Parallel Opportunities

- `T005`, `T011`, `T012`, `T013`, `T028`, `T029`, and `T030` are marked [P] and can run in parallel because they work on separate files or documentation
- `T006`, `T007`, `T008`, `T009`, and `T010` are foundational but can be developed in parallel by different team members once the initial project skeleton exists
- User stories can proceed in parallel after foundational work, with US1, US2, and US3 each having independent implementation tasks

### Implementation Strategy

- MVP focus: complete Setup + Foundational + US1 first, then validate daily ingestion independently
- Next increment: add US2 health tracking and validate source state correctness
- Final Phase 1 increment: add US3 validation and normalization rules, then polish

---

## Notes

- All tasks include exact file paths and are ordered for execution.
- User stories are organized by priority so the P1 ingestion core is delivered first.
- The file path conventions follow the Python backend structure described in `plan.md`.

---

description: "Task list for Phase 3 — Baseline AI + Sentiment implementation"
---

# Tasks: Phase 3 — Baseline AI + Sentiment

**Input**: Design documents from `/specs/003-baseline-ai-sentiment/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths below are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure: `nlp/`, `models/`, `agents/`, `tests/unit/`, `tests/integration/`, `tests/contract/`
- [x] T002 Update `pyproject.toml` with new dependencies: `xgboost`, `scikit-learn`, `nltk`, `textblob`, `click`
- [x] T003 [P] Initialize NLTK data (punkt, stopwords) in `nlp/keyword_scorer.py` setup

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create `SentimentEvent` and `Forecast` database tables in `db/schema.py` with proper indexes
- [x] T005 Create `HistoricalOnboardingLog` database table in `db/schema.py`
- [x] T006 [P] Create `SentimentEvent` model in `models/sentiment_event.py`
- [x] T007 [P] Create `Forecast` model in `models/forecast.py`
- [x] T008 [P] Create `HistoricalOnboardingLog` model in `models/historical_onboarding_log.py`
- [x] T009 Update `db/repository.py` with persistence methods for new Phase 3 models
- [x] T010 [P] Create uncertainty scaling logic in `utils/confidence_decay.py` (20% widening rule)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Historical Data Onboarding (Priority: P1) 🎯 MVP

**Goal**: Ingest historical cotton market data from CSV files via CLI

**Independent Test**: Run `fiberpulse ingest-history <file.csv>` and verify records in `price_history` and `historical_onboarding_log`

### Implementation for User Story 1

- [x] T011 [P] [US1] Contract test for historical CSV format in `tests/contract/test_historical_ingest.py`
- [x] T012 [US1] Implement CSV parser and integrity validator in `agents/historical_onboarding.py`
- [x] T013 [US1] Implement CLI command `ingest-history` in `agents/historical_onboarding.py` using `click`
- [x] T014 [US1] Add duplicate detection and record tagging in `agents/historical_onboarding.py`
- [x] T015 [US1] Integration test for full onboarding flow in `tests/integration/test_historical_onboarding.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Market Forecasting (Priority: P1)

**Goal**: Generate daily price forecasts with confidence intervals using XGBoost

**Independent Test**: Run `fiberpulse forecast --target cai_spot` and verify output record in `forecasts` table

### Implementation for User Story 2

- [x] T016 [P] [US2] Contract test for forecast record schema in `tests/contract/test_forecast_schema.py`
- [x] T017 [US2] Implement feature extraction (30-day sliding window) in `models/baseline_model.py`
- [x] T018 [US2] Implement XGBoost Quantile Regression (0.05, 0.5, 0.95) in `models/baseline_model.py`
- [x] T019 [US2] Implement forecast orchestrator in `agents/forecast.py` (recursive prediction logic for 24h horizon)
- [x] T020 [US2] Integrate confidence decay penalty in `agents/forecast.py` (calling `utils/confidence_decay.py`)
- [x] T021 [US2] Implement MAE validation utility in `utils/metrics.py` to verify SC-001 accuracy targets
- [x] T022 [US2] Integration test for forecast pipeline in `tests/integration/test_forecast_pipeline.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Market Sentiment Scoring (Priority: P2)

**Goal**: Score daily Market Headlines as Bullish, Bearish, or Neutral

**Independent Test**: Feed sample headlines to `KeywordScorer` and verify scores in `sentiment_events`

### Implementation for User Story 3

- [x] T023 [P] [US3] Contract test for sentiment event payload in `tests/contract/test_sentiment_schema.py`
- [x] T024 [US3] Implement curated keyword list and scoring logic in `nlp/keyword_scorer.py`
- [x] T025 [US3] Integrate VADER/TextBlob for polarity refinement in `nlp/keyword_scorer.py`
- [x] T026 [US3] Update `agents/data_fetcher.py` to route Market Headlines to `KeywordScorer`
- [x] T027 [US3] Unit test for sentiment engine in `tests/unit/test_sentiment.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T028 [P] Update `docs/unified_repository_api.md` with sentiment and forecast query patterns
- [x] T029 [P] Add type hints to all new modules in `nlp/`, `models/`, and `agents/`
- [x] T030 Performance review: verify SC-004 (1,000 records < 60s) using `tests/performance/test_onboarding_speed.py`
- [x] T031 Final validation: Run `quickstart.md` examples and verify all SC-001 through SC-004 criteria

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1
- **User Stories (Phase 3-5)**: All depend on Foundational (Phase 2)
  - US1 and US2 are P1 and should be prioritized
  - US3 (Sentiment) is P2
- **Polish (Phase 6)**: Depends on US1-US3

### User Story Dependencies

- **US1 (Onboarding)**: Independent
- **US2 (Forecast)**: Independent, but benefits from US1 data
- **US3 (Sentiment)**: Independent

---

## Parallel Example: Phase 2

```bash
# Launch all model definitions together:
Task: "Create SentimentEvent model in models/sentiment_event.py"
Task: "Create Forecast model in models/forecast.py"
Task: "Create HistoricalOnboardingLog model in models/historical_onboarding_log.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 & 2)

1. Complete Phase 1 & 2
2. Complete US1 (Ingest historical data)
3. Complete US2 (Generate forecasts)
4. **STOP and VALIDATE**: Verify we can train on history and predict tomorrow's price

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group

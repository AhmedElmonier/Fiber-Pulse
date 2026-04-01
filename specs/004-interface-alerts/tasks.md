# Tasks: Phase 4 — Interface & Alerts

**Input**: Design documents from `/specs/004-interface-alerts/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included as requested by the development workflow in the FiberPulse AI Constitution ("All PRs MUST include tests for new behavior...").

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure for `src/bot/`, `src/charts/`, and `src/models/`
- [x] T002 [P] Install dependencies: `python-telegram-bot`, `matplotlib`, `APScheduler`
- [x] T003 [P] Update `.env.example` with `TELEGRAM_BOT_TOKEN` and `TELEGRAM_WHITELIST`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create database migration for `alert_log` and `bot_command_log` in `db/migrations/002_add_phase4_tables.py`
- [x] T005 [P] Implement SQLAlchemy models for logging in `src/models/alert_log.py`
- [x] T006 [P] Update `src/db/repository.py` with methods for persistence of alert and command logs
- [x] T007 Implement basic bot skeleton and whitelisting logic in `src/bot/telegram_bot.py`
- [x] T008 [P] Implement generic message and error handlers in `src/bot/handlers.py`
- [x] T009 [P] Implement alert suppression utility in `src/utils/alert_suppressor.py`

**Checkpoint**: Foundation ready - whitelisted users can interact with a "Hello World" bot.

---

## Phase 3: User Story 1 - Market Outlook & Buy Recommendations (Priority: P1) 🎯 MVP

**Goal**: Provide AI-driven trade recommendations and outlooks via Telegram.

**Independent Test**: Send `/buy` and `/outlook` to the bot and verify a response with valid data and a fan chart.

### Tests for User Story 1

- [x] T010 [P] [US1] Unit test for fan chart generation in `tests/unit/test_fan_chart.py`
- [x] T011 [US1] Integration test for `/buy` and `/outlook` handlers in `tests/integration/test_bot_forecast_commands.py`

### Implementation for User Story 1

- [x] T012 [P] [US1] Implement fan chart generation using Matplotlib in `src/charts/fan_chart.py`
- [x] T013 [US1] Implement `/buy` and `/outlook` command handlers in `src/bot/commands.py`
- [x] T014 [US1] Integrate `src/charts/fan_chart.py` into `/outlook` command response
- [x] T015 [US1] Add command logging for `/buy` and `/outlook` in `src/bot/handlers.py`

**Checkpoint**: MVP Ready - Users can get forecasts and buy signals via Telegram.

---

## Phase 4: User Story 2 - High Volatility Alerts (Priority: P1)

**Goal**: Trigger immediate notifications for >3% price movements.

**Independent Test**: Insert a 4% price jump in the DB and verify all whitelisted users receive an alert.

### Tests for User Story 2

- [x] T016 [US2] Integration test for alert trigger and suppression in `tests/integration/test_price_alerts.py`

### Implementation for User Story 2

- [x] T017 [P] [US2] Implement the alerting logic that compares the latest price vs. previous day in `src/utils/alert_trigger.py`
- [x] T018 [US2] Integrate alert trigger with `src/utils/alert_suppressor.py`
- [x] T019 [US2] Implement the broadcast logic to send alerts to all whitelisted users in `src/bot/telegram_bot.py`
- [x] T020 [US2] Log all sent alerts in `alert_log` table

**Checkpoint**: Real-time monitoring is active and notifies users of significant shifts.

---

## Phase 5: User Story 3 - Scheduled Market Reports (Priority: P2)

**Goal**: 4x daily automated market pulse reports (Cairo time).

**Independent Test**: Manually trigger the scheduler and verify a comprehensive report is sent to all users.

### Tests for User Story 3

- [x] T021 [US3] Unit test for scheduler configuration and Cairo-timezone offset in `tests/unit/test_scheduler.py`

### Implementation for User Story 3

- [x] T022 [US3] Configure `APScheduler` with 09:00, 12:00, 15:00, 18:00 triggers in `src/bot/scheduler.py`
- [x] T023 [US3] Implement the market report composition logic (Price + Freight + Sentiment) in `src/bot/scheduler.py`
- [x] T024 [US3] Integrate scheduled reports with the individual broadcast logic in `src/bot/telegram_bot.py`

**Checkpoint**: Automated reporting is active, providing regular market pulses.

---

## Phase 6: User Story 4 - Logistics & Freight Monitoring (Priority: P3)

**Goal**: Provide freight rate checks and trend bar charts.

**Independent Test**: Send `/freight` to the bot and verify a response with rates and a bar chart.

### Implementation for User Story 4

- [x] T025 [P] [US4] Implement freight bar chart generation in `src/charts/freight_bar.py`
- [x] T026 [US4] Implement `/freight` command handler in `src/bot/commands.py`
- [x] T027 [US4] Integrate `src/charts/freight_bar.py` into `/freight` response

---

## Phase 7: History Command (Priority: P2)

**Goal**: Retrieve 30-day historical data.

**Independent Test**: Send `/history` and verify a tabular response with a trend chart.

- [x] T028 [US1] Implement `/history` command handler in `src/bot/commands.py`
- [x] T029 [US1] Implement price trend chart (sparkline style) in `src/charts/fan_chart.py` or new `src/charts/trend_chart.py`

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T030 [P] Implement health-check command `/status` for bot monitoring
- [x] T031 Final validation of SC-001 (response time < 2s) using `bot_command_log`
- [x] T032 Run `quickstart.md` validation on a clean environment
- [x] T033 Documentation updates in `README.md` and `docs/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** & **Foundational (Phase 2)**: MUST be complete before any user stories.
- **User Story 1 (P1)**: The MVP target. Can be worked on after Phase 2.
- **User Story 2 (P1)**: High priority, depends on Phase 2.
- **User Story 3 (P2)**: Depends on Phase 2 and bot broadcasting logic (from US2).
- **User Story 4 (P3)**: Depends on Phase 2.

### Parallel Opportunities

- All tasks marked [P] can run in parallel.
- US1, US2, and US4 can technically start in parallel once Phase 2 foundation is ready.

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Setup and Foundational infrastructure.
2. Implement US1 (`/buy`, `/outlook` with Fan Charts).
3. **STOP and VALIDATE**: Test with real forecast data.

### Incremental Delivery

1. Foundation → Bot skeleton active.
2. US1 → Forecasts delivered.
3. US2 → Real-time alerts active.
4. US3 → Automated reporting active.
5. US4 → Logistics utility added.

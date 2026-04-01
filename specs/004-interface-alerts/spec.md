# Feature Specification: Phase 4 — Interface & Alerts

**Feature Branch**: `004-interface-alerts`  
**Created**: 2026-04-01  
**Status**: Draft  
**Input**: User description: "read @plan.md and create detailed oriented & comprehensive specification for Phase 4 — Interface & Alerts (Week 4)"

## Clarifications

### Session 2026-04-01
- Q: How should the bot restrict access to authorized users? → A: Whitelist of specific Telegram User IDs (pre-configured in DB/Env).
- Q: What are the specific target hours for the 4 daily reports? → A: 09:00, 12:00, 15:00, 18:00 (Cairo time).
- Q: Should reports and alerts be sent to individual whitelisted users or a shared channel? → A: Broadcasted individually to all users in the whitelist.
- Q: What should the `/history` command return? → A: Last 30 days of price history (Table + Sparkline/Chart).
- Q: How should the alert suppressor handle multiple instruments? → A: Individual alerts per instrument, suppressed independently (max 1/hr per instrument).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Market Outlook & Buy Recommendations (Priority: P1)

As a trader, I want to query the AI's current outlook and buy/sell recommendations via Telegram so that I can make informed decisions quickly from my mobile device.

**Why this priority**: This is the primary interface for users to access the core value of the FiberPulse AI system (the forecasts).

**Independent Test**: Can be fully tested by sending `/buy` and `/outlook` commands to the bot and receiving a response with a summary and a fan chart.

**Acceptance Scenarios**:

1. **Given** the bot is active and models have generated forecasts, **When** I send `/buy`, **Then** the bot returns a clear recommendation (Strong Buy/Buy/Hold/Sell) with a confidence score.
2. **Given** the bot is active, **When** I send `/outlook`, **Then** the bot returns a textual summary of the next 30 days and attaches a fan chart visualization.

---

### User Story 2 - High Volatility Alerts (Priority: P1)

As a market participant, I want to receive immediate notifications when prices move significantly so that I can react to sudden market shifts.

**Why this priority**: Real-time alerting provides critical time-sensitive value that scheduled reports might miss.

**Independent Test**: Can be tested by simulating a 3% price move in the database and verifying that an alert is sent individually to all whitelisted users.

**Acceptance Scenarios**:

1. **Given** a new price entry shows a >3% change from the previous day, **When** the alerting engine runs, **Then** a notification is sent individually to all whitelisted users.
2. **Given** multiple price updates within a short window, **When** the alert suppressor is active, **Then** redundant alerts are filtered to prevent notification fatigue.

---

### User Story 3 - Scheduled Market Reports (Priority: P2)

As a busy professional, I want to receive automated market updates 4 times a day (Cairo time) so that I stay informed without having to manually query the bot.

**Why this priority**: Ensures consistent engagement and provides regular "pulse" updates.

**Independent Test**: Can be tested by setting the scheduler to a 1-minute interval and verifying 4 reports are generated and sent individually to all whitelisted users.

**Acceptance Scenarios**:

1. **Given** the scheduler is running, **When** the time matches one of the 4 daily slots (Cairo time), **Then** a comprehensive market report (Price, Freight, Sentiment) is broadcasted individually to all whitelisted users.

---

### User Story 4 - Logistics & Freight Monitoring (Priority: P3)

As a logistics manager, I want to check current freight rates and trends via Telegram so that I can estimate shipping costs.

**Why this priority**: Provides specialized utility for logistics-focused users.

**Independent Test**: Can be tested by sending `/freight` to the bot and receiving current Mediterranean/WCI rates with a bar chart.

**Acceptance Scenarios**:

1. **Given** the bot is active, **When** I send `/freight`, **Then** the bot returns current rates for CCFI Mediterranean and Drewry WCI routes with a trend bar chart.

---

### Edge Cases

- **What happens when the forecast engine fails?** The bot should report that forecasts are currently unavailable and provide the last known price instead of crashing.
- **How does system handle data gaps?** If a data source is stale, the bot should include a "confidence decay" warning in the output.
- **What happens if Telegram API is unreachable?** The system should log the failure and retry the broadcast/alert according to an exponential backoff policy.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a Telegram Bot interface reachable via a public handle, restricted to a whitelist of authorized Telegram User IDs.
- **FR-002**: Bot MUST support command-based interaction for `/buy`, `/outlook`, `/freight`, and `/history`.
- **FR-003**: System MUST generate "fan charts" showing price forecasts with confidence intervals (shaded regions).
- **FR-004**: System MUST generate "bar charts" for freight rate comparisons across routes.
- **FR-005**: Alerting engine MUST trigger a notification when a 24h price movement exceeds a 3% threshold.
- **FR-006**: System MUST implement an alert suppressor that limits notifications to a maximum of one alert per hour per instrument, sent individually as they occur.
- **FR-007**: Scheduler MUST execute report broadcasts individually to all whitelisted users 4 times daily at 09:00, 12:00, 15:00, and 18:00 (Cairo time).
- **FR-008**: All alerts and sent reports MUST be logged in an `alert_log` table for audit and debugging.
- **FR-009**: The `/history` command MUST return the last 30 days of price history for the primary instrument, including both a text-based table and a trend chart.

### Key Entities *(include if feature involves data)*

- **Alert Log**: Represents a record of a sent notification. Attributes: `timestamp`, `trigger_reason`, `target_chat_id`, `message_payload`, `status`.
- **Bot Command**: Represents a user interaction. Attributes: `user_id`, `command_name`, `timestamp`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Bot responds to standard commands (`/buy`, `/outlook`) in under 2 seconds.
- **SC-002**: 99.9% of scheduled reports are delivered within 5 minutes of the target Cairo time (09:00, 12:00, 15:00, 18:00).
- **SC-003**: Charts generated for Telegram are optimized for mobile viewing (legible text, correct aspect ratio).
- **SC-004**: Alert suppressor reduces redundant notifications by at least 80% during periods of extreme volatility.

## Assumptions

- **Timezone**: All scheduling is based on Cairo time (EET/EEST).
- **Mobile First**: User interface is optimized for the Telegram mobile app.
- **Data Availability**: Assumes Phase 1-3 are complete and the database is populated with prices, freight, and forecasts.
- **Connectivity**: The server hosting the bot has stable outgoing HTTPS access to the Telegram Bot API.

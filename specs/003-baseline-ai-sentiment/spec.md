# Feature Specification: Phase 3 — Baseline AI + Sentiment

**Feature Branch**: `003-baseline-ai-sentiment`  
**Created**: 2026-03-31  
**Status**: Draft  
**Input**: User description: "read @plan.md and create specification for Phase 3 — Baseline AI + Sentiment (Week 3)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Historical Data Onboarding (Priority: P1)

As a Data Analyst, I want to upload historical cotton market data from local files so that I can provide a robust training foundation for the predictive models.

**Why this priority**: Essential for model training. Without historical data, the baseline model cannot produce accurate or validated forecasts.

**Independent Test**: Can be fully tested by providing a standard data file to the ingestion interface and verifying that all records are correctly parsed and stored in the repository.

**Acceptance Scenarios**:

1. **Given** a formatted historical data file, **When** the ingestion process is triggered, **Then** the system validates data integrity and adds the records to the historical repository.
2. **Given** a data file with missing mandatory fields, **When** the ingestion is attempted, **Then** the system rejects the file and provides a summary of validation errors.

---

### User Story 2 - Baseline Market Forecasting (Priority: P1)

As a Business Stakeholder, I want to see daily price forecasts with confidence intervals so that I can make informed procurement decisions based on expected market movement.

**Why this priority**: Core value proposition of Phase 3. Provides the first actionable AI-driven insights.

**Independent Test**: Can be tested by running the forecast pipeline on a validated dataset and verifying that a prediction record is generated with both a point estimate and a defined confidence range.

**Acceptance Scenarios**:

1. **Given** fresh ingested market data, **When** the daily forecast cycle runs, **Then** the system generates a price outlook for the next cycle.
2. **Given** a generated forecast, **When** viewed by a user, **Then** it must clearly display the "most likely" price and the upper/lower bounds of confidence.

---

### User Story 3 - Market Sentiment Scoring (Priority: P2)

As a Market Analyst, I want the system to score daily Market Headlines so that I can understand the prevailing sentiment (bullish/bearish) affecting the cotton market.

**Why this priority**: Adds a qualitative dimension to the quantitative price data, improving the richness of the signals provided to stakeholders.

**Independent Test**: Can be tested by feeding known Market Headlines to the engine and verifying that a sentiment score is produced and associated with the headline in the database.

**Acceptance Scenarios**:

1. **Given** a set of Market Headlines, **When** the sentiment engine processes them, **Then** each headline is assigned a score reflecting its impact on market outlook.
2. **Given** headlines from multiple sources, **When** stored, **Then** the sentiment scores are aggregated to provide an overall daily sentiment trend.

---

### User Story 4 - Confidence Decay Visualization (Priority: P3)

As an Operational User, I want to see wider confidence intervals when data sources are stale so that I am aware of the increased uncertainty in the forecast.

**Why this priority**: Prevents misleading precision when the underlying data is old or missing.

**Independent Test**: Can be tested by simulating a 48-hour data outage and verifying that the generated forecast intervals for the subsequent period are measurably wider than those generated with fresh data.

**Acceptance Scenarios**:

1. **Given** a data source that has not been updated for >48 hours, **When** a forecast is generated using that source, **Then** the system automatically applies a "decay penalty" to the confidence intervals.

### Edge Cases

- **Empty Text Source**: How does the sentiment engine handle days with zero headlines? (Default: Neutral score or "Insufficient Data" flag).
- **Data Gaps**: What happens if historical data has missing dates? (Default: Statistical interpolation or record flagging).
- **Extreme Volatility**: How does the baseline model handle unprecedented price spikes? (Constraint: Model MUST flag extreme outliers for review).

## Clarifications

### Session 2026-03-31
- Q: What primary interface should be provided for "Historical Data Onboarding"? → A: CLI command (e.g., `fiberpulse ingest-history <path>`)
- Q: What scoring logic should the Tier-1 sentiment engine use for headlines? → A: Keywords/Rules (Bullish/Bearish/Neutral)
- Q: What is the primary forecast horizon for the baseline model? → A: Next 24-hour cycle (Next Day)
- Q: How should confidence intervals decay when data is stale (>48h)? → A: Fixed % increase (e.g., +20% width)
- Q: When should the automated price forecast be executed? → A: Scheduled (Fixed daily time)

## Functional Requirements

- **FR-001**: System MUST provide a CLI command (e.g., `fiberpulse ingest-history <path>`) to ingest historical market data from standard structured files (e.g., CSV).
- **FR-002**: System MUST implement a keyword-based scoring engine to categorize market sentiment from headlines as Bullish, Bearish, or Neutral.
- **FR-003**: System MUST generate automated price forecasts for the next 24-hour cycle on a fixed daily schedule.
- **FR-004**: System MUST calculate upper and lower confidence bounds for every price forecast generated.
- **FR-005**: System MUST automatically increase the uncertainty range (confidence interval width) by a fixed percentage (e.g., 20%) when primary data feeds are stale (>48 hours).
- **FR-006**: System MUST persist all sentiment events and forecast results with full provenance (source, timestamp, model version).

### Key Entities *(include if feature involves data)*

- **Market Headline**: Represents an individual piece of text data used for sentiment analysis.
- **SentimentEvent**: Represents the result of a sentiment scoring operation, including the score and engine version.
- **Forecast**: Represents a predicted market state, containing the predicted value, timestamp, and confidence interval bounds.
- **HistoricalOnboardingLog**: Tracks the status and record count of bulk CSV data ingestion operations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Baseline model achieves a Mean Absolute Error (MAE) of less than 5% on validated historical datasets.
- **SC-002**: 100% of ingested headlines are assigned a sentiment score within 5 minutes of ingestion.
- **SC-003**: Forecast confidence intervals widen by at least 20% when data staleness exceeds the 48-hour threshold.
- **SC-004**: The system can ingest and validate a historical dataset of 1,000+ records in under 60 seconds.

## Assumptions

- **Language**: Market headlines are primarily in English.
- **Frequency**: Ingestion and forecasting cycles follow the Africa/Cairo business calendar.
- **Baseline Rule**: A simple statistical or machine learning baseline MUST be operational before complex deep learning models are introduced.
- **Data Availability**: Reliable historical data exists for at least the past 12 months for primary cotton indices.

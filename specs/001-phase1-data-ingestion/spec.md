# Feature Specification: Phase 1 — Foundation & Data Ingestion

**Feature Branch**: `001-phase1-data-ingestion`  
**Created**: March 28, 2026  
**Status**: Ready for implementation  
**Input**: User description: "Read and create detailed oriented specification for Phase 1 — Foundation & Data Ingestion (Week 1) only using best practices"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Daily data ingestion success (Priority: P1)

A data engineer needs the system to ingest and normalize daily cotton market data so the downstream forecasting pipeline can operate on a reliable price history.

**Why this priority**: Daily ingestion is the foundation for all downstream analytics, model training, and alerts.

**Independent Test**: Execute the ingestion pipeline for the primary sources and verify new normalized records appear in the `price_history` repository with source health updates.

**Acceptance Scenarios**:

1. **Given** the ingestion scheduler is triggered for a new day, **When** primary feed sources respond successfully, **Then** the system stores normalized price records in the database and marks the sources healthy.
2. **Given** one primary source returns stale or missing data, **When** the pipeline runs fallback scrapers, **Then** the system records the fallback data and updates source health to indicate degraded availability.

---

### User Story 2 - Source health monitoring (Priority: P2)

An operations analyst needs visibility into each data source so they can identify failed or stale inputs before model forecasts are produced.

**Why this priority**: Source health is required to trust the data feed and to avoid relying on stale or missing prices.

**Independent Test**: Run the source health updater against live and simulated failing endpoints and confirm the health state is stored and categorized correctly.

**Acceptance Scenarios**:

1. **Given** a source returns current data within expected thresholds, **When** the health updater evaluates it, **Then** the source health state is recorded as live.
2. **Given** a source has not reported fresh data for more than 24 hours, **When** the health updater evaluates it, **Then** the source health state is recorded as stale and the fallback path is flagged.

---

### User Story 3 - Data validation and normalization (Priority: P3)

A developer needs the ingestion pipeline to validate raw prices and convert them to USD so downstream consumers can rely on a consistent currency basis.

**Why this priority**: Normalized prices prevent inconsistent units and currency mismatches in model training and reporting.

**Independent Test**: Ingest sample raw data with local currency values and verify the normalized USD values are stored alongside the original source metadata.

**Acceptance Scenarios**:

1. **Given** a raw price is available in a foreign currency, **When** the conversion module processes it, **Then** the record is stored in USD and the original currency details are retained for audit.

---

### Edge Cases

- Primary data sources return partial data for the current day; the pipeline must still ingest available prices and mark missing sources as degraded.
- A source is temporarily unreachable; the system must record the failure, retry according to defined limits, and activate fallback sources when available.
- Currency conversion rates are unavailable for a given timestamp; the system must flag the affected records and prevent invalid USD normalization.
- Duplicate records are received from a source; the ingestion pipeline must deduplicate on source, timestamp, and price attributes before persistence.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST ingest daily cotton commodity prices from primary sources including CAI spot and MCX futures.
- **FR-002**: The system MUST ingest fallback data from secondary sources such as CCFGroup, Fibre2Fashion, and IEA when a primary source is unavailable.
- **FR-003**: The system MUST normalize all ingested price records to USD before storing them in the `price_history` repository.
- **FR-004**: The system MUST record source health for each data source, including live, stale, degraded, and failed states.
- **FR-005**: The system MUST support a daily end-to-end validation flow that confirms ingestion results, source health updates, and persistence of normalized price history.
- **FR-006**: The system MUST deduplicate incoming records by source, timestamp, and price to avoid duplicate persisted entries.
- **FR-007**: The system MUST flag and retain raw source metadata for each ingested record to support traceability and audit.

### Key Entities *(include if feature involves data)*

- **Price History Record**: Represents a single normalized commodity price entry with source metadata, timestamp, currency, and USD-converted value.
- **Source Health Record**: Represents the status of a data source, including freshness, availability state, last successful update, and fallback activation.
- **Ingestion Source**: Represents a configured feed endpoint or scraper, including source type, priority, and fallback relationships.
- **Currency Conversion Record**: Represents an exchange rate or conversion event used to normalize raw prices into USD.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The ingestion baseline is complete for at least 95% of configured Phase 1 primary sources (CAI spot and MCX futures) each day during initial validation.
- **SC-002**: Source health status is updated within 5 minutes of ingestion completion for all evaluated sources.
- **SC-003**: At least 95% of stored price history entries include a valid USD-normalized value and source metadata.
- **SC-004**: The system records fallback data for any primary source failure and retains a clear degraded state for the affected source.
- **SC-005**: Daily end-to-end ingestion validation produces a pass/fail result and identifies any missing or stale sources.

## Assumptions

- Phase 1 is scoped to data ingestion and source health tracking only; user-facing reporting and forecasting are out of scope.
- The Phase 1 primary ingestion sources are CAI spot and MCX futures; fallback sources are CCFGroup, Fibre2Fashion, and IEA.
- A relational storage layer is available and accessible for `price_history` and `source_health` persistence.
- Primary source endpoints and fallback provider feeds have sufficient access and response characteristics for scheduled ingestion.
- Exchange rate data for currency conversion is available from existing feeds or a reliable external service.
- The first iteration focuses on data accuracy, traceability, and pipeline reliability rather than performance optimization.


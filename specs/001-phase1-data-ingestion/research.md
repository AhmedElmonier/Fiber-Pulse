# Phase 0 Research: Phase 1 — Foundation & Data Ingestion

## Decision: Python data pipeline with PostgreSQL storage

- Chosen: Python 3.12 with Poetry for dependency management and reproducible environments.
- Rationale: Python has strong ecosystem support for data ingestion, async HTTP fetching, SQL-based persistence, and rapid prototyping. Poetry ensures lockfile-based installs and clean isolation.
- Alternatives considered: Go for raw performance, but it adds delivery risk for a phase focused on reliable data contracts and source health instead of high-throughput streaming. Node.js was rejected because the project requires tight PostgreSQL integration and a mature Python data science ecosystem.

## Decision: Async HTTP ingestion with HTTPX and retry/backoff

- Chosen: HTTPX for HTTP scraping and feed access, backed by configurable retry logic, timeouts, and response validation.
- Rationale: HTTPX supports sync and async APIs with the same interface, which makes it easy to build both scheduled batch ingestion and parallel source fetchers. It also handles connection pooling and modern TLS behavior better than legacy requests.
- Alternatives considered: requests was simpler, but it lacks first-class async support and would make parallel source ingestion harder to scale as source count grows.

## Decision: PostgreSQL with schema contracts and pgvector readiness

- Chosen: PostgreSQL for authoritative storage of normalized price history and source health state; reserve `pgvector` for future embedding-based similarity analysis.
- Rationale: PostgreSQL is the best choice for structured time-series-like transactional data with audit metadata and schema enforcement. It also supports strong indexing for deduplication and historical queries.
- Alternatives considered: NoSQL or flat file storage was rejected because Phase 1 requires strict data integrity, transactional writes, and explicit health-state contracts.

## Decision: Internal data contracts over external APIs

- Chosen: Define internal ingestion contracts for `PriceHistoryRecord`, `SourceHealthRecord`, and `CurrencyConversionRecord` rather than exposing a public HTTP API in Phase 1.
- Rationale: Phase 1 scope is foundation and data ingestion, so the most important contract is the data model and ingestion interface. External API work is deferred to later phases.
- Alternatives considered: Building a REST ingestion API now would add unnecessary surface area and delay the core telemetry and normalization work.

## Decision: Focus on traceability and fallback behavior

- Chosen: Preserve raw source metadata and health state for every record, and model fallback sources explicitly in the ingestion pipeline.
- Rationale: The constitution requires data integrity and operational transparency. That means staleness, fallback activity, and conversion provenance must all be retained alongside normalized values.
- Alternatives considered: Storing only normalized USD values would be simpler, but it would eliminate auditability and make failure diagnosis much harder.

## Research summary

- Primary goal: establish a reliable ingestion foundation for cotton market data with strong source health visibility and USD normalization.
- Scope: ingest CAI spot and MCX futures first, with fallback support for CCFGroup, Fibre2Fashion, and IEA.
- Outcome: define precise data contracts, validation rules, and a Python-backed pipeline architecture that can be extended into forecasting and Telegram reporting.

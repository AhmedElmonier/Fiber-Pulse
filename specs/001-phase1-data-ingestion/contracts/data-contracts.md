# Data Contracts: Phase 1 — Foundation & Data Ingestion

## Contract: PriceHistoryRecord

A single canonical price record produced by the ingestion pipeline.

```json
{
  "id": "uuid",
  "source_name": "string",
  "source_type": "spot|future|fallback|macro",
  "timestamp_utc": "string (ISO-8601 UTC)",
  "commodity": "string",
  "region": "string | null",
  "raw_price": "decimal",
  "raw_currency": "string",
  "normalized_usd": "decimal",
  "conversion_rate": "decimal | null",
  "normalized_at": "string (ISO-8601 UTC)",
  "quality_flags": {"stale": true|false, "fallback": true|false, "fallback_source": "string|undefined"},
  "metadata": {"raw_payload": {...}, "normalized_at": "...", "source_type": "...", "extraction_context": {...}},
  "created_at": "string (ISO-8601 UTC)",
  "updated_at": "string (ISO-8601 UTC)"
}
```

### Contract invariants

- `normalized_usd` MUST be present and positive.
- `raw_currency` MUST be a valid ISO 4217 3-letter currency code.
- `timestamp_utc` MUST be timezone-aware UTC (stored as `datetime(timezone=True)`).
- `quality_flags.fallback` MUST be `true` when the record was sourced from a fallback provider.
- `quality_flags.fallback_source` MUST contain the source name when fallback is active.
- `metadata.raw_payload` MUST contain the original source payload or extraction details.
- `metadata.normalized_at` MUST contain the ISO-8601 timestamp when normalization occurred.

### Implementation notes

- **Model**: `models/price_history.PriceHistoryRecord`
- **Schema**: `db/schema.PriceHistory`
- **Persistence**: `db/repository.Repository.insert_price_record()` / `insert_price_records_batch()`
- **Unique constraint**: `(source_name, timestamp_utc, raw_price)` prevents duplicate ingestion.

## Contract: SourceHealthRecord

Represents the operational health state of a configured ingestion source.

```json
{
  "id": "uuid",
  "source_name": "string",
  "status": "live|stale|degraded|failed",
  "last_success_at": "string (ISO-8601 UTC) | null",
  "last_checked_at": "string (ISO-8601 UTC)",
  "fallback_active": true|false,
  "stale_duration_minutes": "integer | null",
  "remarks": "string | null",
  "details": {"retry_count": int, "last_attempt": "...", ...},
  "created_at": "string (ISO-8601 UTC)",
  "updated_at": "string (ISO-8601 UTC)"
}
```

### Contract invariants

- `status` MUST be one of: `live`, `stale`, `degraded`, `failed`.
- `fallback_active` MUST be `true` if the source is using fallback data.
- `last_checked_at` MUST always be set (required field).
- `details.retry_count` MUST track consecutive failed ingestion attempts.
- `details.last_attempt` MUST contain the ISO-8601 timestamp of the last ingestion attempt.

### State transitions

| From | To | Condition |
|------|-----|-----------|
| live | stale | Data age exceeds `stale_threshold_minutes` (default: 60) |
| stale | degraded | Fallback ingestion is activated |
| degraded | live | Primary source returns healthy data |
| any | failed | Ingestion attempts exceed `max_retry_attempts` (default: 3) without recovery |

### Implementation notes

- **Model**: `models/source_health.SourceHealthRecord`
- **Schema**: `db/schema.SourceHealth`
- **Persistence**: `db/repository.Repository.upsert_source_health()`
- **Evaluator**: `agents/source_health.SourceHealthEvaluator`
- **Default thresholds**: `stale_threshold_minutes=60`, `failed_threshold_minutes=1440`, `max_retry_attempts=3`

## Contract: CurrencyConversionRecord

Defines the authoritative currency rate used for USD normalization.

```json
{
  "id": "uuid",
  "currency": "string",
  "rate_to_usd": "decimal",
  "rate_timestamp": "string (ISO-8601 UTC)",
  "source_name": "string",
  "retrieved_at": "string (ISO-8601 UTC)",
  "metadata": {"..."} | null
}
```

### Contract invariants

- `rate_to_usd` MUST be present and positive.
- `currency` MUST be a valid ISO 4217 3-letter currency code.
- `rate_timestamp` MUST reflect the timestamp of the underlying conversion rate.
- `retrieved_at` MUST contain the timestamp when the rate was fetched by the system.

### Implementation notes

- **Model**: `models/currency_conversion.CurrencyConversionRecord`
- **Schema**: `db/schema.CurrencyConversion`
- **Persistence**: `db/repository.Repository.insert_currency_conversion()`, `get_latest_rate()`
- **Converter**: `utils/usd_converter.USDConverter`

## Contract: IngestionSource

Represents a configured data source with priority and fallback relationships.

```json
{
  "source_name": "string (primary key)",
  "display_name": "string",
  "priority": "integer",
  "source_url": "string | null",
  "category": "primary|fallback|currency_rate|utility",
  "active": true|false,
  "fallback_to": "string | null",
  "last_run_at": "string (ISO-8601 UTC) | null",
  "config": {"..."},
  "created_at": "string (ISO-8601 UTC)",
  "updated_at": "string (ISO-8601 UTC)"
}
```

### Contract invariants

- `source_name` MUST be unique (primary key).
- `priority` MUST be a positive integer (lower values = higher priority).
- `category` MUST be one of: `primary`, `fallback`, `currency_rate`, `utility`.
- `active` MUST be `false` if the source should be skipped during ingestion.

### Implementation notes

- **Model**: `models/ingestion_source.IngestionSource`
- **Schema**: `db/schema.IngestionSource`
- **Persistence**: `db/repository.Repository.upsert_ingestion_source()`, `get_active_sources()`

## Ingestion Interface Contract

All ingestion source adapters MUST implement the `BaseScraper` interface and produce payloads conforming to this contract:

```json
{
  "source_name": "string",
  "timestamp_utc": "string (ISO-8601 UTC)",
  "commodity": "string",
  "raw_price": "decimal",
  "raw_currency": "string",
  "region": "string | null",
  "metadata": {"..."}
}
```

### Adapter contract rules

- Adapter output MUST include `source_name` and `timestamp_utc`.
- Adapter output MUST NOT include normalized values; normalization is performed by `agents/normalizer.Normalizer`.
- Validation MUST reject records missing any required field.
- Each adapter MUST annotate fallback source records with `metadata.fallback_source` when applicable.
- Adapter `scrape()` method MUST return `ScraperResult` with `success`, `records`, and optional `error`.

### Implementation notes

- **Base class**: `agents.base_scraper.BaseScraper`
- **Primary adapters**: `agents.cai_spot_scraper.CAISpotScraper`, `agents.mcx_futures_scraper.MCXFuturesScraper`
- **Fallback adapters**: `agents.ccfgroup_scraper.CCFGroupScraper`, `agents.fibre2fashion_scraper.Fibre2FashionScraper`
- **Utility adapters**: `agents.iea_scraper.IEAScraper`
- **Orchestrator**: `agents.data_fetcher.DataFetcher`

## Quality Flags Contract

Records include `quality_flags` to track data quality indicators:

```json
{
  "stale": true|false,
  "fallback": true|false,
  "fallback_source": "string (when fallback=true)"
}
```

### Flag semantics

- `stale`: Data is older than the configured freshness threshold.
- `fallback`: Data was sourced from a fallback provider due to primary failure.
- `fallback_source`: The name of the fallback source (only present when `fallback=true`).

## Change control

Phase 1 data contracts are authoritative for the ingestion foundation. Any schema or contract changes MUST be tracked in the feature plan and validated against the constitution principles for data integrity and traceability.

### Version history

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-28 | Initial contract definitions |
| 1.1.0 | 2026-03-30 | Added implementation notes, quality flags contract, and state transitions |
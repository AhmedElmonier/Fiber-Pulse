# Data Model: Phase 1 — Foundation & Data Ingestion

## Entities

### PriceHistoryRecord
- `id` (UUID) — unique primary key.
- `source_name` (string) — canonical source identifier, e.g. `cai_spot`, `mcx_futures`, `ccfgroup`.
- `source_type` (enum) — `spot`, `future`, `fallback`, `macro`.
- `timestamp_utc` (datetime, UTC) — recorded timestamp for the underlying market price.
- `commodity` (string) — product type, e.g. `cotton`.
- `region` (string, nullable) — optional delivery region or location context.
- `raw_price` (decimal) — original reported price value.
- `raw_currency` (string) — original price currency code.
- `normalized_usd` (decimal) — USD-converted price value.
- `conversion_rate` (decimal, nullable) — exchange rate used for USD normalization.
- `normalized_at` (datetime, UTC) — time the conversion was applied.
- `quality_flags` (jsonb) — validation and source health indicators, e.g. `{"stale": false, "fallback": true}`.
- `metadata` (jsonb) — raw source payload, extraction context, and audit details.
- `created_at` (datetime) — insertion timestamp.
- `updated_at` (datetime) — last update timestamp.

### SourceHealthRecord
- `id` (UUID) — unique primary key.
- `source_name` (string) — canonical source identifier.
- `status` (enum) — `live`, `stale`, `degraded`, `failed`.
- `last_success_at` (datetime, UTC, nullable) — last successful ingest time.
- `last_checked_at` (datetime, UTC) — most recent health evaluation time.
- `fallback_active` (boolean) — whether fallback data was used for this source.
- `stale_duration_minutes` (integer, nullable) — how long the source has been stale.
- `remarks` (string, nullable) — human-readable health details.
- `details` (jsonb, nullable) — extended health metadata and diagnostics.
- `created_at` (datetime) — insertion timestamp.
- `updated_at` (datetime) — last update timestamp.

### IngestionSource
- `source_name` (string, primary key) — canonical identifier.
- `display_name` (string) — human-friendly source label.
- `priority` (integer) — primary sources have lower numeric priority than fallback sources.
- `source_url` (string, nullable) — feed endpoint or documentation URL.
- `type` (enum) — `primary`, `fallback`, `currency_rate`, `utility`.
- `active` (boolean) — configured and enabled.
- `fallback_to` (string, nullable) — linked fallback source for degraded flow.
- `last_run_at` (datetime, UTC, nullable) — last ingestion attempt.
- `created_at` (datetime) — insertion timestamp.
- `updated_at` (datetime) — last update timestamp.

### CurrencyConversionRecord
- `id` (UUID) — unique primary key.
- `currency` (string) — currency code, e.g. `INR`, `CNY`, `USD`.
- `rate_to_usd` (decimal) — exchange rate used to normalize values.
- `rate_timestamp` (datetime, UTC) — timestamp for the rate.
- `source_name` (string) — source of the conversion rate.
- `retrieved_at` (datetime, UTC) — when the rate was fetched.
- `metadata` (jsonb, nullable) — raw provider payload.

## Relationships

- `PriceHistoryRecord.source_name` references `IngestionSource.source_name`.
- `PriceHistoryRecord.raw_currency` references `CurrencyConversionRecord.currency` indirectly by timestamp for audit.
- `SourceHealthRecord.source_name` references `IngestionSource.source_name`.

## Validation Rules

- `source_name`, `timestamp_utc`, `raw_price`, and `normalized_usd` MUST be present for every price record.
- `normalized_usd` MUST be positive and computed from `raw_price` via a validated currency rate.
- Duplicate price ingestion MUST be prevented by a unique constraint on `(source_name, timestamp_utc, raw_price)`.
- `quality_flags` MUST record whether fallback or stale data was used.
- `SourceHealthRecord.status` MUST be one of `live`, `stale`, `degraded`, or `failed`.
- `last_checked_at` MUST always be set for health records.
- `fallback_active` MUST be true whenever a fallback source was used due to primary failure.

## State & Transitions

### Source health state machine
- `live` -> `stale` when data age exceeds configured freshness threshold.
- `stale` -> `degraded` when fallback ingestion is activated.
- `degraded` -> `live` when primary source returns healthy data and fallback is no longer needed.
- Any state -> `failed` when ingestion attempts exceed retry limits without successful recovery.

### Price ingestion lifecycle
1. Raw data fetched from a source.
2. Data validated and normalized to USD.
3. Record persisted in `price_history` with raw payload metadata.
4. Source health updated in `source_health`.
5. Fallback records are flagged and maintain a clear provenance trail.

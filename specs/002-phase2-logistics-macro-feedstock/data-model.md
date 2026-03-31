# Data Model: Phase 2 — Logistics, Macro & Feedstock

## Entities

### FreightRate
- `id` (UUID) — unique primary key.
- `source_name` (string) — canonical source identifier, e.g. `ccfi_med`, `drewry_wci`.
- `route` (string) — logistics route or corridor, e.g. `Mediterranean`.
- `timestamp_utc` (datetime, UTC) — observation timestamp for the freight rate.
- `raw_rate` (float) — original reported freight rate.
- `raw_currency` (string) — original currency code.
- `normalized_usd` (float) — USD-converted freight rate.
- `conversion_rate` (float, nullable) — exchange rate applied to normalize the value.
- `quality_flags` (jsonb) — health flags for stale, fallback, and confidence state.
- `metadata` (jsonb) — raw source payload, extraction context, and provenance.
- `created_at` (datetime) — insertion timestamp.
- `updated_at` (datetime) — last update timestamp.

### MacroFeedRecord
- `id` (UUID) — unique primary key.
- `source_name` (string) — canonical macro feed source identifier, e.g. `fx_usd_inr`, `fx_usd_cny`, `oil_spot`, `electricity`.
- `source_type` (enum) — `macro`.
- `timestamp_utc` (datetime, UTC) — observation timestamp.
- `commodity` (string) — logical feed label, e.g. `usd_inr`, `usd_cny`, `oil_spot`, `electricity`.
- `raw_price` (float) — original feed value.
- `raw_currency` (string) — original currency code.
- `normalized_usd` (float) — USD-equivalent value after conversion.
- `conversion_rate` (float, nullable) — exchange rate used for normalization.
- `normalized_at` (datetime, UTC) — time the conversion was performed.
- `quality_flags` (jsonb) — health flags for stale, fallback, and confidence state.
- `metadata` (jsonb) — raw source payload and diagnostic context.
- `created_at` (datetime) — insertion timestamp.
- `updated_at` (datetime) — last update timestamp.

### SourceHealthRecord
- `id` (UUID) — unique primary key.
- `source_name` (string) — canonical source identifier.
- `status` (enum) — `live`, `stale`, `degraded`, `failed`.
- `last_success_at` (datetime, UTC, nullable) — last successful ingest timestamp.
- `last_checked_at` (datetime, UTC) — time of the most recent health evaluation.
- `fallback_active` (boolean) — true when fallback data is currently in use.
- `stale_duration_minutes` (integer, nullable) — elapsed staleness duration.
- `remarks` (string, nullable) — brief human-readable health explanation.
- `details` (jsonb, nullable) — extended health diagnostics and metadata.
- `created_at` (datetime) — insertion timestamp.
- `updated_at` (datetime) — last update timestamp.

### IngestionSource
- `source_name` (string, primary key) — canonical source identifier.
- `display_name` (string) — human-readable label.
- `priority` (integer) — primary < fallback priority.
- `category` (enum) — `primary`, `fallback`, `currency_rate`, `utility`.
- `active` (boolean) — enabled source.
- `fallback_to` (string, nullable) — linked fallback source.
- `last_run_at` (datetime, UTC, nullable) — last ingestion attempt.
- `config` (jsonb) — source-specific scraper or feed configuration.
- `created_at` (datetime) — insertion timestamp.
- `updated_at` (datetime) — last update timestamp.

## Relationships

- `FreightRate.source_name` and `MacroFeedRecord.source_name` reference `IngestionSource.source_name`.
- `SourceHealthRecord.source_name` references `IngestionSource.source_name`.
- Macro feeds in `price_history` use `SourceType.MACRO` and can be joined with `currency_conversion` history by timestamp for validation.

## Validation Rules

- `source_name`, `timestamp_utc`, `raw_price`, and `normalized_usd` MUST be present for all normalized records.
- `raw_currency` MUST be a 3-letter ISO currency code.
- `normalized_usd` MUST be computed using a validated conversion rate and MUST be positive.
- `quality_flags` MUST include `stale`, `fallback`, and any `fallback_source` provenance.
- `status` in `SourceHealthRecord` MUST be one of `live`, `stale`, `degraded`, `failed`.
- A source is stale if no fresh data arrives within 48 hours of expected publication.
- Fallback records MUST preserve `fallback_active: true` and a `fallback_source` identifier.

## State & Transitions

### Source health state machine
- `live` -> `stale` when a configured source fails to deliver fresh data within 48 hours.
- `stale` -> `degraded` when fallback ingestion is activated for the source.
- `degraded` -> `live` when the primary source returns healthy, fresh data and fallback is no longer needed.
- Any state -> `failed` when retry limits are exceeded or the source is unavailable for an extended period.

### Record ingestion lifecycle
1. Raw data fetched from a logistics or macro source.
2. Payload validated and normalized, including USD conversion.
3. Normalized record persisted with audit metadata.
4. Source health updated in `source_health`.
5. Fallback records are flagged and maintain provenance in `quality_flags`.

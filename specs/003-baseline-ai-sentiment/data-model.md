# Data Model: Phase 3 — Baseline AI + Sentiment

## Entities

### SentimentEvent
- `id` (UUID) — unique primary key.
- `headline` (string) — the raw text of the headline.
- `source_name` (string) — canonical source identifier.
- `timestamp_utc` (datetime, UTC) — when the headline was published.
- `sentiment_score` (enum) — `bullish`, `bearish`, `neutral`.
- `confidence` (float) — numeric confidence in the scoring (0.0 to 1.0).
- `engine_version` (string) — version of the sentiment engine used.
- `metadata` (jsonb) — original payload and keyword hits.
- `created_at` (datetime) — insertion timestamp.

### Forecast
- `id` (UUID) — unique primary key.
- `target_source` (string) — the source name being predicted (e.g., `cai_spot`).
- `timestamp_utc` (datetime, UTC) — the observation time this forecast was generated.
- `target_timestamp_utc` (datetime, UTC) — the future time being predicted.
- `horizon_hours` (integer) — forecast horizon (e.g., 24).
- `predicted_value` (float) — point estimate (normalized USD).
- `lower_bound` (float) — lower confidence interval bound.
- `upper_bound` (float) — upper confidence interval bound.
- `confidence_level` (float) — e.g., 0.95 for a 95% interval.
- `model_version` (string) — identifier for the model that generated this.
- `is_decayed` (boolean) — true if CI was widened due to stale inputs.
- `created_at` (datetime) — insertion timestamp.

### HistoricalOnboardingLog
- `id` (UUID) — unique primary key.
- `file_name` (string) — name of the ingested file.
- `timestamp_utc` (datetime, UTC) — when ingestion occurred.
- `record_count` (integer) — number of records successfully ingested.
- `status` (string) — `success`, `failed`, `partial`.
- `error_summary` (text, nullable) — details of validation failures.
- `metadata` (jsonb) — ingest parameters and user who triggered it.

## Relationships

- `SentimentEvent.source_name` references `IngestionSource.source_name`.
- `Forecast.target_source` references `IngestionSource.source_name`.
- `Forecast` results can be compared against subsequent `PriceHistory` records for MAE validation.

## Validation Rules

- `sentiment_score` MUST be one of `bullish`, `bearish`, `neutral`.
- `predicted_value`, `lower_bound`, and `upper_bound` MUST be positive floats.
- `upper_bound` MUST be greater than or equal to `predicted_value`.
- `lower_bound` MUST be less than or equal to `predicted_value`.
- `target_timestamp_utc` MUST be in the future relative to `timestamp_utc`.

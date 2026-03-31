# Data Contracts: Phase 2 — Logistics, Macro & Feedstock

## Raw Source Payload Contract

All ingested sources MUST emit raw payloads conforming to this contract before normalization.

```json
{
  "source_name": "string",
  "timestamp_utc": "ISO-8601 datetime string or UTC datetime",
  "commodity": "string",
  "region": "string|null",
  "raw_price": "positive float",
  "raw_currency": "3-letter currency code",
  "metadata": "object|null"
}
```

Required fields:
- `source_name`
- `timestamp_utc`
- `commodity`
- `raw_price`
- `raw_currency`

Optional fields:
- `region`
- `metadata`

## Normalized Freight Record Contract

Freight data is persisted with logistics-specific metadata and USD normalization.

```json
{
  "source_name": "string",
  "route": "string",
  "timestamp_utc": "ISO-8601 datetime",
  "raw_rate": "positive float",
  "raw_currency": "3-letter currency code",
  "normalized_usd": "positive float",
  "conversion_rate": "float|null",
  "quality_flags": {
    "stale": "boolean",
    "fallback": "boolean",
    "fallback_source": "string|null"
  },
  "metadata": "object"
}
```

## Normalized Macro Record Contract

Macro feed records use the existing normalized price contract with `source_type = macro`.

```json
{
  "source_name": "string",
  "source_type": "macro",
  "timestamp_utc": "ISO-8601 datetime",
  "commodity": "string",
  "raw_price": "positive float",
  "raw_currency": "3-letter currency code",
  "normalized_usd": "positive float",
  "conversion_rate": "float|null",
  "quality_flags": {
    "stale": "boolean",
    "fallback": "boolean",
    "fallback_source": "string|null"
  },
  "metadata": "object"
}
```

## Source Health Contract

Source health is the operational contract that tracks ingest confidence.

```json
{
  "source_name": "string",
  "status": "live|stale|degraded|failed",
  "last_success_at": "ISO-8601 datetime|null",
  "last_checked_at": "ISO-8601 datetime",
  "fallback_active": "boolean",
  "stale_duration_minutes": "integer|null",
  "remarks": "string|null",
  "details": "object|null"
}
```

## Contract Guarantees

- Every normalized record MUST preserve the raw payload in `metadata` for auditability.
- Every record MUST include `quality_flags` to signal stale or fallback-derived values.
- Stale detection MUST be applied consistently across logistics and macro sources.
- Fallback activation MUST preserve `fallback_source` provenance.

# Unified Repository API

This document describes the unified interface for querying normalized price history, logistics freight rates, and macroeconomic feed records in FiberPulse.

## Overview

FiberPulse persists data into three primary tables:
1. `price_history`: Spot and futures price records for cotton.
2. `freight_rates`: Logistics freight indices (e.g., CCFI, Drewry).
3. `macro_feed_records`: Macroeconomic indicators (FX rates, oil prices, electricity).

While stored in separate tables for logical separation, these records share a **standardized core schema** and can be queried through a **unified repository interface**.

## Unified Schema

All normalized records share the following core fields:

| Field | Type | Description |
|-------|------|-------------|
| `source_name` | string | Canonical identifier for the data source. |
| `timestamp_utc` | datetime | Observation timestamp in UTC. |
| `raw_price` | float | Original reported value before normalization. |
| `raw_currency` | string | 3-letter ISO currency code. |
| `normalized_usd` | float | USD-converted value. |
| `conversion_rate` | float | Exchange rate applied for normalization. |
| `quality_flags` | jsonb | Health metadata: `{"stale": bool, "fallback": bool, ...}`. |
| `metadata` | jsonb | Raw source payload and extraction context. |

## Query Interface (`db/repository.py`)

### `get_normalized_records`

Queries across multiple record types using a single method call.

**Arguments:**
- `source_types` (list[str]): List of types to include (`'spot'`, `'future'`, `'freight'`, `'macro'`).
- `source_names` (list[str]): Filter by specific source identifiers.
- `start_time` (datetime): Return records after this time.
- `end_time` (datetime): Return records before this time.
- `limit` (int): Maximum number of records to return.

**Example:**
```python
from db.repository import Repository
repo = Repository(DATABASE_URL)

# Get all macro and freight data for the last 24 hours
records = await repo.get_normalized_records(
    source_types=['macro', 'freight'],
    start_time=datetime.now(timezone.utc) - timedelta(days=1)
)

for r in records:
    print(f"{r.source_name}: {r.normalized_usd} USD")
```

### `get_records_by_health_status`

Returns records from sources that match a specific health status.

**Arguments:**
- `status` (str): Status to filter by (`'live'`, `'stale'`, `'degraded'`, `'failed'`).

**Example:**
```python
# Get records from all currently stale sources
stale_data = await repo.get_records_by_health_status('stale')
```

## Unified Orchestration

To run ingestion for a set of diverse sources, use the `UnifiedIngestionOrchestrator`:

```python
from agents.unified_ingestion_orchestrator import UnifiedIngestionOrchestrator

orchestrator = UnifiedIngestionOrchestrator(repository=repo)
results = await orchestrator.run_ingestion(['ccfi_med', 'fx_usd_inr', 'cai_spot'])

print(f"Ingested {results['summary']['total_records_ingested']} records.")
```

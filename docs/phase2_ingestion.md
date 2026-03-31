# Phase 2 Ingestion: Logistics & Macro Feeds

This document provides detailed usage examples and technical patterns for Phase 2 data ingestion in FiberPulse.

## Supported Data Sources

Phase 2 introduces the following canonical sources:

### Logistics (Freight)
- `ccfi_med`: China Containerized Freight Index (Mediterranean Route).
- `drewry_wci`: Drewry World Container Index (Shanghai-Rotterdam).

### Macroeconomic (Macro)
- `fx_usd_inr`: USD to Indian Rupee exchange rate.
- `fx_usd_cny`: USD to Chinese Yuan exchange rate.
- `oil_spot`: Brent Oil spot prices.
- `electricity`: Base load electricity rates.

## Basic Ingestion Usage

Individual sources can be ingested using the `DataFetcher`:

```python
import asyncio
from db.repository import Repository
from agents.data_fetcher import DataFetcher

async def ingest_logistics():
    repo = Repository(DATABASE_URL)
    fetcher = DataFetcher(repository=repo)
    
    # Ingest a specific freight source
    result = await fetcher.ingest_source("ccfi_med")
    
    if result.success:
        print(f"Successfully ingested {result.records_ingested} records from CCFI.")
    else:
        print(f"Ingestion failed: {result.error}")

asyncio.run(ingest_logistics())
```

## Fallback Behavior

Phase 2 features an automatic fallback chain resolution. If a primary source (like `ccfi_med`) fails or returns stale data, the orchestrator automatically attempts fallback sources.

```python
# Force fallback behavior by disabling primary or simulating failure
# DataFetcher will automatically look up the fallback (e.g., drewry_wci for ccfi_med)
result = await fetcher.ingest_source("ccfi_med", use_fallback=True)

if result.fallback_used:
    print(f"Primary source failed. Data obtained from fallback: {result.source_name}")
```

## Source Health Monitoring

Source health is evaluated against a **48-hour staleness threshold**.

### Querying Health Status

Use the `Repository` to check the current health of ingestion sources:

```python
from db.repository import Repository
from models.source_health import HealthStatus

repo = Repository(DATABASE_URL)

# Get all sources that are currently DEGRADED (using fallback)
degraded_sources = await repo.get_sources_by_status(HealthStatus.DEGRADED)

for source in degraded_sources:
    print(f"Source {source.source_name} is degraded. Remarks: {source.remarks}")
```

### Health State Machine

| Current State | Event | Next State | Reason |
|---------------|-------|------------|--------|
| `LIVE` | Age > 48h | `STALE` | No fresh data received within threshold. |
| `STALE` | Fallback Active | `DEGRADED` | Primary is stale, but fallback data is arriving. |
| `STALE/DEGRADED` | Primary Success | `LIVE` | Fresh data received from primary source. |
| `ANY` | Retries > 3 | `FAILED` | Persistent failures without recovery. |

## Unified Querying

Downstream consumers (forecasting, UI) should use the unified interface to query across different tables:

```python
# Unified query for all logistics and macro indicators
records = await repo.get_normalized_records(
    source_types=['freight', 'macro'],
    limit=50
)

for record in records:
    # All records share source_name, timestamp_utc, and normalized_usd
    print(f"[{record.timestamp_utc}] {record.source_name}: {record.normalized_usd} USD")
```

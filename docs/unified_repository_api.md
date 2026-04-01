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

## Sentiment Events Query Interface

### `get_sentiment_events`

Queries market headline sentiment events.

**Arguments:**
- `source_name` (str): Filter by source identifier.
- `start_time` (datetime): Return events after this time.
- `end_time` (datetime): Return events before this time.
- `sentiment_label` (str): Filter by sentiment (`'bullish'`, `'bearish'`, `'neutral'`).
- `limit` (int): Maximum number of records to return.

**Example:**
```python
# Get latest bullish sentiment events
bullish_events = await repo.get_sentiment_events(
    sentiment_label='bullish',
    limit=10
)

for e in bullish_events:
    print(f"{e.headline}: {e.sentiment_score} (confidence: {e.confidence})")
```

### `insert_sentiment_event`

Persists a sentiment-scored market headline.

**Example:**
```python
from models.sentiment_event import SentimentEvent, SentimentLabel
from datetime import datetime, timezone

event = SentimentEvent(
    headline="Cotton prices surge on strong demand",
    source_name="reuters",
    timestamp_utc=datetime.now(timezone.utc),
    sentiment_score=SentimentLabel.BULLISH,
    confidence=0.85,
    metadata={"matched_keywords": ["surge", "strong", "demand"]}
)

await repo.insert_sentiment_event(event)
```

## Forecasts Query Interface

### `get_forecasts`

Queries generated price forecasts with confidence intervals.

**Arguments:**
- `target_source` (str): Filter by target source name.
- `start_time` (datetime): Return forecasts generated after this time.
- `end_time` (datetime): Return forecasts generated before this time.
- `limit` (int): Maximum number of records to return.

**Example:**
```python
# Get latest forecasts for CAI spot
forecasts = await repo.get_forecasts(
    target_source='cai_spot',
    limit=5
)

for f in forecasts:
    print(f"{f.target_source}: {f.predicted_value:.2f} "
          f"[{f.lower_bound:.2f}, {f.upper_bound:.2f}] "
          f"(decayed: {f.is_decayed})")
```

### `insert_forecast`

Persists a price forecast with confidence intervals.

**Example:**
```python
from models.forecast import Forecast
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
target_ts = now + timedelta(hours=24)

forecast = Forecast(
    target_source="cai_spot",
    timestamp_utc=now,
    target_timestamp_utc=target_ts,
    horizon_hours=24,
    predicted_value=85.50,
    lower_bound=80.00,
    upper_bound=91.00,
    confidence_level=0.95,
    is_decayed=False
)

await repo.insert_forecast(forecast)
```

## Sentiment & Forecast Orchestration

To generate forecasts and process sentiment in a pipeline:

```python
from agents.forecast import generate_forecast
from agents.data_fetcher import process_market_headlines
from nlp.keyword_scorer import KeywordScorer

# Generate daily forecast
forecast = await generate_forecast(repo, target_source="cai_spot")

# Process market headlines for sentiment
headlines = [
    {"text": "Cotton surge on strong demand", "source": "reuters"},
    {"text": "Prices drop on weak demand", "source": "ap"}
]
sentiment_results = await process_market_headlines(repo, headlines)

print(f"Forecast: {forecast.predicted_value}")
print(f"Sentiment events: {len(sentiment_results)} scored")
```

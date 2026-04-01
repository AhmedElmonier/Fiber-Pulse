# Quickstart: Phase 3 — Baseline AI + Sentiment

## Goal
Onboard historical data, score market sentiment, and generate the first AI-driven price forecasts.

## 1. Onboard Historical Data
Use the CLI to ingest historical CSV data into the repository.

```bash
# Example: Ingesting CAI historical data
fiberpulse ingest-history data/historical/cai_2023.csv
```

## 2. Run Sentiment Scoring
Trigger the keyword-based sentiment engine for recent headlines.

```python
import asyncio
from agents.data_fetcher import DataFetcher
from nlp.keyword_scorer import KeywordScorer

async def run_sentiment_scoring():
    # Fetch headlines and score them
    fetcher = DataFetcher()
    results = await fetcher.ingest_source("google_news_cotton")
    return results

# This snippet is intended to be run within an async context
if __name__ == "__main__":
    asyncio.run(run_sentiment_scoring())
```

## 3. Generate Price Forecasts
Execute the baseline XGBoost model to generate a 24-hour outlook.

```bash
# Run the daily forecast cycle
fiberpulse forecast --target cai_spot
```

## 4. Verify Results
Check the database for generated artifacts.

```sql
-- Check latest forecasts
SELECT target_source, predicted_value, lower_bound, upper_bound, is_decayed
FROM forecasts
ORDER BY timestamp_utc DESC
LIMIT 5;

-- Check sentiment events
SELECT headline, sentiment_score, confidence
FROM sentiment_events
ORDER BY timestamp_utc DESC
LIMIT 10;
```

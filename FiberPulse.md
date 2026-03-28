# PRD: FiberPulse AI — Final Implementation Build v8.0
> **Revised & Expanded Edition** — Includes technical specs, code scaffolding, DB schema, and week-by-week roadmap.

---

## Table of Contents
1. [Project Metadata](#1-project-metadata)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Technical Stack](#3-technical-stack)
4. [Data Architecture](#4-data-architecture)
5. [Database Schema](#5-database-schema)
6. [AI & Predictive Logic](#6-ai--predictive-logic)
7. [Sentiment Analysis Engine](#7-sentiment-analysis-engine)
8. [Functional Features & Interface](#8-functional-features--interface)
9. [Visual Intelligence](#9-visual-intelligence)
10. [Alert System](#10-alert-system)
11. [Code Scaffolding](#11-code-scaffolding)
12. [Implementation Roadmap](#12-implementation-roadmap)
13. [Financial Performance Tracking](#13-financial-performance-tracking)
14. [Risk Register](#14-risk-register)

---

## 1. Project Metadata

| Field | Detail |
|---|---|
| **Project Name** | FiberPulse AI |
| **Version** | 8.0 |
| **Owner** | Ahmed El Monier — Procurement Senior Associate |
| **Primary Objective** | Predict Yarn and Fiber price movements 90 days in advance to align with warehouse lead times |
| **Target Markets** | India (Cotton/Yarn), China (PSF/Feedstock), Egypt (Freight Destination) |
| **Currency Standard** | USD — all internal calculations and external displays normalized to USD |
| **Revision Date** | March 2026 |

### 1.1 Problem Statement
Textile procurement decisions for Egypt-bound shipments require a 3-month forward view on fiber and yarn prices. Current market tools offer no integrated signal that combines upstream feedstock (China PSF), raw cotton (India), logistics (Suez corridor), and macro conditions (Oil, FX, Energy) into a single actionable outlook. FiberPulse AI closes this gap.

### 1.2 Success Metrics

| Metric | Target |
|---|---|
| 90-Day Forecast MAE | < 5% vs. actual settlement price |
| Alert Precision Rate | > 60% of alerts lead to a procurement action |
| Data Feed Uptime | > 95% across all primary sources |
| Procurement Alpha | Positive USD savings vs. market average within 6 months |

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      DATA INGESTION LAYER                   │
│  CAI · MCX · ICE · Cotlook · CCFGroup · CCFI · WCI · IEX   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                      │
│              LangGraph Multi-Agent Framework                │
│   Agent: DataFetcher │ Agent: Normalizer │ Agent: Alerter  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                          │
│         PostgreSQL + pgvector (Price History + Embeddings)  │
└──────────┬────────────────┬────────────────┬────────────────┘
           │                │                │
           ▼                ▼                ▼
┌──────────────┐  ┌──────────────────┐  ┌───────────────────┐
│   TFT Model  │  │ Sentiment Engine │  │  USDConverter     │
│  (PyTorch)   │  │ (FinBERT/Tier-1) │  │  (FX Normalizer)  │
└──────┬───────┘  └────────┬─────────┘  └─────────┬─────────┘
       │                   │                       │
       └───────────────────┴───────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACE LAYER                          │
│         Telegram Bot · Plotly Dashboard · Alerts           │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Multi-Agent Design (LangGraph)

| Agent | Responsibility |
|---|---|
| `DataFetcherAgent` | Pulls raw data from all sources on schedule |
| `NormalizerAgent` | Converts all prices to USD, validates ranges |
| `ForecastAgent` | Runs TFT / baseline model, outputs confidence intervals |
| `SentimentAgent` | Scores news headlines, applies intensity multipliers |
| `AlertAgent` | Monitors 3% thresholds, applies suppression filters |
| `ReporterAgent` | Assembles Telegram messages and chart snapshots |

---

## 3. Technical Stack

### 3.1 Core Dependencies

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.12"
polars = "^0.20"
torch = "^2.2"
pytorch-forecasting = "^1.0"
transformers = "^4.40"          # HuggingFace FinBERT
langgraph = "^0.1"
psycopg2-binary = "^2.9"
pgvector = "^0.2"
plotly = "^5.20"
matplotlib = "^3.8"
seaborn = "^0.13"
python-telegram-bot = "^21.0"
httpx = "^0.27"                 # Async HTTP for scrapers
selectolax = "^0.3"             # Fast HTML parsing
apscheduler = "^3.10"          # Cron scheduling
pydantic = "^2.6"               # Data validation
loguru = "^0.7"                 # Structured logging
```

### 3.2 Environment Configuration

```
# .env
TELEGRAM_BOT_TOKEN=xxxx
TELEGRAM_CHAT_ID=xxxx
POSTGRES_URL=postgresql://user:pass@localhost:5432/fiberpulse
CCF_API_KEY=xxxx                  # CCFGroup subscription key
IEX_API_KEY=xxxx                  # India Electricity Exchange
ALPHA_VANTAGE_KEY=xxxx            # FX rates (USD/INR, USD/CNY)
OPENAI_KEY=xxxx                   # Optional: GPT-4 fallback summarizer
TZ=Africa/Cairo                   # All scheduling in Egypt time
```

### 3.3 Project Directory Structure

```
fiberpulse/
├── agents/
│   ├── data_fetcher.py
│   ├── normalizer.py
│   ├── forecast.py
│   ├── sentiment.py
│   ├── alert.py
│   └── reporter.py
├── data/
│   ├── scrapers/
│   │   ├── cai_scraper.py
│   │   ├── mcx_scraper.py
│   │   ├── ccfgroup_scraper.py
│   │   ├── ccfi_scraper.py
│   │   └── iex_scraper.py
│   ├── fallbacks/
│   │   ├── fibre2fashion.py
│   │   └── iea_proxy.py
│   └── health.py               # DataSourceHealthDashboard
├── models/
│   ├── tft_model.py
│   ├── baseline_model.py       # ARIMAX/XGBoost
│   └── model_registry.py      # Promotion gate logic
├── nlp/
│   ├── keyword_scorer.py       # Tier-1 sentiment
│   └── finbert_scorer.py       # Tier-2 sentiment
├── db/
│   ├── schema.sql
│   ├── migrations/
│   └── repository.py
├── bot/
│   ├── telegram_bot.py
│   ├── commands.py
│   └── scheduler.py
├── charts/
│   ├── fan_chart.py
│   ├── heatmap.py
│   ├── freight_bar.py
│   └── alpha_scatter.py
├── utils/
│   ├── usd_converter.py
│   ├── confidence_decay.py
│   └── alert_suppressor.py
├── config.py
├── main.py
└── pyproject.toml
```

---

## 4. Data Architecture

### 4.1 Fiber & Feedstock (Daily Fetch)

| Source | Data Point | Frequency | Access Method |
|---|---|---|---|
| CAI (Cotton Association of India) | Cotton spot price (INR/Candy) | Daily | Scraper (public) |
| MCX India | Cotton futures (near/far month) | Daily | Scraper / API |
| ICE Futures | Cotton No. 2 futures (USc/lb) | Daily | API |
| Cotlook A Index | Global benchmark spot | Daily | Scraper |
| CCFGroup (Primary) | PSF spot, PTA, MEG, Operating Rates | Daily | Subscription API |
| Fibre2Fashion (Fallback 1) | PSF/PTA summary prices | Daily | Scraper |
| IEA Petrochemical (Fallback 2) | PTA/MEG upstream proxy | Weekly | Scraper |
| `/feedstock` command (Fallback 3) | Manual user entry | On-demand | Telegram bot |

### 4.2 Macro & Operations

| Source | Data Point | Frequency | Access Method |
|---|---|---|---|
| Alpha Vantage / ExchangeRate API | USD/INR, USD/CNY | Daily | API |
| WTI / Brent | Crude oil spot | Daily | API (FRED or Yahoo Finance) |
| IEX India | Electricity spot (INR/kWh) | Daily | API |
| Ministry of Labour India | Minimum wage policy | Monthly | Scraper (gov site) |

### 4.3 Logistics — Egypt Corridor

| Route | Index | Surcharge Flags |
|---|---|---|
| Mundra/Nhava Sheva → Egypt | CCFI Mediterranean Route | War Risk, Suez Diversion, PSS |
| Shanghai/Ningbo → Egypt | Drewry WCI (Composite) | GRI, BAF, CAF |

**Surcharge Logic:**
- System scrapes CCFI and Drewry weekly
- NLP keyword scan on shipping news detects "Suez closure", "war risk", "diversion"
- When detected → `surcharge_flag = HIGH` → freight confidence interval widens

### 4.4 Data Source Health Dashboard

Each source is assigned a health state refreshed every 30 minutes:

| State | Meaning | Action |
|---|---|---|
| 🟢 LIVE | Updated within expected window | Normal operation |
| 🟡 STALE | Last update > 24h ago | Activate fallback, flag in Telegram |
| 🔴 DEAD | Last update > 48h ago | Confidence Decay trigger, notify user |

---

## 5. Database Schema

### 5.1 PostgreSQL Tables

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ─────────────────────────────────────────────
-- PRICE HISTORY
-- ─────────────────────────────────────────────
CREATE TABLE price_history (
    id              BIGSERIAL PRIMARY KEY,
    commodity       VARCHAR(50)     NOT NULL,   -- 'cotton_india', 'psf_china', 'yarn_30s', etc.
    source          VARCHAR(50)     NOT NULL,   -- 'CAI', 'CCFGroup', 'ICE', etc.
    price_usd       NUMERIC(12, 4)  NOT NULL,
    price_local     NUMERIC(12, 4),             -- Original local currency
    local_currency  CHAR(3),                    -- 'INR', 'CNY', 'USc', etc.
    fx_rate         NUMERIC(10, 6),             -- USD/local at time of fetch
    recorded_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    data_date       DATE            NOT NULL,   -- The market date this price refers to
    UNIQUE (commodity, source, data_date)
);

CREATE INDEX idx_price_commodity_date ON price_history (commodity, data_date DESC);

-- ─────────────────────────────────────────────
-- FREIGHT RATES
-- ─────────────────────────────────────────────
CREATE TABLE freight_rates (
    id              BIGSERIAL PRIMARY KEY,
    route           VARCHAR(100)    NOT NULL,   -- 'mundra_egypt', 'shanghai_egypt'
    index_source    VARCHAR(50)     NOT NULL,   -- 'CCFI', 'WCI'
    base_rate_usd   NUMERIC(10, 2)  NOT NULL,
    surcharge_usd   NUMERIC(10, 2)  DEFAULT 0,
    surcharge_flags TEXT[],                     -- ['war_risk', 'suez_diversion']
    data_date       DATE            NOT NULL,
    recorded_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (route, index_source, data_date)
);

-- ─────────────────────────────────────────────
-- FORECASTS
-- ─────────────────────────────────────────────
CREATE TABLE forecasts (
    id              BIGSERIAL PRIMARY KEY,
    commodity       VARCHAR(50)     NOT NULL,
    model_name      VARCHAR(50)     NOT NULL,   -- 'TFT', 'XGBoost', 'ARIMAX'
    horizon_days    SMALLINT        NOT NULL,   -- 30, 60, 90
    forecast_date   DATE            NOT NULL,   -- Date forecast was generated
    target_date     DATE            NOT NULL,   -- Date forecast is for
    point_forecast  NUMERIC(12, 4)  NOT NULL,
    ci_lower        NUMERIC(12, 4),             -- 80% confidence lower bound
    ci_upper        NUMERIC(12, 4),             -- 80% confidence upper bound
    mae_backtest    NUMERIC(8, 4),              -- MAE from last backtest
    confidence_decay BOOLEAN        DEFAULT FALSE,
    decay_reason    TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_forecast_commodity_date ON forecasts (commodity, target_date DESC);

-- ─────────────────────────────────────────────
-- SENTIMENT EVENTS
-- ─────────────────────────────────────────────
CREATE TABLE sentiment_events (
    id              BIGSERIAL PRIMARY KEY,
    source          VARCHAR(100)    NOT NULL,   -- 'USDA', 'CCFGroup', 'TextileWorld'
    headline        TEXT            NOT NULL,
    sentiment_score NUMERIC(4, 3),             -- -1.0 to +1.0
    intensity       VARCHAR(10),               -- 'HIGH', 'MEDIUM', 'LOW'
    keywords        TEXT[],                    -- Matched keywords
    embedding       vector(768),               -- FinBERT sentence embedding
    commodity_tags  TEXT[],                    -- ['cotton', 'psf', 'freight']
    published_at    TIMESTAMPTZ,
    recorded_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sentiment_commodity ON sentiment_events USING GIN (commodity_tags);
CREATE INDEX idx_sentiment_embedding ON sentiment_events USING hnsw (embedding vector_cosine_ops);

-- ─────────────────────────────────────────────
-- USER PURCHASES (/buy command)
-- ─────────────────────────────────────────────
CREATE TABLE user_purchases (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT          NOT NULL,   -- Telegram user ID
    commodity       VARCHAR(50)     NOT NULL,
    price_usd       NUMERIC(12, 4)  NOT NULL,
    volume_kg       NUMERIC(12, 2),
    purchase_date   DATE            NOT NULL DEFAULT CURRENT_DATE,
    market_avg_usd  NUMERIC(12, 4),            -- Market mean at time of purchase
    alpha_usd       NUMERIC(12, 4)  GENERATED ALWAYS AS
                    ((market_avg_usd - price_usd) * volume_kg) STORED,
    notes           TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- ALERT LOG
-- ─────────────────────────────────────────────
CREATE TABLE alert_log (
    id              BIGSERIAL PRIMARY KEY,
    commodity       VARCHAR(50)     NOT NULL,
    alert_type      VARCHAR(30)     NOT NULL,   -- 'VOLATILITY', 'STALE_FEED', 'DECAY'
    trigger_value   NUMERIC(8, 4),             -- % move that triggered alert
    sources_confirmed SMALLINT,                -- Number of sources that confirmed
    suppressed      BOOLEAN         DEFAULT FALSE,
    suppression_reason TEXT,
    sent_at         TIMESTAMPTZ,
    acted_on        BOOLEAN,                   -- Updated by /buy within 6h = TRUE
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- DATA SOURCE HEALTH
-- ─────────────────────────────────────────────
CREATE TABLE source_health (
    source_name     VARCHAR(50)     PRIMARY KEY,
    last_updated    TIMESTAMPTZ,
    status          VARCHAR(10)     NOT NULL DEFAULT 'UNKNOWN', -- LIVE, STALE, DEAD
    fallback_active BOOLEAN         DEFAULT FALSE,
    fallback_source VARCHAR(50),
    checked_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
```

### 5.2 Repository Pattern (Python)

```python
# db/repository.py
from datetime import date
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
from config import settings

class PriceRepository:
    def __init__(self):
        self.conn = psycopg2.connect(settings.POSTGRES_URL)

    def upsert_price(
        self,
        commodity: str,
        source: str,
        price_usd: Decimal,
        data_date: date,
        price_local: Decimal = None,
        local_currency: str = None,
        fx_rate: Decimal = None,
    ):
        sql = """
            INSERT INTO price_history
                (commodity, source, price_usd, price_local, local_currency, fx_rate, data_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (commodity, source, data_date)
            DO UPDATE SET
                price_usd = EXCLUDED.price_usd,
                fx_rate   = EXCLUDED.fx_rate,
                recorded_at = NOW()
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (
                commodity, source, price_usd, price_local,
                local_currency, fx_rate, data_date
            ))
        self.conn.commit()

    def get_price_history(self, commodity: str, days: int = 90):
        sql = """
            SELECT data_date, price_usd, source
            FROM price_history
            WHERE commodity = %s
              AND data_date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY data_date DESC
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (commodity, days))
            return cur.fetchall()
```

---

## 6. AI & Predictive Logic

### 6.1 Baseline Model — Deploy First (Week 3)

Before TFT, deploy an XGBoost model as the production baseline.

```python
# models/baseline_model.py
import polars as pl
import xgboost as xgb
from sklearn.metrics import mean_absolute_error
import numpy as np

FEATURES = [
    "cotton_india_usd",     # CAI spot
    "psf_china_usd",        # CCFGroup PSF
    "pta_usd",              # PTA upstream
    "meg_usd",              # MEG upstream
    "wti_crude_usd",        # Oil
    "usd_inr",              # FX
    "usd_cny",              # FX
    "iex_electricity_usd",  # Energy cost
    "ccfi_med_usd",         # Freight
    "sentiment_score",      # Composite sentiment
    # Lagged features (90-day correlation logic)
    "psf_china_usd_lag30",
    "psf_china_usd_lag60",
    "psf_china_usd_lag90",
]

class BaselineForecaster:
    def __init__(self, horizon_days: int = 90):
        self.horizon = horizon_days
        self.model = xgb.XGBRegressor(
            n_estimators=500,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
        )

    def prepare_features(self, df: pl.DataFrame) -> pl.DataFrame:
        """Add lagged features for upstream correlation."""
        return df.with_columns([
            pl.col("psf_china_usd").shift(30).alias("psf_china_usd_lag30"),
            pl.col("psf_china_usd").shift(60).alias("psf_china_usd_lag60"),
            pl.col("psf_china_usd").shift(90).alias("psf_china_usd_lag90"),
        ]).drop_nulls()

    def train(self, df: pl.DataFrame, target: str = "yarn_30s_usd"):
        df = self.prepare_features(df)
        X = df.select(FEATURES).to_numpy()
        y = df[target].to_numpy()
        split = int(len(X) * 0.8)
        self.model.fit(X[:split], y[:split])
        preds = self.model.predict(X[split:])
        mae = mean_absolute_error(y[split:], preds)
        print(f"[Baseline] Validation MAE: {mae:.4f} USD/kg")
        return mae

    def predict(self, latest_features: dict) -> dict:
        X = np.array([[latest_features[f] for f in FEATURES]])
        point = float(self.model.predict(X)[0])
        # Simple prediction interval via residual std (placeholder)
        ci_width = point * 0.08
        return {
            "point_forecast": round(point, 4),
            "ci_lower": round(point - ci_width, 4),
            "ci_upper": round(point + ci_width, 4),
            "model": "XGBoost-Baseline",
        }
```

### 6.2 TFT Model — Promote After Baseline (Week 5–6)

```python
# models/tft_model.py
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting.metrics import QuantileLoss
import pytorch_lightning as pl

class TFTForecaster:
    """
    Temporal Fusion Transformer for multi-horizon yarn price forecasting.
    Only promoted to production if MAE < BaselineMAE * 0.85 (15% improvement gate).
    """

    STATIC_CATEGORICALS = ["commodity", "origin_country"]
    TIME_VARYING_KNOWN = ["usd_inr", "usd_cny", "wti_crude_usd"]
    TIME_VARYING_UNKNOWN = [
        "cotton_india_usd", "psf_china_usd", "pta_usd",
        "ccfi_med_usd", "iex_electricity_usd", "sentiment_score"
    ]

    def build_dataset(self, df, max_encoder_length=120, max_prediction_length=90):
        return TimeSeriesDataSet(
            df,
            time_idx="time_idx",
            target="yarn_30s_usd",
            group_ids=["commodity"],
            max_encoder_length=max_encoder_length,
            max_prediction_length=max_prediction_length,
            static_categoricals=self.STATIC_CATEGORICALS,
            time_varying_known_reals=self.TIME_VARYING_KNOWN,
            time_varying_unknown_reals=self.TIME_VARYING_UNKNOWN,
            target_normalizer="auto",
        )

    def build_model(self, dataset):
        return TemporalFusionTransformer.from_dataset(
            dataset,
            learning_rate=1e-3,
            hidden_size=64,
            attention_head_size=4,
            dropout=0.1,
            hidden_continuous_size=32,
            output_size=7,          # 7 quantiles → fan chart
            loss=QuantileLoss(),
            log_interval=10,
            reduce_on_plateau_patience=4,
        )
```

### 6.3 Model Promotion Gate

```python
# models/model_registry.py

PROMOTION_THRESHOLD = 0.85  # TFT must beat baseline MAE by 15%

def evaluate_promotion(baseline_mae: float, tft_mae: float) -> bool:
    if tft_mae < baseline_mae * PROMOTION_THRESHOLD:
        print(f"✅ TFT promoted: {tft_mae:.4f} vs baseline {baseline_mae:.4f}")
        return True
    print(f"❌ TFT NOT promoted: {tft_mae:.4f} does not beat {baseline_mae * PROMOTION_THRESHOLD:.4f}")
    return False

def get_active_model(registry: dict) -> str:
    """Returns 'TFT' if promoted, else 'XGBoost-Baseline'."""
    return registry.get("active_model", "XGBoost-Baseline")
```

---

## 7. Sentiment Analysis Engine

### 7.1 Tier 1 — Keyword Scorer (Day 1)

```python
# nlp/keyword_scorer.py
from dataclasses import dataclass
from typing import List

@dataclass
class KeywordRule:
    keyword: str
    intensity: str      # HIGH, MEDIUM, LOW
    direction: float    # +1.0 = bullish price, -1.0 = bearish price
    commodities: List[str]

KEYWORD_RULES = [
    # HIGH intensity — immediate market impact
    KeywordRule("suez closure",      "HIGH",   +1.0, ["freight", "all"]),
    KeywordRule("suez diversion",    "HIGH",   +1.0, ["freight", "all"]),
    KeywordRule("war risk",          "HIGH",   +1.0, ["freight"]),
    KeywordRule("refinery shutdown", "HIGH",   +1.0, ["psf", "pta", "meg"]),
    KeywordRule("mill strike",       "HIGH",   +1.0, ["yarn", "cotton"]),
    KeywordRule("drought",           "HIGH",   +1.0, ["cotton"]),
    KeywordRule("monsoon failure",   "HIGH",   +1.0, ["cotton"]),

    # MEDIUM intensity — trend influencers
    KeywordRule("inventory buildup", "MEDIUM", -1.0, ["psf", "cotton"]),
    KeywordRule("energy tariff",     "MEDIUM", +1.0, ["yarn", "psf"]),
    KeywordRule("monsoon forecast",  "MEDIUM", -0.5, ["cotton"]),
    KeywordRule("operating rate",    "MEDIUM", +0.5, ["psf"]),
    KeywordRule("anti-dumping",      "MEDIUM", +1.0, ["yarn", "psf"]),

    # LOW intensity — background noise
    KeywordRule("steady demand",     "LOW",    +0.2, ["all"]),
    KeywordRule("normal operations", "LOW",    -0.2, ["all"]),
]

INTENSITY_WEIGHTS = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.2}

def score_headline(headline: str) -> dict:
    headline_lower = headline.lower()
    matched = []
    total_score = 0.0

    for rule in KEYWORD_RULES:
        if rule.keyword in headline_lower:
            weight = INTENSITY_WEIGHTS[rule.intensity]
            total_score += rule.direction * weight
            matched.append({
                "keyword": rule.keyword,
                "intensity": rule.intensity,
                "commodities": rule.commodities,
            })

    # Clamp to [-1, +1]
    total_score = max(-1.0, min(1.0, total_score))
    return {
        "score": round(total_score, 3),
        "matches": matched,
        "intensity": "HIGH" if any(m["intensity"] == "HIGH" for m in matched) else
                     "MEDIUM" if matched else "LOW",
    }
```

### 7.2 Tier 2 — FinBERT Zero-Shot (Month 2+)

```python
# nlp/finbert_scorer.py
from transformers import pipeline

# Use zero-shot before committing to fine-tuning
# Fine-tune only if accuracy on 100 labeled headlines < 70%

finbert = pipeline(
    "text-classification",
    model="ProsusAI/finbert",
    tokenizer="ProsusAI/finbert",
    top_k=None,
)

LABEL_MAP = {"positive": +1.0, "negative": -1.0, "neutral": 0.0}

def score_with_finbert(headline: str) -> dict:
    results = finbert(headline[:512])[0]
    scores = {r["label"]: r["score"] for r in results}
    # Weighted composite
    composite = sum(LABEL_MAP[label] * score for label, score in scores.items())
    return {
        "score": round(composite, 3),
        "raw": scores,
        "model": "FinBERT-zero-shot",
    }
```

---

## 8. Functional Features & Interface

### 8.1 Telegram Bot — Scheduler (Egypt Time)

```python
# bot/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

CAIRO_TZ = pytz.timezone("Africa/Cairo")

def setup_scheduler(bot, reporter_agent):
    scheduler = AsyncIOScheduler(timezone=CAIRO_TZ)

    # 09:30 CAI — Global Overnight Recap (Oil + ICE Cotton)
    scheduler.add_job(
        reporter_agent.send_overnight_recap,
        CronTrigger(hour=9, minute=30, timezone=CAIRO_TZ),
    )
    # 13:30 CAI — Indian Market Opening + Freight Indications
    scheduler.add_job(
        reporter_agent.send_india_recap,
        CronTrigger(hour=13, minute=30, timezone=CAIRO_TZ),
    )
    # 17:30 CAI — Chinese Market Recap (CCFG Inventory + PTA/MEG)
    scheduler.add_job(
        reporter_agent.send_china_recap,
        CronTrigger(hour=17, minute=30, timezone=CAIRO_TZ),
    )
    # 21:00 CAI — 90-Day Outlook + Sentiment + Performance Review
    scheduler.add_job(
        reporter_agent.send_evening_outlook,
        CronTrigger(hour=21, minute=0, timezone=CAIRO_TZ),
    )

    scheduler.start()
    return scheduler
```

### 8.2 Bot Commands

```python
# bot/commands.py
from telegram import Update
from telegram.ext import ContextTypes
from db.repository import PriceRepository, PurchaseRepository
from agents.forecast import ForecastAgent
from agents.alert import AlertAgent

repo = PriceRepository()
forecast_agent = ForecastAgent()

async def cmd_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Usage: /buy yarn_30s 1.85
    Logs a purchase and compares against the market mean.
    """
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /buy [commodity] [price_USD]")
        return

    commodity = args[0]
    try:
        price_usd = float(args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid price. Use a number e.g. /buy yarn_30s 1.85")
        return

    market_avg = repo.get_market_avg(commodity, days=30)
    alpha = (market_avg - price_usd)

    emoji = "✅" if alpha > 0 else "⚠️"
    msg = (
        f"{emoji} *Purchase Logged*\n"
        f"Commodity: `{commodity}`\n"
        f"Your Price: `${price_usd:.4f}/kg`\n"
        f"30-Day Market Avg: `${market_avg:.4f}/kg`\n"
        f"Alpha: `{'+'if alpha>0 else ''}{alpha:.4f} USD/kg`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    repo.log_purchase(update.effective_user.id, commodity, price_usd, market_avg)


async def cmd_outlook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/outlook — Returns 90-day fan chart and point forecast."""
    forecast = forecast_agent.run(commodity="yarn_30s", horizon=90)
    decay_warning = ""
    if forecast.get("confidence_decay"):
        decay_warning = f"\n⚠️ _{forecast['decay_reason']}_"

    msg = (
        f"📈 *90-Day Outlook — Yarn 30s*\n"
        f"Point Forecast: `${forecast['point_forecast']:.4f}/kg`\n"
        f"80% CI: `${forecast['ci_lower']:.4f} — ${forecast['ci_upper']:.4f}`\n"
        f"Model: `{forecast['model']}`\n"
        f"Backtest MAE: `{forecast['mae_backtest']:.2%}`"
        f"{decay_warning}"
    )
    await update.message.reply_photo(
        photo=forecast["chart_bytes"],
        caption=msg,
        parse_mode="Markdown",
    )


async def cmd_freight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/freight — Returns current freight indications for Egypt-bound routes."""
    routes = repo.get_latest_freight()
    lines = ["🚢 *Freight Indications — Egypt Bound*\n"]
    for r in routes:
        flags = ", ".join(r["surcharge_flags"]) if r["surcharge_flags"] else "None"
        lines.append(
            f"*{r['route']}* ({r['index_source']})\n"
            f"  Base: `${r['base_rate_usd']:,.0f}`  Surcharge: `${r['surcharge_usd']:,.0f}`\n"
            f"  Flags: `{flags}`\n"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/history — Accepts a pasted CSV block for historical price onboarding."""
    await update.message.reply_text(
        "📂 *Historical Data Upload*\n"
        "Paste your CSV in this format:\n"
        "`date,commodity,price_usd`\n"
        "e.g. `2024-01-15,yarn_30s,1.82`\n\n"
        "Send the data as a text message and I'll ingest it.",
        parse_mode="Markdown",
    )
```

### 8.3 USD Converter Module

```python
# utils/usd_converter.py
import httpx
from decimal import Decimal
from config import settings

class USDConverter:
    """
    Normalizes all commodity prices to USD.
    Supports INR, CNY, USc (US cents), EUR.
    """
    _rates: dict = {}

    async def refresh_rates(self):
        """Fetch latest FX rates. Runs daily at 08:00 Cairo."""
        url = f"https://v6.exchangerate-api.com/v6/{settings.FX_API_KEY}/latest/USD"
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            data = r.json()
            self._rates = data["conversion_rates"]

    def to_usd(self, amount: float, currency: str) -> Decimal:
        if currency == "USD":
            return Decimal(str(amount))
        if currency == "USc":       # US cents (ICE Cotton quotes)
            return Decimal(str(amount)) / 100
        rate = self._rates.get(currency)
        if not rate:
            raise ValueError(f"Unknown currency: {currency}")
        return Decimal(str(amount)) / Decimal(str(rate))

    def inr_per_candy_to_usd_per_kg(self, inr_per_candy: float) -> Decimal:
        """CAI quotes in INR/Candy. 1 Candy = 356 kg."""
        usd_per_candy = self.to_usd(inr_per_candy, "INR")
        return usd_per_candy / Decimal("356")
```

---

## 9. Visual Intelligence

### 9.1 90-Day Fan Chart

```python
# charts/fan_chart.py
import plotly.graph_objects as go
import pandas as pd
from io import BytesIO

def build_fan_chart(
    historical: pd.DataFrame,   # columns: date, price_usd
    forecast: dict,             # point_forecast, ci_lower, ci_upper, dates
    commodity_label: str = "Yarn 30s",
) -> bytes:
    fig = go.Figure()

    # Historical actuals
    fig.add_trace(go.Scatter(
        x=historical["date"],
        y=historical["price_usd"],
        mode="lines",
        name="Historical",
        line=dict(color="#1f77b4", width=2),
    ))

    # Confidence band (shaded)
    fig.add_trace(go.Scatter(
        x=forecast["dates"] + forecast["dates"][::-1],
        y=forecast["ci_upper"] + forecast["ci_lower"][::-1],
        fill="toself",
        fillcolor="rgba(255,127,14,0.2)",
        line=dict(color="rgba(255,255,255,0)"),
        name="80% Confidence Interval",
    ))

    # Point forecast
    fig.add_trace(go.Scatter(
        x=forecast["dates"],
        y=forecast["point_forecast"],
        mode="lines+markers",
        name="AI Forecast",
        line=dict(color="#ff7f0e", width=2, dash="dash"),
    ))

    fig.update_layout(
        title=f"FiberPulse AI — {commodity_label} 90-Day Outlook",
        xaxis_title="Date",
        yaxis_title="Price (USD/kg)",
        template="plotly_white",
        legend=dict(x=0, y=1),
    )

    buf = BytesIO()
    fig.write_image(buf, format="png", width=1000, height=500)
    return buf.getvalue()
```

### 9.2 Chart Inventory

| Chart | Description | Trigger |
|---|---|---|
| 90-Day Fan Chart | Historical actuals + AI point forecast + CI bands | `/outlook`, 21:00 report |
| Correlation Heatmap | Cotton vs PSF vs Oil vs Freight — color-coded | Weekly digest |
| Freight Volatility Bar | Baseline freight vs surcharges per route | `/freight`, 13:30 report |
| Procurement Alpha Scatter | `/buy` data points vs market price line | Weekly digest |

---

## 10. Alert System

### 10.1 3% Volatility Shield with Noise Suppression

```python
# utils/alert_suppressor.py
from datetime import datetime, timedelta
from collections import defaultdict

class AlertSuppressor:
    """
    Applies 3 suppression filters before firing any volatility alert.
    """
    _last_alert: dict = defaultdict(lambda: datetime.min)
    COOLDOWN_HOURS = 6
    ESCALATION_THRESHOLD = 0.05     # 5% bypasses cooldown

    def should_fire(
        self,
        commodity: str,
        pct_move: float,
        sources_confirmed: int,
        rolling_avg_pct: float,
    ) -> tuple[bool, str]:

        # Filter 1: Require 2+ sources to confirm the move
        if sources_confirmed < 2:
            return False, "Insufficient source confirmation (need 2+)"

        # Filter 2: Compare against 5-day rolling average, not just prior close
        if abs(rolling_avg_pct) < 0.03:
            return False, "Move does not exceed 3% vs 5-day rolling avg"

        # Filter 3: Cooldown (unless escalation threshold exceeded)
        last = self._last_alert[commodity]
        cooldown_expired = datetime.now() - last > timedelta(hours=self.COOLDOWN_HOURS)
        if not cooldown_expired and abs(pct_move) < self.ESCALATION_THRESHOLD:
            return False, f"Cooldown active — next alert after {last + timedelta(hours=self.COOLDOWN_HOURS)}"

        self._last_alert[commodity] = datetime.now()
        return True, "All filters passed"

    def log_alert_outcome(self, alert_id: int, acted_on: bool, repo):
        """Called when /buy is used within 6h of an alert — marks it as acted on."""
        repo.update_alert_acted_on(alert_id, acted_on)
```

### 10.2 Alert Fatigue Monitoring

```python
# Weekly check — if ignored rate > 40%, tighten threshold
def evaluate_alert_fatigue(repo, lookback_days: int = 7) -> dict:
    alerts = repo.get_recent_alerts(lookback_days)
    total = len(alerts)
    acted = sum(1 for a in alerts if a["acted_on"])
    ignored_rate = 1 - (acted / total) if total > 0 else 0

    recommendation = None
    if ignored_rate > 0.40:
        recommendation = "⚠️ Alert fatigue detected. Consider raising threshold to 4%."

    return {
        "total_alerts": total,
        "acted_on": acted,
        "ignored_rate": f"{ignored_rate:.0%}",
        "recommendation": recommendation,
    }
```

### 10.3 Confidence Decay Flag

```python
# utils/confidence_decay.py
from datetime import datetime, timedelta
from db.repository import SourceHealthRepository

DECAY_THRESHOLD_HOURS = 48

def check_confidence_decay(commodity: str, health_repo: SourceHealthRepository) -> dict:
    """
    Widens CI and flags forecast if any key feed is stale > 48h.
    """
    affected_sources = health_repo.get_stale_sources(commodity, DECAY_THRESHOLD_HOURS)

    if not affected_sources:
        return {"decay": False}

    stale_names = [s["source_name"] for s in affected_sources]
    return {
        "decay": True,
        "reason": f"Feed stale >48h: {', '.join(stale_names)} — forecast uses proxy data",
        "ci_multiplier": 1.5,   # Widen confidence interval by 50%
    }
```

---

## 11. Code Scaffolding

### 11.1 Main Entry Point

```python
# main.py
import asyncio
from agents.data_fetcher import DataFetcherAgent
from agents.reporter import ReporterAgent
from bot.telegram_bot import build_app
from bot.scheduler import setup_scheduler
from utils.usd_converter import USDConverter

async def main():
    converter = USDConverter()
    await converter.refresh_rates()

    fetcher = DataFetcherAgent(converter=converter)
    reporter = ReporterAgent()

    app = build_app()
    setup_scheduler(app.bot, reporter)

    print("🚀 FiberPulse AI is running...")
    async with app:
        await app.start()
        await asyncio.Event().wait()   # Run forever

if __name__ == "__main__":
    asyncio.run(main())
```

### 11.2 LangGraph Orchestration Skeleton

```python
# agents/graph.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FiberPulseState(TypedDict):
    raw_prices: dict
    normalized_prices: dict
    forecast: dict
    sentiment_score: float
    alerts: List[dict]
    report: str

def build_graph():
    graph = StateGraph(FiberPulseState)

    graph.add_node("fetch",     DataFetcherAgent().run)
    graph.add_node("normalize", NormalizerAgent().run)
    graph.add_node("forecast",  ForecastAgent().run)
    graph.add_node("sentiment", SentimentAgent().run)
    graph.add_node("alert",     AlertAgent().run)
    graph.add_node("report",    ReporterAgent().run)

    graph.set_entry_point("fetch")
    graph.add_edge("fetch",     "normalize")
    graph.add_edge("normalize", "forecast")
    graph.add_edge("normalize", "sentiment")
    graph.add_edge("forecast",  "alert")
    graph.add_edge("sentiment", "alert")
    graph.add_edge("alert",     "report")
    graph.add_edge("report",    END)

    return graph.compile()
```

---

## 12. Implementation Roadmap

### Phase 1 — Data Scaffolding (Week 1)

| Day | Task | Owner | Output |
|---|---|---|---|
| 1 | Setup PostgreSQL + pgvector, run schema.sql | Dev | DB ready |
| 1 | Configure .env, pyproject.toml, install deps | Dev | Environment ready |
| 2 | Build `USDConverter` module + unit tests | Dev | All currencies → USD |
| 2 | Build `DataSourceHealthDashboard` | Dev | Status tracking live |
| 3 | Build CAI scraper (Cotton spot, INR/Candy) | Dev | Daily cotton prices |
| 3 | Build MCX scraper (Futures near/far month) | Dev | Futures data |
| 4 | Build CCFGroup integration (API + fallback chain) | Dev | PSF/PTA/MEG data |
| 4 | Build Fibre2Fashion + IEA fallback scrapers | Dev | Fallback confirmed |
| 5 | Build `PriceRepository` + upsert logic | Dev | Prices persisting to DB |
| 5 | End-of-week: validate all data flows, fix gaps | Dev | Clean data in DB |

### Phase 2 — Logistics & Operations (Week 2)

| Day | Task | Owner | Output |
|---|---|---|---|
| 1 | Build CCFI scraper (Mediterranean route) | Dev | Freight baseline |
| 1 | Build Drewry WCI integration | Dev | Second freight source |
| 2 | Implement surcharge NLP keyword scanner | Dev | War risk / Suez flags |
| 2 | Build `FreightRepository` + upsert logic | Dev | Freight in DB |
| 3 | Build IEX electricity price feed | Dev | Energy cost data |
| 3 | Build Alpha Vantage FX feed (USD/INR, USD/CNY) | Dev | FX rates live |
| 4 | Build WTI/Brent crude feed (FRED API) | Dev | Oil prices live |
| 4 | Connect all sources to `DataFetcherAgent` | Dev | Unified fetch pipeline |
| 5 | Validate freight + macro data integrity | Dev | Full data pipeline QA |

### Phase 3 — Baseline AI + Sentiment (Week 3)

| Day | Task | Owner | Output |
|---|---|---|---|
| 1 | Build `KeywordScorer` (Tier-1 NLP) | Dev | Day-1 sentiment scores |
| 1 | Build `SentimentAgent` integration | Dev | Scores saving to DB |
| 2 | Prepare 5-year historical dataset (CSV import via `/history`) | Ahmed | Training data ready |
| 2 | Feature engineering: lagged correlations (30/60/90 days) | Dev | Feature matrix |
| 3 | Train XGBoost baseline model | Dev | Baseline forecasts live |
| 3 | Validate baseline MAE (target < 5%) | Dev | MAE benchmark set |
| 4 | Connect baseline forecast to `ForecastAgent` | Dev | Forecasts in DB |
| 4 | Implement `ConfidenceDecayFlag` module | Dev | Decay detection active |
| 5 | End-of-week: first full pipeline run (data → forecast → DB) | Dev | Full pipeline live |

### Phase 4 — Interface & Alerts (Week 4)

| Day | Task | Owner | Output |
|---|---|---|---|
| 1 | Build Telegram bot skeleton + all commands | Dev | Bot responding |
| 1 | Implement `/buy`, `/outlook`, `/freight`, `/history` | Dev | Commands functional |
| 2 | Build `AlertSuppressor` (3-filter logic) | Dev | Smart alerts |
| 2 | Implement 3% Volatility Shield | Dev | Alerts firing |
| 3 | Build Fan Chart (`fan_chart.py`) | Dev | Chart sent via bot |
| 3 | Build Freight Volatility Bar chart | Dev | Freight chart ready |
| 4 | Setup 4x daily scheduler (Cairo timezone) | Dev | Scheduled messages |
| 4 | Build morning/afternoon/evening report templates | Dev | Formatted messages |
| 5 | End-to-end QA: full day simulation | Ahmed + Dev | System validated |

### Phase 5 — TFT Upgrade & Fine-tuning (Week 5–6)

| Day | Task | Output |
|---|---|---|
| Week 5, Day 1–2 | Verify 2 weeks of clean pipeline data | Data quality confirmed |
| Week 5, Day 3–4 | Build TFT dataset + train model | TFT trained |
| Week 5, Day 5 | Run MAE comparison vs baseline | Promotion decision |
| Week 6, Day 1–2 | If promoted: swap active model in registry | TFT in production |
| Week 6, Day 3–4 | Label 100 headlines, evaluate FinBERT zero-shot | Accuracy assessed |
| Week 6, Day 5 | If FinBERT < 70% accuracy: begin fine-tuning pipeline | Fine-tuning or skip |

---

## 13. Financial Performance Tracking

### 13.1 Alpha Formula

$$\text{Alpha}_{USD} = (\text{Market Avg}_{USD} - \text{User Price}_{USD}) \times \text{Volume}_{kg}$$

### 13.2 Performance Dashboard (Weekly)

```python
def generate_weekly_performance(repo, user_id: int) -> str:
    purchases = repo.get_user_purchases(user_id, days=30)
    total_alpha = sum(p["alpha_usd"] for p in purchases)
    total_volume = sum(p["volume_kg"] for p in purchases)
    avg_beat = total_alpha / total_volume if total_volume else 0

    alert_stats = evaluate_alert_fatigue(repo)

    return (
        f"📊 *Weekly Performance Review*\n\n"
        f"*Procurement Alpha:* `${total_alpha:+,.2f} USD`\n"
        f"*Total Volume:* `{total_volume:,.0f} kg`\n"
        f"*Avg Beat vs Market:* `${avg_beat:+.4f}/kg`\n\n"
        f"*Alert Performance:*\n"
        f"  Total alerts: `{alert_stats['total_alerts']}`\n"
        f"  Acted on: `{alert_stats['acted_on']}`\n"
        f"  Ignored rate: `{alert_stats['ignored_rate']}`\n"
        f"{alert_stats.get('recommendation', '')}"
    )
```

---

## 14. Risk Register

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | CCFGroup data access blocked/paywalled | 🔴 High | 3-tier fallback chain + `/feedstock` manual command |
| 2 | TFT training fails due to data quality | 🟡 Medium | Baseline-first; TFT promoted only after gate |
| 3 | Alert fatigue renders shield useless | 🟡 Medium | 3-filter suppressor + weekly fatigue score |
| 4 | Stale feed produces false-precision forecast | 🔴 High | ConfidenceDecayFlag widens CI + Telegram warning |
| 5 | FinBERT fine-tuning mislabels textile context | 🟡 Medium | Zero-shot evaluation before committing |
| 6 | Suez surcharge spike not captured | 🟡 Medium | Dual-source confirmation (CCFI + Drewry) |
| 7 | FX rate lag distorts USD normalization | 🟢 Low | Daily FX refresh at 08:00 Cairo before all fetches |
| 8 | Telegram bot downtime during market hours | 🟡 Medium | APScheduler retry logic + dead-letter queue |

---

*FiberPulse AI PRD v8.0 — Prepared for Ahmed El Monier, March 2026*
*This document supersedes all prior versions (v1.0–v7.0)*

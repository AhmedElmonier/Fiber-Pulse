# 🚀 FiberPulse AI: Detailed Operational Guide

This guide provides a comprehensive, engineering-centric walkthrough for running the **FiberPulse AI** system. The application is a multi-stage data pipeline that integrates market data scraping, XGBoost machine learning, and a Telegram-based alerting interface.

---

## 🏗️ Part 1: Infrastructure & Environment Setup

Before running any code, you must prepare the environment where the data will live.

### 1. System Requirements
*   **Python 3.12+**: Required for `zoneinfo` and modern async features.
*   **PostgreSQL 16+**: Must have the `pgvector` extension installed (used for future sentiment embedding and similarity searches).
*   **Telegram Bot Token**: Created via [@BotFather](https://t.me/botfather).

### 2. Secrets: The `.env` File
Create a `.env` file in the root directory. Use `.env.example` as a template:
```bash
# Database
DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/fiberpulse"

# Telegram
TELEGRAM_BOT_TOKEN="123456789:ABC-DEF..."
TELEGRAM_WHITELIST="your_user_id,another_user_id" # Critical for security

# AI/NLP
XGBOOST_RANDOM_STATE=42
```

---

## 📦 Part 2: Installation

**IMPORTANT**: Ensure you are in the project root directory before running these commands.
```bash
cd "/mnt/4EDC012BDC010EC1/Projects/Cotton - PSF"
```

FiberPulse uses **Poetry** to manage complex dependencies like `xgboost` and `python-telegram-bot`.

```bash
# 1. Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# 2. Update the lock file if you changed pyproject.toml
poetry lock

# 3. Install dependencies (this automatically creates a virtual environment)
poetry install

# 4. Enter the virtual environment
poetry shell
```

---

## 📊 Part 3: The Data Lifecycle

The application cannot forecast without "fuel." You must populate the database in three ways:

### 1. Database Initialization
Run the migration scripts to build the schema for prices, freight, and logs.
```bash
python -m db.migrations.001_add_phase2_tables
python -m db.migrations.002_add_phase4_tables
```

### 2. Historical Onboarding (One-time)
Ingest existing market data to provide the XGBoost model with training context.
```bash
# Ingest historical CSVs
python -m fiberpulse ingest-history data/historical/cai_2024.csv
```

### 3. Live Ingestion Pulse (Scheduled or Manual)
Trigger the scrapers to fetch current prices (CAI Cotton, MCX Futures, Freight).
```bash
# Run the unified fetcher
python -m agents.unified_ingestion_orchestrator
```

---

## 🧠 Part 4: AI Model Training & Forecasting

Once the database has at least 30 days of history, you can engage the AI engine.

### 1. Training the Baseline
The `BaselineXGBoostModel` uses **Quantile Regression** to generate 5%, 50%, and 95% confidence bounds. Training is cached based on a SHA-256 data fingerprint.
```bash
# Typically handled internally by the forecast agent, but can be triggered via:
python -m agents.forecast --train --target cai_spot
```

### 2. Generating Predictions
The forecast agent extracts a 30-day sliding window of features (momentum, rolling averages) and generates the 30-day predicted outlook.
```bash
python -m agents.forecast --target cai_spot
```

---

## 🤖 Part 5: Running the Interface (The Bot)

The Telegram Bot is the primary delivery vehicle. It handles reactive commands and proactive alerts.

### 1. Launching the Bot Service
This process runs an `AsyncIO` loop that polls for messages and manages the internal scheduler.
```bash
python -m bot.telegram_bot
```

### 2. Interactive Commands (Whitelisted Only)
*   **/buy**: Returns a Strong Buy/Hold/Sell signal with a confidence score.
*   **/outlook**: Generates a **Fan Chart** (Matplotlib graph with shaded confidence regions).
*   **/freight**: Displays current global shipping rates with a comparative Bar Chart.
*   **/history**: Shows a 30-day historical price table.

### 3. Proactive Background Tasks
*   **Scheduled Market Pulse**: Automatically broadcasts a market summary at **09:00, 12:00, 15:00, and 18:00 (Cairo Time)**.
*   **Volatility Alerts**: If a new price entry shows a **>3% change**, the bot sends an immediate alert to all whitelisted users (subject to a 1-hour suppression limit).

---

## 🧪 Part 6: Validation & Health

To ensure the system is meeting the **MAE < 5%** accuracy target:

```bash
# Run the full test suite
python -m pytest

# Check system health logs via SQL
psql $DATABASE_URL -c "SELECT * FROM source_health ORDER BY last_check DESC LIMIT 10;"

# Verify Alerting and Audit logs
psql $DATABASE_URL -c "SELECT timestamp, instrument_name, trigger_reason, status FROM alert_log ORDER BY timestamp DESC LIMIT 5;"
```

---

## 🔑 Final Operational Checklist
1.  **Timezone**: The system is hard-coded to `Africa/Cairo` for market alignment. Ensure your server environment reflects this.
2.  **Whitelisting**: Verify your Telegram User ID is in the `TELEGRAM_WHITELIST` in `.env`.
3.  **Visualization**: The bot requires write access to the root directory to generate temporary PNG files for charts.
4.  **Matplotlib**: Running on a headless server is supported via the `Agg` backend.

---

## 🐘 Appendix: PostgreSQL Database Setup

If you see `OperationalError: FATAL: password authentication failed`, it means your PostgreSQL credentials do not match your `.env` file. 

Follow these steps to create the database and user correctly:

```bash
# 1. Access PostgreSQL as the superuser
sudo -u postgres psql

# 2. Create the FiberPulse database
CREATE DATABASE fiberpulse;

# 3. Create the user (matching the guide's default)
CREATE USER "user" WITH PASSWORD 'password';

# 4. Grant all permissions to the user for this database
GRANT ALL PRIVILEGES ON DATABASE fiberpulse TO "user";

# 5. [Optional] If using PostgreSQL 15+, grant schema permissions
\c fiberpulse
GRANT ALL ON SCHEMA public TO "user";

# 6. Exit
\q
```

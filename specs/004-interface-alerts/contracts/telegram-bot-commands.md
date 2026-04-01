# Telegram Bot Command Contract: Phase 4 — Interface & Alerts

## Command Interface

All commands MUST be issued via a direct message or group mention and are restricted to whitelisted users.

### `/buy`
Returns a trade recommendation based on the latest AI forecasts.
- **Input**: None (or optional instrument name, defaults to Cairo Cotton)
- **Output**:
  - `recommendation`: Strong Buy | Buy | Hold | Sell
  - `confidence_score`: 0.0 - 1.0
  - `price_target_30d`: USD value
  - `visual`: (Optional) Price trend sparkline

### `/outlook`
Provides a 30-day market forecast with visualization.
- **Input**: None
- **Output**:
  - `summary`: Textual description of the trend (Bullish/Bearish/Neutral)
  - `forecast_range`: Min/Max expected prices
  - `visual`: **Fan Chart** (Matplotlib plot with confidence shaded regions)

### `/freight`
Displays current freight rates for tracked routes.
- **Input**: None
- **Output**:
  - `rates`: List of latest CCFI Mediterranean and Drewry WCI prices
  - `visual`: **Bar Chart** comparing routes and previous week's prices

### `/history`
Retrieves the last 30 days of price history.
- **Input**: None
- **Output**:
  - `data`: Table showing Date | Price | % Change
  - `visual`: **Price Trend Chart**

## Message Format
- **Encoding**: UTF-8 (MarkdownV2 format for rich text)
- **Charts**: PNG images sent as `photo` type via Telegram API.

## Alerting Protocol
- **Trigger**: New price entry >3% delta from previous day for the same instrument.
- **Frequency**: Max 1 per hour per instrument.
- **Delivery**: Broadcast individually to all whitelisted User IDs.

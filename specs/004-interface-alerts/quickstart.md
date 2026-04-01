# Quickstart: Phase 4 — Interface & Alerts

## Prerequisites
- Telegram Bot API Token (from @BotFather)
- Valid Telegram User ID(s) for whitelisting
- Python 3.12+ and established database (PostgreSQL)

## Environment Configuration
Update `.env` with the following variables:
```bash
TELEGRAM_BOT_TOKEN="your_token_here"
TELEGRAM_WHITELIST="12345678,90123456" # Comma-separated User IDs
```

## Running the Bot Locally
1. Start the bot process:
   ```bash
   python -m src.bot.telegram_bot
   ```
2. In Telegram, search for your bot's handle and send `/start`.
3. If whitelisted, you should receive a welcome message.

## Testing Commands
- Send `/buy` to test forecast retrieval and recommendation logic.
- Send `/outlook` to verify fan chart generation and delivery.
- Send `/freight` to test bar chart generation.
- Send `/history` to test tabular historical data retrieval.

## Simulating Alerts
To trigger an alert manually for testing purposes:
1. Insert a price entry in `price_history` that is >3% different from the previous entry.
2. Run the alert trigger check (or wait for the next scheduled pulse).
3. Verify all whitelisted users receive the notification.

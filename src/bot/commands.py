"""Command handlers for Telegram bot.

Implements /buy, /outlook, and other market-related commands.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def outlook_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /outlook command - generates market forecast fan chart.

    Args:
        update: Telegram update.
        context: Bot context.
    """
    from config import get_config
    from db.repository import Repository
    from src.bot.telegram_bot import is_user_whitelisted
    from src.charts.fan_chart import generate_fan_chart, generate_simple_forecast_message

    if update.effective_user is None or update.message is None:
        return
    if not is_user_whitelisted(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    try:
        config = get_config()
        repository = Repository(config.database_url)

        forecasts = await repository.get_forecasts(target_source="cai_spot", limit=5)
        await repository.close()

        if not forecasts:
            await update.message.reply_text("No forecast data available. Run /forecast first.")
            return

        dates = [f.target_timestamp_utc.strftime("%Y-%m-%d") for f in forecasts]
        predicted = [float(f.predicted_value) for f in forecasts]
        lower = [float(f.lower_bound) for f in forecasts]
        upper = [float(f.upper_bound) for f in forecasts]

        chart_buffer = generate_fan_chart(dates, predicted, lower, upper)

        latest = forecasts[0]
        message = generate_simple_forecast_message(
            source=latest.target_source,
            predicted_value=latest.predicted_value,
            lower_bound=latest.lower_bound,
            upper_bound=latest.upper_bound,
            horizon_hours=latest.horizon_hours,
        )

        await update.message.reply_photo(photo=chart_buffer, caption=message)

    except Exception as e:
        logger.exception(f"Error generating outlook: {e}")
        await update.message.reply_text("An internal error occurred, please try again later.")


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /buy command - generates buy/sell/hold signal.

    Args:
        update: Telegram update.
        context: Bot context.
    """
    from config import get_config
    from db.repository import Repository
    from src.bot.telegram_bot import is_user_whitelisted
    from src.charts.fan_chart import generate_buy_signal_message

    if update.effective_user is None or update.message is None:
        return
    if not is_user_whitelisted(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    try:
        config = get_config()
        repository = Repository(config.database_url)

        forecasts = await repository.get_forecasts(target_source="cai_spot", limit=2)
        await repository.close()

        if not forecasts:
            await update.message.reply_text("No forecast data available. Run /forecast first.")
            return

        latest = forecasts[0]
        predicted = float(latest.predicted_value)
        lower = float(latest.lower_bound)
        upper = float(latest.upper_bound)

        confidence = latest.confidence_level
        mid = (upper + lower) / 2
        if mid <= 0:
            signal = "HOLD"
            confidence = 0.3
        else:
            pct_upper = (upper - mid) / mid
            pct_lower = (mid - lower) / mid

            if pct_upper < 0.05:
                signal = "BUY"
                confidence = min(confidence * 1.2, 0.95)
            elif pct_lower < 0.05:
                signal = "SELL"
                confidence = min(confidence * 1.2, 0.95)
            else:
                signal = "HOLD"
                confidence = 0.5

        message = generate_buy_signal_message(
            source=latest.target_source,
            signal=signal,
            confidence=confidence,
            predicted_value=predicted,
            lower_bound=lower,
            upper_bound=upper,
        )

        await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        logger.exception(f"Error generating buy signal: {e}")
        await update.message.reply_text(
            "An internal error occurred while generating the buy signal, please try again later."
        )


async def freight_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /freight command - get freight rates with bar chart.

    Fetches the latest freight rate records from the database,
    groups them by route, generates a bar chart comparing current
    rates, and sends the chart with a text summary.

    Args:
        update: Telegram update.
        context: Bot context.
    """
    from config import get_config
    from db.repository import Repository
    from src.bot.telegram_bot import is_user_whitelisted
    from src.charts.freight_bar import format_freight_message, generate_freight_bar_chart

    if update.effective_user is None or update.message is None:
        return
    if not is_user_whitelisted(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    try:
        config = get_config()
        async with Repository(config.database_url) as repository:
            records = await repository.get_normalized_records(source_types=["freight"], limit=20)

        if not records:
            await update.message.reply_text("No freight rate data available.")
            return

        latest_per_route: dict[str, dict] = {}
        for rec in records:
            route = getattr(rec, "route", None) or getattr(rec, "source_name", "Unknown")
            if route in latest_per_route:
                continue
            normalized = getattr(rec, "normalized_usd", None)
            price = float(normalized if normalized is not None else getattr(rec, "raw_price", 0))
            ts = getattr(rec, "timestamp_utc", None)
            latest_per_route[route] = {
                "route": route,
                "current_rate": price,
                "timestamp": ts,
            }

        route_data = list(latest_per_route.values())
        route_labels = [d["route"] for d in route_data]
        current_rates = [d["current_rate"] for d in route_data]

        chart_buffer = generate_freight_bar_chart(
            route_labels=route_labels,
            current_rates=current_rates,
        )

        message = format_freight_message(route_data)

        await update.message.reply_photo(photo=chart_buffer, caption=message)

    except Exception as e:
        logger.exception(f"Error generating freight report: {e}")
        await update.message.reply_text("An internal error occurred, please try again later.")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history command - get 30-day price history with trend chart.

    Fetches up to 30 days of price records, formats a text table
    showing date / price / % change, and attaches a sparkline-style
    trend chart.

    Args:
        update: Telegram update.
        context: Bot context.
    """
    from datetime import timedelta, timezone

    from config import get_config
    from db.repository import Repository
    from src.bot.telegram_bot import is_user_whitelisted
    from src.charts.trend_chart import format_history_table, generate_trend_chart

    if update.effective_user is None or update.message is None:
        return
    if not is_user_whitelisted(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    try:
        config = get_config()
        async with Repository(config.database_url) as repository:
            records = await repository.get_price_records(limit=30)

        if not records:
            await update.message.reply_text("No price history available.")
            return

        records.reverse()

        dates: list[str] = []
        prices: list[float] = []
        for rec in records:
            ts = getattr(rec, "timestamp_utc", None)
            normalized = getattr(rec, "normalized_usd", None)
            price = float(normalized if normalized is not None else getattr(rec, "raw_price", 0))
            dates.append(ts.strftime("%Y-%m-%d") if ts else "N/A")
            prices.append(price)

        table = format_history_table(dates, prices)
        chart_buffer = generate_trend_chart(dates, prices)

        await update.message.reply_photo(photo=chart_buffer, caption=table)

    except Exception as e:
        logger.exception(f"Error generating history: {e}")
        await update.message.reply_text("An internal error occurred, please try again later.")

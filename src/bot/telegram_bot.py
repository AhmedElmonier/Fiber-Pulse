"""Telegram bot skeleton with whitelisting logic."""

from __future__ import annotations

import logging
import os
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.utils.alert_trigger import PriceAlert

logger = logging.getLogger(__name__)


def get_whitelisted_users() -> set[int]:
    """Get whitelisted user IDs from environment."""
    whitelist = os.getenv("TELEGRAM_WHITELIST", "")
    if not whitelist:
        return set()

    user_ids = set()
    for user_id in whitelist.split(","):
        user_id = user_id.strip()
        if user_id:
            try:
                user_ids.add(int(user_id))
            except ValueError:
                logger.warning(f"Invalid user ID in whitelist: {user_id}")

    return user_ids


def is_user_whitelisted(user_id: int) -> bool:
    """Check if a user is whitelisted."""
    whitelisted = get_whitelisted_users()
    return user_id in whitelisted


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.effective_user is None:
        return
    if update.message is None:
        return

    user_id = update.effective_user.id
    if not is_user_whitelisted(user_id):
        await update.message.reply_text("Unauthorized.")
        return

    await update.message.reply_text(
        "Welcome to FiberPulse Bot!\n\nUse /help to see available commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if update.effective_user is None:
        return
    if update.message is None:
        return

    if not is_user_whitelisted(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/outlook - Get market outlook\n"
        "/buy - Get buy signal\n"
        "/freight - Get freight rates\n"
        "/history - Get history\n"
        "/status - Health check"
    )
    await update.message.reply_text(help_text)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - bot health check.

    Reports bot uptime, database connectivity, number of whitelisted
    users, and scheduler job status.
    """
    import time

    from config import get_config
    from db.repository import Repository

    if update.effective_user is None or update.message is None:
        return
    if not is_user_whitelisted(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    lines = ["BOT STATUS", "=" * 24]

    # --- Uptime ---
    start_time = context.bot_data.get("_start_time")
    if start_time:
        uptime_secs = int(time.time() - start_time)
        hours, remainder = divmod(uptime_secs, 3600)
        minutes, _ = divmod(remainder, 60)
        lines.append(f"  Uptime: {hours}h {minutes}m")
    else:
        lines.append("  Uptime: unknown")

    # --- Whitelist ---
    whitelisted = get_whitelisted_users()
    lines.append(f"  Whitelisted users: {len(whitelisted)}")

    # --- Database ---
    try:
        config = get_config()
        async with Repository(config.database_url) as repository:
            await repository.get_price_records(limit=1)
        lines.append("  Database: connected")
    except Exception:
        lines.append("  Database: UNREACHABLE")

    # --- Scheduler jobs ---
    from src.bot.scheduler import REPORT_HOURS, get_next_report_time

    next_run = get_next_report_time()
    lines.append(f"  Reports: {len(REPORT_HOURS)}x daily (Cairo)")
    lines.append(f"  Next report: {next_run.strftime('%H:%M %Z')}")

    lines.append("=" * 24)
    await update.message.reply_text("\n".join(lines))


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    if not is_user_whitelisted(update.effective_user.id):
        return
    await update.message.reply_text("Unknown command. Use /help.")


def create_bot_application() -> Application:
    """Create and configure the bot application."""
    from src.bot.handlers import error_handler, message_handler

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")

    application = Application.builder().token(token).build()

    from src.bot.commands import outlook_command, buy_command, freight_command, history_command

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("outlook", outlook_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("freight", freight_command))
    application.add_handler(CommandHandler("history", history_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    application.add_error_handler(error_handler)

    async def _post_init(app: Application) -> None:
        import time

        app.bot_data["_start_time"] = time.time()

    application.post_init = _post_init

    return application


def run_bot() -> None:
    """Run the bot in polling mode."""
    app = create_bot_application()
    logger.info("Starting FiberPulse bot...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


async def broadcast_alert(
    application: Application,
    alert: PriceAlert,
) -> int:
    """Broadcast a price alert to all whitelisted users.

    Sends the alert message individually to each whitelisted user,
    logs each send attempt in the alert_log table, and records the
    alert in the suppressor to prevent duplicates.

    Args:
        application: The bot Application instance.
        alert: The PriceAlert to broadcast.

    Returns:
        Number of users the alert was successfully sent to.
    """
    from config import get_config
    from db.repository import Repository
    from src.utils.alert_suppressor import get_suppressor

    whitelisted = get_whitelisted_users()
    if not whitelisted:
        logger.warning("No whitelisted users to broadcast alert to")
        return 0

    message = alert.format_message()
    payload = alert.to_payload()
    sent_count = 0

    config = get_config()
    async with Repository(config.database_url) as repository:
        for user_id in whitelisted:
            status = "success"
            try:
                await application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                )
                sent_count += 1
                logger.info(f"Alert sent to user {user_id} for {alert.instrument_name}")
            except Exception as e:
                status = "failed"
                logger.error(f"Failed to send alert to user {user_id}: {e}")

            try:
                await repository.insert_alert_log(
                    instrument_name=alert.instrument_name,
                    trigger_reason=alert.trigger_reason,
                    target_chat_id=user_id,
                    message_payload=payload,
                    status=status,
                )
            except Exception as e:
                logger.error(f"Failed to log alert for user {user_id}: {e}")

    if sent_count > 0:
        suppressor = get_suppressor()
        suppressor.record_alert_sent(alert.instrument_name, alert.trigger_reason)

    return sent_count


async def _log_alert(
    instrument_name: str,
    trigger_reason: str,
    target_chat_id: int,
    message_payload: dict[str, Any],
    status: str,
) -> None:
    """Log a single alert to the alert_log table.

    Creates its own Repository with an async context manager so
    the connection is always closed, even on failure.

    Args:
        instrument_name: Name of the instrument.
        trigger_reason: Reason for the alert.
        target_chat_id: Telegram Chat ID of recipient.
        message_payload: Alert payload dict.
        status: 'success' or 'failed'.
    """
    try:
        from config import get_config
        from db.repository import Repository

        config = get_config()
        async with Repository(config.database_url) as repository:
            await repository.insert_alert_log(
                instrument_name=instrument_name,
                trigger_reason=trigger_reason,
                target_chat_id=target_chat_id,
                message_payload=message_payload,
                status=status,
            )
    except Exception as e:
        logger.error(f"Failed to log alert: {e}")


async def run_alert_scan(application: Application) -> list[PriceAlert]:
    """Scan for volatility alerts and broadcast them.

    This function is intended to be called periodically by the
    scheduler or manually for testing.

    Args:
        application: The bot Application instance.

    Returns:
        List of alerts that were triggered and broadcast.
    """
    from config import get_config
    from db.repository import Repository
    from src.utils.alert_trigger import check_volatility_with_suppression

    config = get_config()
    repository = Repository(config.database_url)

    try:
        records = await repository.get_price_records(limit=50)
        instruments = list({r.source_name for r in records})

        triggered_alerts: list[PriceAlert] = []

        for instrument in instruments:
            inst_records = await repository.get_price_records(source_name=instrument, limit=2)
            if len(inst_records) < 2:
                continue

            latest = inst_records[0]
            previous = inst_records[1]

            current_price = float(latest.normalized_usd)
            previous_price = float(previous.normalized_usd)

            alert = check_volatility_with_suppression(
                current_price=current_price,
                previous_price=previous_price,
                instrument_name=instrument,
            )
            if alert is not None:
                await broadcast_alert(application, alert)
                triggered_alerts.append(alert)

        return triggered_alerts
    finally:
        await repository.close()


async def broadcast_report(application: Application) -> int:
    """Compose and broadcast a scheduled market report to all whitelisted users.

    Fetches the latest price, freight, and sentiment data, composes a
    report, and sends it individually to every whitelisted user. Each
    send is logged in the alert_log table.

    Args:
        application: The bot Application instance.

    Returns:
        Number of users the report was successfully sent to.
    """
    from config import get_config
    from db.repository import Repository
    from src.bot.scheduler import compose_market_report

    whitelisted = get_whitelisted_users()
    if not whitelisted:
        logger.warning("No whitelisted users to broadcast report to")
        return 0

    config = get_config()
    async with Repository(config.database_url) as repository:
        price_records = await repository.get_price_records(limit=5)
        freight_records = await repository.get_normalized_records(source_types=["freight"], limit=5)
        sentiment_records = await repository.get_sentiment_events(limit=5)

    report_message = compose_market_report(
        price_records=price_records,
        freight_records=freight_records,
        sentiment_records=sentiment_records,
    )

    payload = {
        "type": "scheduled_report",
        "sections": {
            "price_count": len(price_records),
            "freight_count": len(freight_records),
            "sentiment_count": len(sentiment_records),
        },
    }

    sent_count = 0
    async with Repository(config.database_url) as repository:
        for user_id in whitelisted:
            status = "success"
            try:
                await application.bot.send_message(
                    chat_id=user_id,
                    text=report_message,
                )
                sent_count += 1
                logger.info(f"Report sent to user {user_id}")
            except Exception as e:
                status = "failed"
                logger.error(f"Failed to send report to user {user_id}: {e}")

            try:
                await repository.insert_alert_log(
                    instrument_name="market_report",
                    trigger_reason="scheduled_report",
                    target_chat_id=user_id,
                    message_payload=payload,
                    status=status,
                )
            except Exception as e:
                logger.error(f"Failed to log report for user {user_id}: {e}")

    return sent_count


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    run_bot()

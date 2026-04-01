"""Generic message and error handlers for Telegram bot."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle non-command messages.

    Args:
        update: Telegram update.
        context: Bot context.
    """
    from src.bot.telegram_bot import is_user_whitelisted

    user_id = update.effective_user.id if update.effective_user else 0

    if not is_user_whitelisted(user_id):
        return

    if update.message:
        await update.message.reply_text(
            "I didn't understand that. Use /help to see available commands."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot.

    Args:
        update: Telegram update.
        context: Bot context.
    """
    logger.error(f"Update {update} caused error {context.error}")

    if update and update.message:
        await update.message.reply_text(
            "An error occurred while processing your request. Please try again later."
        )


class CommandLogger:
    """Middleware to log command execution time."""

    def __init__(self) -> None:
        self.start_time: float = 0.0

    async def log_command(
        self,
        update: Update,
        command_name: str,
        arguments: str | None = None,
    ) -> None:
        """Log command execution.

        Args:
            update: Telegram update.
            command_name: Name of the command.
            arguments: Optional arguments.
        """
        user_id = update.effective_user.id if update.effective_user else 0

        logger.info(f"Command '{command_name}' from user {user_id}")

        try:
            from config import get_config
            from db.repository import Repository

            config = get_config()
            repository = Repository(config.database_url)

            await repository.insert_bot_command_log(
                user_id=user_id,
                command_name=command_name,
                arguments=arguments,
            )
            await repository.close()
        except Exception as e:
            logger.error(f"Failed to log command: {e}")

    async def log_response_time(
        self,
        update: Update,
        command_name: str,
        response_time_ms: int,
    ) -> None:
        """Log response time for performance monitoring.

        Args:
            update: Telegram update.
            command_name: Name of the command.
            response_time_ms: Time taken to respond.
        """
        logger.info(f"Command '{command_name}' responded in {response_time_ms}ms")

        if response_time_ms > 2000:
            logger.warning(f"Command '{command_name}' exceeded 2s threshold: {response_time_ms}ms")

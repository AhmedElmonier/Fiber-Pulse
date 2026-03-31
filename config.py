"""FiberPulse configuration management.

Loads environment settings for database, timezone, and application configuration.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    database_url: str
    timezone: str
    log_level: str
    currency_rate_api_key: str | None = None
    data_source_credentials: dict[str, str] = field(default_factory=dict)
    telegram_bot_token: str | None = None

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        Looks for a .env file in the current directory or parent directories.
        Falls back to system environment variables.
        """
        # Load .env file if it exists
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()  # Look in parent directories

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        timezone = os.getenv("TIMEZONE", "Africa/Cairo")
        log_level = os.getenv("LOG_LEVEL", "INFO")
        currency_rate_api_key = os.getenv("CURRENCY_RATE_API_KEY")

        # Parse data source credentials if provided
        data_source_credentials: dict[str, str] = {}
        credentials_json = os.getenv("DATA_SOURCE_CREDENTIALS")
        if credentials_json:
            import json

            try:
                data_source_credentials = json.loads(credentials_json)
            except json.JSONDecodeError as e:
                logger.warning(
                    "Invalid DATA_SOURCE_CREDENTIALS value %r: %s",
                    credentials_json,
                    e,
                )
                data_source_credentials = {}

        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

        return cls(
            database_url=database_url,
            timezone=timezone,
            log_level=log_level,
            currency_rate_api_key=currency_rate_api_key,
            data_source_credentials=data_source_credentials,
            telegram_bot_token=telegram_bot_token,
        )

    def validate(self) -> None:
        """Validate that all required settings and source credentials are present.

        Raises:
            ValueError: If a required configuration is missing.
        """
        if not self.database_url:
            raise ValueError("DATABASE_URL is missing")
        
        # Add source-specific validation for Phase 2
        # For MVP, we mainly ensure required sources exist in config if needed
        # (Placeholder for real API keys in later iterations)
        pass

    def get_source_credentials(self, source_name: str) -> str | None:
        """Get credentials for a specific data source.

        Args:
            source_name: The canonical source identifier.

        Returns:
            The credentials for the source, or None if not configured.
        """
        return self.data_source_credentials.get(source_name)


logger = logging.getLogger(__name__)

# Global config instance, lazily loaded
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.

    Lazily loads the configuration on first access.
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reset_config() -> None:
    """Reset the global configuration instance.

    Useful for testing or reloading configuration.
    """
    global _config
    _config = None
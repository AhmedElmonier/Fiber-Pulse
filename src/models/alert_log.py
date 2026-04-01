"""Alert and command log models for Telegram bot integration.

Defines application-level models for tracking alerts and bot commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from enum import Enum


class AlertStatus(str, Enum):
    """Status of an alert message."""

    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class AlertLog:
    """Record of an alert or notification sent to a user.

    Attributes:
        id: Primary key.
        timestamp: When the alert was sent.
        instrument_name: Name of instrument (e.g., 'cai_cotton').
        trigger_reason: Reason for alert (e.g., '3pct_volatility').
        target_chat_id: Telegram Chat/User ID recipient.
        message_payload: Full content of message sent.
        status: 'success' or 'failed'.
    """

    instrument_name: str
    trigger_reason: str
    target_chat_id: int
    message_payload: dict[str, Any]
    status: AlertStatus
    id: int | None = None
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Validate required fields."""
        if not self.instrument_name:
            raise ValueError("instrument_name is required")
        if not self.trigger_reason:
            raise ValueError("trigger_reason is required")
        if self.target_chat_id == 0:
            raise ValueError("target_chat_id must be non-zero")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "instrument_name": self.instrument_name,
            "trigger_reason": self.trigger_reason,
            "target_chat_id": self.target_chat_id,
            "message_payload": self.message_payload,
            "status": self.status.value,
        }


@dataclass
class BotCommandLog:
    """Record of a bot command invocation.

    Attributes:
        id: Primary key.
        user_id: Telegram User ID.
        command_name: Command invoked (e.g., '/buy').
        arguments: Optional arguments to the command.
        timestamp: When command was received.
        response_time_ms: Time taken to respond.
    """

    user_id: int
    command_name: str
    arguments: str | None = None
    id: int | None = None
    timestamp: datetime | None = None
    response_time_ms: int | None = None

    def __post_init__(self) -> None:
        """Validate required fields."""
        if self.user_id <= 0:
            raise ValueError("user_id must be positive")
        if not self.command_name:
            raise ValueError("command_name is required")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "command_name": self.command_name,
            "arguments": self.arguments,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "response_time_ms": self.response_time_ms,
        }

"""Ingestion source model for FiberPulse.

Defines the IngestionSource entity representing a configured data source
for the ingestion pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SourcePriority(int, Enum):
    """Priority level for ingestion sources.

    Lower numeric values indicate higher priority (primary sources).
    """

    PRIMARY = 1
    SECONDARY = 2
    FALLBACK = 3
    UTILITY = 99


class SourceCategory(str, Enum):
    """Category of ingestion source."""

    PRIMARY = "primary"
    FALLBACK = "fallback"
    CURRENCY_RATE = "currency_rate"
    UTILITY = "utility"


@dataclass
class IngestionSource:
    """A configured ingestion source for the FiberPulse pipeline.

    Attributes:
        source_name: Canonical identifier (primary key).
        display_name: Human-friendly source label.
        priority: Priority level (lower = higher priority).
        source_url: Feed endpoint or documentation URL.
        category: Source category (primary, fallback, currency_rate, utility).
        active: Whether the source is configured and enabled.
        fallback_to: Linked fallback source for degraded flow.
        last_run_at: Last ingestion attempt (UTC).
        config: Additional source configuration.
        created_at: Insertion timestamp.
        updated_at: Last update timestamp.
    """

    source_name: str = ""
    display_name: str = ""
    priority: int = 1
    source_url: str | None = None
    category: SourceCategory = SourceCategory.PRIMARY
    active: bool = True
    fallback_to: str | None = None
    last_run_at: datetime | None = None
    config: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        if not self.source_name:
            raise ValueError("source_name is required")
        if not self.display_name:
            raise ValueError("display_name is required")

    @property
    def is_primary(self) -> bool:
        """Check if this is a primary source."""
        return self.category == SourceCategory.PRIMARY

    @property
    def is_fallback(self) -> bool:
        """Check if this is a fallback source."""
        return self.category == SourceCategory.FALLBACK

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary representation."""
        return {
            "source_name": self.source_name,
            "display_name": self.display_name,
            "priority": self.priority,
            "source_url": self.source_url,
            "category": self.category.value,
            "active": self.active,
            "fallback_to": self.fallback_to,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
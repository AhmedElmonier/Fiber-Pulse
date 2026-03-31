"""Macro feed record model for FiberPulse ingestion.

Defines the MacroFeedRecord entity representing a single macroeconomic
feed record (FX, commodities, utilities) from a configured source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from models.price_history import SourceType


@dataclass
class MacroFeedRecord:
    """A single macroeconomic feed record (FX, commodities, utilities) from the ingestion pipeline.

    Represents normalized macroeconomic indicators, standardized to USD for
    unified market analysis and correlation studies. These records are typically
    persisted to the price_history table with SourceType.MACRO.

    Attributes:
        id (UUID): Unique primary key for the record.
        source_name (str): Canonical source identifier (e.g. 'fx_usd_inr').
        commodity (str): Macro commodity or indicator (e.g. 'brent_oil', 'usd_inr').
        timestamp_utc (datetime): Observation timestamp for the macro data (UTC).
        raw_price (float): Original reported macro value.
        raw_currency (str): Original value currency code (3-letter ISO).
        normalized_usd (float): USD-converted macro value.
        source_type (SourceType): Type of data source, defaults to MACRO.
        conversion_rate (float, optional): Exchange rate used for USD normalization.
        normalized_at (datetime, optional): Time conversion was applied (UTC).
        quality_flags (dict): Validation and source health indicators (stale, fallback).
        metadata (dict): Raw source payload and diagnostic audit context.
        created_at (datetime, optional): Database insertion timestamp.
        updated_at (datetime, optional): Last record update timestamp.
    """

    source_name: str
    commodity: str
    timestamp_utc: datetime
    raw_price: float
    raw_currency: str
    normalized_usd: float
    id: UUID = field(default_factory=uuid4)
    source_type: SourceType = SourceType.MACRO
    conversion_rate: float | None = None
    normalized_at: datetime | None = None
    quality_flags: dict[str, Any] = field(default_factory=lambda: {"stale": False, "fallback": False})
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate required fields after initialization.

        Ensures mandatory fields are populated and price values are non-negative.

        Raises:
            ValueError: If validation rules are violated.
        """
        if not self.source_name:
            raise ValueError("source_name is required")
        if not self.commodity:
            raise ValueError("commodity is required")
        if self.timestamp_utc is None:
            raise ValueError("timestamp_utc is required")
        if self.raw_price < 0:
            raise ValueError("raw_price must be non-negative")
        if self.normalized_usd < 0:
            raise ValueError("normalized_usd must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        """Convert the record to a dictionary representation.

        Useful for JSON serialization and data exchange.

        Returns:
            A dictionary containing all record attributes.
        """
        return {
            "id": str(self.id),
            "source_name": self.source_name,
            "source_type": self.source_type.value,
            "commodity": self.commodity,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None,
            "raw_price": self.raw_price,
            "raw_currency": self.raw_currency,
            "normalized_usd": self.normalized_usd,
            "conversion_rate": self.conversion_rate,
            "normalized_at": self.normalized_at.isoformat() if self.normalized_at else None,
            "quality_flags": self.quality_flags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

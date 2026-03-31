"""Freight rate model for FiberPulse ingestion.

Defines the FreightRate entity representing a single logistics freight rate
record from a configured ingestion source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class FreightRate:
    """A single logistics freight rate record produced by the ingestion pipeline.

    Represents normalized freight index data from sources like CCFI or Drewry,
    standardized to USD for downstream logistics cost analysis.

    Attributes:
        id (UUID): Unique primary key for the record.
        source_name (str): Canonical source identifier (e.g. 'ccfi_med').
        route (str): Logistics route or corridor (e.g. 'Mediterranean').
        timestamp_utc (datetime): Observation timestamp for the freight rate (UTC).
        raw_price (float): Original reported freight rate value.
        raw_currency (str): Original rate currency code (3-letter ISO).
        normalized_usd (float): USD-converted freight rate value.
        conversion_rate (float, optional): Exchange rate used for USD normalization.
        quality_flags (dict): Validation and source health indicators (stale, fallback).
        metadata (dict): Raw source payload and audit context.
        created_at (datetime, optional): Database insertion timestamp.
        updated_at (datetime, optional): Last record update timestamp.
    """

    source_name: str
    route: str
    timestamp_utc: datetime
    raw_price: float
    raw_currency: str
    normalized_usd: float
    id: UUID = field(default_factory=uuid4)
    conversion_rate: float | None = None
    quality_flags: dict[str, Any] = field(default_factory=lambda: {"stale": False, "fallback": False})
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate required fields after initialization.

        Raises:
            ValueError: If mandatory fields are empty or prices are negative.
        """
        if not self.source_name:
            raise ValueError("source_name is required")
        if not self.route:
            raise ValueError("route is required")
        if self.timestamp_utc is None:
            raise ValueError("timestamp_utc is required")
        if self.raw_price is None:
            raise ValueError("raw_price is required")
        if self.normalized_usd is None:
            raise ValueError("normalized_usd is required")
        if self.raw_price < 0:
            raise ValueError("raw_price must be non-negative")
        if self.normalized_usd < 0:
            raise ValueError("normalized_usd must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        """Convert the record to a dictionary representation.

        Useful for JSON serialization and API responses.

        Returns:
            A dictionary containing all record fields.
        """
        return {
            "id": str(self.id),
            "source_name": self.source_name,
            "route": self.route,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None,
            "raw_price": self.raw_price,
            "raw_currency": self.raw_currency,
            "normalized_usd": self.normalized_usd,
            "conversion_rate": self.conversion_rate,
            "quality_flags": self.quality_flags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

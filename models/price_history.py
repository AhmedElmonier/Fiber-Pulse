"""Price history model for FiberPulse ingestion.

Defines the PriceHistoryRecord entity representing a single canonical price record
produced by the ingestion pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class SourceType(str, Enum):
    """Type of data source."""

    SPOT = "spot"
    FUTURE = "future"
    FALLBACK = "fallback"
    MACRO = "macro"


@dataclass
class PriceHistoryRecord:
    """A single canonical price record produced by the ingestion pipeline.

    Attributes:
        id: Unique primary key.
        source_name: Canonical source identifier, e.g. 'cai_spot', 'mcx_futures'.
        source_type: Type of data source (spot, future, fallback, macro).
        timestamp_utc: Recorded timestamp for the underlying market price (UTC).
        commodity: Product type, e.g. 'cotton'.
        region: Optional delivery region or location context.
        raw_price: Original reported price value.
        raw_currency: Original price currency code.
        normalized_usd: USD-converted price value.
        conversion_rate: Exchange rate used for USD normalization.
        normalized_at: Time the conversion was applied (UTC).
        quality_flags: Validation and source health indicators.
        metadata: Raw source payload, extraction context, and audit details.
        created_at: Insertion timestamp.
        updated_at: Last update timestamp.
    """

    source_name: str
    timestamp_utc: datetime
    raw_price: float
    normalized_usd: float
    source_type: SourceType = SourceType.SPOT
    raw_currency: str = "USD"
    id: UUID = field(default_factory=uuid4)
    commodity: str = "cotton"
    region: str | None = None
    conversion_rate: float | None = None
    normalized_at: datetime | None = None
    quality_flags: dict[str, Any] = field(default_factory=lambda: {"stale": False, "fallback": False})
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        if not self.source_name:
            raise ValueError("source_name is required")
        if self.timestamp_utc is None:
            raise ValueError("timestamp_utc is required")
        if self.raw_price <= 0:
            raise ValueError("raw_price must be positive")
        if self.normalized_usd <= 0:
            raise ValueError("normalized_usd must be positive")

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary representation."""
        return {
            "id": str(self.id),
            "source_name": self.source_name,
            "source_type": self.source_type.value,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None,
            "commodity": self.commodity,
            "region": self.region,
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

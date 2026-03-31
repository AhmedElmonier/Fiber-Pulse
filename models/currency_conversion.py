"""Currency conversion model for FiberPulse ingestion.

Defines the CurrencyConversionRecord entity representing the authoritative
currency rate used for USD normalization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class CurrencyConversionRecord:
    """Defines the authoritative currency rate used for USD normalization.

    Attributes:
        id: Unique primary key.
        currency: Currency code, e.g. 'INR', 'CNY', 'USD'.
        rate_to_usd: Exchange rate used to normalize values.
        rate_timestamp: Timestamp for the rate (UTC).
        source_name: Source of the conversion rate.
        retrieved_at: When the rate was fetched (UTC).
        metadata: Raw provider payload.
    """

    id: UUID = field(default_factory=uuid4)
    currency: str = ""
    rate_to_usd: float = 0.0
    rate_timestamp: datetime | None = None
    source_name: str = ""
    retrieved_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        if not self.currency:
            raise ValueError("currency is required")
        if self.rate_to_usd <= 0:
            raise ValueError("rate_to_usd must be positive")
        if not self.source_name:
            raise ValueError("source_name is required")

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary representation."""
        return {
            "id": str(self.id),
            "currency": self.currency,
            "rate_to_usd": self.rate_to_usd,
            "rate_timestamp": self.rate_timestamp.isoformat() if self.rate_timestamp else None,
            "source_name": self.source_name,
            "retrieved_at": self.retrieved_at.isoformat() if self.retrieved_at else None,
            "metadata": self.metadata,
        }
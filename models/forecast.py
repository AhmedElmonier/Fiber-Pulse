"""Forecast model for FiberPulse prediction pipeline.

Defines the Forecast entity representing a price prediction with confidence intervals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Forecast:
    """A single price forecast with confidence interval.

    Attributes:
        id: Unique primary key.
        target_source: The source name being predicted (e.g., 'cai_spot').
        timestamp_utc: The observation time this forecast was generated (UTC).
        target_timestamp_utc: The future time being predicted (UTC).
        horizon_hours: Forecast horizon in hours.
        predicted_value: Point estimate (normalized USD).
        lower_bound: Lower confidence interval bound.
        upper_bound: Upper confidence interval bound.
        confidence_level: e.g., 0.95 for a 95% interval.
        model_version: Identifier for the model that generated this.
        is_decayed: True if CI was widened due to stale inputs.
        created_at: Insertion timestamp.
    """

    target_source: str
    timestamp_utc: datetime
    target_timestamp_utc: datetime
    horizon_hours: int
    predicted_value: float
    lower_bound: float
    upper_bound: float
    confidence_level: float = 0.95
    id: UUID = field(default_factory=uuid4)
    model_version: str = "baseline-1.0.0"
    is_decayed: bool = False
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        if not self.target_source:
            raise ValueError("target_source is required")
        if self.predicted_value <= 0:
            raise ValueError("predicted_value must be positive")
        if self.lower_bound <= 0:
            raise ValueError("lower_bound must be positive")
        if self.upper_bound <= 0:
            raise ValueError("upper_bound must be positive")
        if self.upper_bound < self.predicted_value:
            raise ValueError("upper_bound must be >= predicted_value")
        if self.lower_bound > self.predicted_value:
            raise ValueError("lower_bound must be <= predicted_value")
        if self.target_timestamp_utc <= self.timestamp_utc:
            raise ValueError("target_timestamp_utc must be in the future relative to timestamp_utc")

    def to_dict(self) -> dict[str, Any]:
        """Convert forecast to dictionary representation."""
        return {
            "id": str(self.id),
            "target_source": self.target_source,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None,
            "target_timestamp_utc": self.target_timestamp_utc.isoformat()
            if self.target_timestamp_utc
            else None,
            "horizon_hours": self.horizon_hours,
            "predicted_value": self.predicted_value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "confidence_level": self.confidence_level,
            "model_version": self.model_version,
            "is_decayed": self.is_decayed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

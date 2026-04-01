"""Sentiment event model for FiberPulse NLP pipeline.

Defines the SentimentEvent entity representing a scored market headline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class SentimentLabel(str, Enum):
    """Sentiment classification for a headline."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class SentimentEvent:
    """A single sentiment-scored market headline.

    Attributes:
        id: Unique primary key.
        headline: Raw text of the headline.
        source_name: Canonical source identifier.
        timestamp_utc: When the headline was published (UTC).
        sentiment_score: Classification result (bullish, bearish, neutral).
        confidence: Numeric confidence in the scoring (0.0 to 1.0).
        engine_version: Version of the sentiment engine used.
        metadata: Original payload and keyword hits.
        created_at: Insertion timestamp.
    """

    headline: str
    source_name: str
    timestamp_utc: datetime
    sentiment_score: SentimentLabel
    confidence: float
    id: UUID = field(default_factory=uuid4)
    engine_version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        if not self.headline:
            raise ValueError("headline is required")
        if not self.source_name:
            raise ValueError("source_name is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            "id": str(self.id),
            "headline": self.headline,
            "source_name": self.source_name,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None,
            "sentiment_score": self.sentiment_score.value,
            "confidence": self.confidence,
            "engine_version": self.engine_version,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

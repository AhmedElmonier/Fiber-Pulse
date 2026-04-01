"""Contract tests for sentiment event payload.

Validates that SentimentEvent records conform to the sentiment-event.json contract:
- source_name: string
- timestamp_utc: ISO-8601 string
- headline: string
- sentiment_score: bullish | bearish | neutral
- confidence: float (0.0 - 1.0)
- metadata: object
"""

from __future__ import annotations

from datetime import datetime

import pytest

from models.sentiment_event import SentimentEvent, SentimentLabel


class TestSentimentEventContract:
    """Validate sentiment event records against sentiment-event.json contract."""

    def test_headline_required(self):
        """Contract: headline is required."""
        now = datetime.now()
        with pytest.raises(ValueError, match="headline"):
            SentimentEvent(
                headline="",
                source_name="reuters",
                timestamp_utc=now,
                sentiment_score=SentimentLabel.BULLISH,
                confidence=0.8,
            )

    def test_source_name_required(self):
        """Contract: source_name is required."""
        now = datetime.now()
        with pytest.raises(ValueError, match="source_name"):
            SentimentEvent(
                headline="Cotton prices surge on strong demand",
                source_name="",
                timestamp_utc=now,
                sentiment_score=SentimentLabel.BULLISH,
                confidence=0.8,
            )

    def test_confidence_range_validation(self):
        """Contract: confidence must be between 0.0 and 1.0."""
        now = datetime.now()
        with pytest.raises(ValueError, match="confidence"):
            SentimentEvent(
                headline="Test headline",
                source_name="reuters",
                timestamp_utc=now,
                sentiment_score=SentimentLabel.BULLISH,
                confidence=1.5,
            )

    def test_confidence_negative_rejected(self):
        """Contract: negative confidence must be rejected."""
        now = datetime.now()
        with pytest.raises(ValueError, match="confidence"):
            SentimentEvent(
                headline="Test headline",
                source_name="reuters",
                timestamp_utc=now,
                sentiment_score=SentimentLabel.BEARISH,
                confidence=-0.1,
            )

    def test_sentiment_label_bullish_valid(self):
        """Contract: bullish sentiment label should be accepted."""
        now = datetime.now()
        event = SentimentEvent(
            headline="Cotton prices surge on strong demand",
            source_name="reuters",
            timestamp_utc=now,
            sentiment_score=SentimentLabel.BULLISH,
            confidence=0.8,
        )
        assert event.sentiment_score == SentimentLabel.BULLISH

    def test_sentiment_label_bearish_valid(self):
        """Contract: bearish sentiment label should be accepted."""
        now = datetime.now()
        event = SentimentEvent(
            headline="Cotton prices fall on weak demand",
            source_name="reuters",
            timestamp_utc=now,
            sentiment_score=SentimentLabel.BEARISH,
            confidence=0.75,
        )
        assert event.sentiment_score == SentimentLabel.BEARISH

    def test_sentiment_label_neutral_valid(self):
        """Contract: neutral sentiment label should be accepted."""
        now = datetime.now()
        event = SentimentEvent(
            headline="Cotton prices remain steady",
            source_name="reuters",
            timestamp_utc=now,
            sentiment_score=SentimentLabel.NEUTRAL,
            confidence=0.6,
        )
        assert event.sentiment_score == SentimentLabel.NEUTRAL

    def test_sentiment_event_to_dict_includes_all_fields(self):
        """Contract: to_dict must include all required fields."""
        now = datetime.now()
        event = SentimentEvent(
            headline="Cotton prices surge on strong demand",
            source_name="reuters",
            timestamp_utc=now,
            sentiment_score=SentimentLabel.BULLISH,
            confidence=0.85,
            engine_version="1.0.0",
            metadata={"keywords": ["surge", "strong", "demand"]},
        )
        event.created_at = now
        result = event.to_dict()

        assert "headline" in result
        assert "source_name" in result
        assert "timestamp_utc" in result
        assert "sentiment_score" in result
        assert "confidence" in result
        assert "engine_version" in result
        assert "metadata" in result
        assert result["sentiment_score"] == "bullish"
        assert result["confidence"] == 0.85

    def test_default_engine_version(self):
        """Contract: engine_version defaults to '1.0.0'."""
        now = datetime.now()
        event = SentimentEvent(
            headline="Test",
            source_name="reuters",
            timestamp_utc=now,
            sentiment_score=SentimentLabel.NEUTRAL,
            confidence=0.5,
        )
        assert event.engine_version == "1.0.0"

    def test_uuid_auto_generated(self):
        """Contract: UUID is auto-generated for id."""
        now = datetime.now()
        event1 = SentimentEvent(
            headline="Test headline",
            source_name="reuters",
            timestamp_utc=now,
            sentiment_score=SentimentLabel.BULLISH,
            confidence=0.8,
        )
        event2 = SentimentEvent(
            headline="Test headline",
            source_name="reuters",
            timestamp_utc=now,
            sentiment_score=SentimentLabel.BULLISH,
            confidence=0.8,
        )
        assert event1.id != event2.id

    def test_metadata_default_empty(self):
        """Contract: metadata defaults to empty dict."""
        now = datetime.now()
        event = SentimentEvent(
            headline="Test headline",
            source_name="reuters",
            timestamp_utc=now,
            sentiment_score=SentimentLabel.NEUTRAL,
            confidence=0.5,
        )
        assert event.metadata == {}

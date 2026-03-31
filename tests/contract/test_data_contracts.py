"""Contract tests for Phase 2 logistics and macro feeds.

Validates that raw payloads and normalized records conform to defined contracts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from agents.normalizer import Normalizer, NormalizerError
from models.freight_rate import FreightRate
from models.macro_feed_record import MacroFeedRecord
from models.price_history import SourceType
from models.source_health import HealthStatus, SourceHealthRecord
from utils.usd_converter import get_converter


@pytest.fixture(autouse=True)
def setup_rates():
    """Setup conversion rates for testing."""
    converter = get_converter()
    converter.set_rate("INR", 83.0)
    converter.set_rate("CNY", 7.2)
    yield
    # No need to reset here as it might affect other tests, 
    # but in a real suite we might reset_converter()


def validate_raw_payload(payload: dict[str, Any]) -> None:
    """Validate raw source payload against contract."""
    required = ["source_name", "timestamp_utc", "commodity", "raw_price", "raw_currency"]
    for field in required:
        assert field in payload, f"Missing required field: {field}"
    
    assert isinstance(payload["source_name"], str)
    assert isinstance(payload["commodity"], str)
    assert float(payload["raw_price"]) >= 0
    assert len(payload["raw_currency"]) == 3


def validate_normalized_freight(record: FreightRate) -> None:
    """Validate normalized freight record against contract."""
    assert record.source_name
    assert record.route
    assert isinstance(record.timestamp_utc, datetime)
    assert record.raw_price >= 0
    assert len(record.raw_currency) == 3
    assert record.normalized_usd >= 0
    assert isinstance(record.quality_flags, dict)
    assert "stale" in record.quality_flags
    assert "fallback" in record.quality_flags
    assert isinstance(record.metadata, dict)


def validate_normalized_macro(record: MacroFeedRecord) -> None:
    """Validate normalized macro record against contract."""
    assert record.source_name
    assert record.source_type == SourceType.MACRO
    assert isinstance(record.timestamp_utc, datetime)
    assert record.commodity
    assert record.raw_price >= 0
    assert len(record.raw_currency) == 3
    assert record.normalized_usd >= 0
    assert isinstance(record.quality_flags, dict)
    assert "stale" in record.quality_flags
    assert "fallback" in record.quality_flags
    assert isinstance(record.metadata, dict)


def validate_source_health(record: SourceHealthRecord) -> None:
    """Validate source health record against contract."""
    assert record.source_name
    assert isinstance(record.status, HealthStatus)
    assert isinstance(record.last_checked_at, datetime)
    assert isinstance(record.fallback_active, bool)
    if record.status == HealthStatus.STALE:
        assert record.stale_duration_minutes is not None


class TestDataContracts:
    """Contract validation tests."""

    def test_raw_payload_contract(self):
        """Test raw source payload contract."""
        payload = {
            "source_name": "test_source",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "commodity": "oil_spot",
            "raw_price": 75.5,
            "raw_currency": "USD",
            "metadata": {"test": True}
        }
        validate_raw_payload(payload)

    def test_normalized_freight_contract(self):
        """Test normalized freight record contract."""
        normalizer = Normalizer()
        payload = {
            "source_name": "ccfi_med",
            "route": "Mediterranean",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "raw_price": 1200.0,
            "raw_currency": "USD"
        }
        record = normalizer.normalize_freight(payload)
        validate_normalized_freight(record)

    def test_normalized_macro_contract(self):
        """Test normalized macro record contract."""
        normalizer = Normalizer()
        payload = {
            "source_name": "fx_usd_inr",
            "commodity": "usd_inr",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "raw_price": 83.2,
            "raw_currency": "INR"
        }
        record = normalizer.normalize_macro(payload)
        validate_normalized_macro(record)

    def test_source_health_contract(self):
        """Test source health record contract."""
        record = SourceHealthRecord(
            source_name="test_source",
            status=HealthStatus.STALE,
            last_success_at=datetime.now(timezone.utc),
            last_checked_at=datetime.now(timezone.utc),
            stale_duration_minutes=60,
            remarks="Testing staleness"
        )
        validate_source_health(record)


@pytest.mark.parametrize("payload, error_match", [
    ({"source_name": "test"}, "Missing required field: timestamp_utc"),
    ({"source_name": "test", "timestamp_utc": "invalid", "commodity": "c", "raw_price": 1, "raw_currency": "USD"}, "Invalid timestamp format"),
    ({"source_name": "test", "timestamp_utc": "2023-01-01T00:00:00Z", "commodity": "c", "raw_price": -1, "raw_currency": "USD"}, "must be non-negative"),
    ({"source_name": "test", "timestamp_utc": "2023-01-01T00:00:00Z", "commodity": "c", "raw_price": 1, "raw_currency": "INVALID"}, "must be a 3-letter currency code"),
])
def test_normalization_failures(payload, error_match):
    """Test normalization failures for invalid payloads."""
    normalizer = Normalizer()
    with pytest.raises(NormalizerError, match=error_match):
        normalizer.normalize_macro(payload)

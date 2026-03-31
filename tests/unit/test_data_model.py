"""Unit tests for FiberPulse data models.

Verifies entity definitions, required fields, and unique constraints.
"""

from datetime import datetime, timezone

import pytest

from models.currency_conversion import CurrencyConversionRecord
from models.ingestion_source import IngestionSource, SourceCategory, SourcePriority
from models.price_history import PriceHistoryRecord, SourceType
from models.source_health import HealthStatus, SourceHealthRecord


class TestPriceHistoryRecord:
    """Tests for PriceHistoryRecord model."""

    def test_create_price_history_record(self) -> None:
        """Test creating a valid price history record."""
        now = datetime.now(timezone.utc)
        record = PriceHistoryRecord(
            source_name="cai_spot",
            source_type=SourceType.SPOT,
            timestamp_utc=now,
            commodity="cotton",
            raw_price=100.50,
            raw_currency="USD",
            normalized_usd=100.50,
        )

        assert record.source_name == "cai_spot"
        assert record.source_type == SourceType.SPOT
        assert record.timestamp_utc == now
        assert record.commodity == "cotton"
        assert record.raw_price == 100.50
        assert record.raw_currency == "USD"
        assert record.normalized_usd == 100.50
        assert record.quality_flags == {"stale": False, "fallback": False}

    def test_price_history_record_requires_source_name(self) -> None:
        """Test that source_name is required."""
        with pytest.raises(ValueError, match="source_name is required"):
            PriceHistoryRecord(
                source_name="",
                timestamp_utc=datetime.now(timezone.utc),
                raw_price=100.0,
                normalized_usd=100.0,
            )

    def test_price_history_record_requires_timestamp(self) -> None:
        """Test that timestamp_utc is required."""
        with pytest.raises(ValueError, match="timestamp_utc is required"):
            PriceHistoryRecord(
                source_name="cai_spot",
                timestamp_utc=None,
                raw_price=100.0,
                normalized_usd=100.0,
            )

    def test_price_history_record_positive_price(self) -> None:
        """Test that raw_price must be positive."""
        with pytest.raises(ValueError, match="raw_price must be positive"):
            PriceHistoryRecord(
                source_name="cai_spot",
                source_type=SourceType.SPOT,
                timestamp_utc=datetime.now(timezone.utc),
                raw_price=0,
                normalized_usd=100.0,
            )

    def test_price_history_record_positive_normalized_usd(self) -> None:
        """Test that normalized_usd must be positive."""
        with pytest.raises(ValueError, match="normalized_usd must be positive"):
            PriceHistoryRecord(
                source_name="cai_spot",
                source_type=SourceType.SPOT,
                timestamp_utc=datetime.now(timezone.utc),
                raw_price=100.0,
                normalized_usd=0,
            )

    def test_price_history_record_to_dict(self) -> None:
        """Test serialization to dictionary."""
        now = datetime.now(timezone.utc)
        record = PriceHistoryRecord(
            source_name="cai_spot",
            source_type=SourceType.SPOT,
            timestamp_utc=now,
            commodity="cotton",
            region="Egypt",
            raw_price=100.50,
            raw_currency="USD",
            normalized_usd=100.50,
            conversion_rate=1.0,
        )

        data = record.to_dict()
        assert data["source_name"] == "cai_spot"
        assert data["source_type"] == "spot"
        assert data["commodity"] == "cotton"
        assert data["region"] == "Egypt"
        assert data["raw_price"] == 100.50
        assert data["normalized_usd"] == 100.50

    def test_price_history_record_with_region(self) -> None:
        """Test creating a record with optional region."""
        record = PriceHistoryRecord(
            source_name="mcx_futures",
            source_type=SourceType.FUTURE,
            timestamp_utc=datetime.now(timezone.utc),
            commodity="cotton",
            region="India",
            raw_price=50000.0,
            raw_currency="INR",
            normalized_usd=600.0,
        )
        assert record.region == "India"

    def test_price_history_record_quality_flags(self) -> None:
        """Test creating a record with quality flags."""
        record = PriceHistoryRecord(
            source_name="cai_spot",
            source_type=SourceType.SPOT,
            timestamp_utc=datetime.now(timezone.utc),
            raw_price=100.0,
            normalized_usd=100.0,
            quality_flags={"stale": True, "fallback": True, "fallback_source": "ccfgroup"},
        )
        assert record.quality_flags["stale"] is True
        assert record.quality_flags["fallback"] is True
        assert record.quality_flags["fallback_source"] == "ccfgroup"


class TestSourceHealthRecord:
    """Tests for SourceHealthRecord model."""

    def test_create_source_health_record(self) -> None:
        """Test creating a valid source health record."""
        now = datetime.now(timezone.utc)
        record = SourceHealthRecord(
            source_name="cai_spot",
            status=HealthStatus.LIVE,
            last_checked_at=now,
        )

        assert record.source_name == "cai_spot"
        assert record.status == HealthStatus.LIVE
        assert record.fallback_active is False

    def test_source_health_record_requires_source_name(self) -> None:
        """Test that source_name is required."""
        with pytest.raises(ValueError, match="source_name is required"):
            SourceHealthRecord(last_checked_at=datetime.now(timezone.utc))

    def test_source_health_record_requires_last_checked(self) -> None:
        """Test that last_checked_at is required."""
        with pytest.raises(ValueError, match="last_checked_at is required"):
            SourceHealthRecord(source_name="cai_spot")

    def test_source_health_record_status_values(self) -> None:
        """Test all health status values."""
        now = datetime.now(timezone.utc)
        for status in [HealthStatus.LIVE, HealthStatus.STALE, HealthStatus.DEGRADED, HealthStatus.FAILED]:
            record = SourceHealthRecord(
                source_name="test_source",
                status=status,
                last_checked_at=now,
            )
            assert record.status == status

    def test_source_health_record_to_dict(self) -> None:
        """Test serialization to dictionary."""
        now = datetime.now(timezone.utc)
        record = SourceHealthRecord(
            source_name="cai_spot",
            status=HealthStatus.STALE,
            last_success_at=now,
            last_checked_at=now,
            stale_duration_minutes=120,
            remarks="Data is 120 minutes old",
        )

        data = record.to_dict()
        assert data["source_name"] == "cai_spot"
        assert data["status"] == "stale"
        assert data["stale_duration_minutes"] == 120


class TestIngestionSource:
    """Tests for IngestionSource model."""

    def test_create_ingestion_source(self) -> None:
        """Test creating a valid ingestion source."""
        source = IngestionSource(
            source_name="cai_spot",
            display_name="CAI Cotton Spot",
            priority=1,
            category=SourceCategory.PRIMARY,
        )

        assert source.source_name == "cai_spot"
        assert source.display_name == "CAI Cotton Spot"
        assert source.priority == 1
        assert source.is_primary is True
        assert source.is_fallback is False

    def test_ingestion_source_requires_source_name(self) -> None:
        """Test that source_name is required."""
        with pytest.raises(ValueError, match="source_name is required"):
            IngestionSource(display_name="Test Source")

    def test_ingestion_source_requires_display_name(self) -> None:
        """Test that display_name is required."""
        with pytest.raises(ValueError, match="display_name is required"):
            IngestionSource(source_name="test_source")

    def test_ingestion_source_fallback(self) -> None:
        """Test fallback source category."""
        source = IngestionSource(
            source_name="ccfgroup",
            display_name="CCFGroup",
            priority=3,
            category=SourceCategory.FALLBACK,
        )
        assert source.is_fallback is True
        assert source.is_primary is False

    def test_ingestion_source_to_dict(self) -> None:
        """Test serialization to dictionary."""
        source = IngestionSource(
            source_name="cai_spot",
            display_name="CAI Cotton Spot",
            priority=1,
            category=SourceCategory.PRIMARY,
            source_url="https://example.com/data",
        )

        data = source.to_dict()
        assert data["source_name"] == "cai_spot"
        assert data["display_name"] == "CAI Cotton Spot"
        assert data["priority"] == 1
        assert data["category"] == "primary"


class TestCurrencyConversionRecord:
    """Tests for CurrencyConversionRecord model."""

    def test_create_currency_conversion_record(self) -> None:
        """Test creating a valid currency conversion record."""
        now = datetime.now(timezone.utc)
        record = CurrencyConversionRecord(
            currency="INR",
            rate_to_usd=83.0,
            rate_timestamp=now,
            source_name="currency_api",
            retrieved_at=now,
        )

        assert record.currency == "INR"
        assert record.rate_to_usd == 83.0
        assert record.source_name == "currency_api"

    def test_currency_conversion_record_requires_currency(self) -> None:
        """Test that currency is required."""
        with pytest.raises(ValueError, match="currency is required"):
            CurrencyConversionRecord(
                rate_to_usd=83.0,
                source_name="test",
            )

    def test_currency_conversion_record_positive_rate(self) -> None:
        """Test that rate_to_usd must be positive."""
        with pytest.raises(ValueError, match="rate_to_usd must be positive"):
            CurrencyConversionRecord(
                currency="INR",
                rate_to_usd=0,
                source_name="test",
            )

    def test_currency_conversion_record_to_dict(self) -> None:
        """Test serialization to dictionary."""
        now = datetime.now(timezone.utc)
        record = CurrencyConversionRecord(
            currency="INR",
            rate_to_usd=83.0,
            rate_timestamp=now,
            source_name="currency_api",
            retrieved_at=now,
        )

        data = record.to_dict()
        assert data["currency"] == "INR"
        assert data["rate_to_usd"] == 83.0
        assert data["source_name"] == "currency_api"


class TestEnums:
    """Tests for enum values."""

    def test_source_type_values(self) -> None:
        """Test SourceType enum values."""
        assert SourceType.SPOT.value == "spot"
        assert SourceType.FUTURE.value == "future"
        assert SourceType.FALLBACK.value == "fallback"
        assert SourceType.MACRO.value == "macro"

    def test_health_status_values(self) -> None:
        """Test HealthStatus enum values."""
        assert HealthStatus.LIVE.value == "live"
        assert HealthStatus.STALE.value == "stale"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.FAILED.value == "failed"

    def test_source_category_values(self) -> None:
        """Test SourceCategory enum values."""
        assert SourceCategory.PRIMARY.value == "primary"
        assert SourceCategory.FALLBACK.value == "fallback"
        assert SourceCategory.CURRENCY_RATE.value == "currency_rate"
        assert SourceCategory.UTILITY.value == "utility"
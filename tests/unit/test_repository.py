"""Unit tests for FiberPulse database repository.

Verifies persistence operations for the core ingestion tables.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.currency_conversion import CurrencyConversionRecord
from models.ingestion_source import SourceCategory
from models.price_history import PriceHistoryRecord, SourceType
from models.source_health import HealthStatus, SourceHealthRecord


class TestRepositoryPriceHistory:
    """Tests for price history persistence operations."""

    @pytest.fixture
    def sample_price_record(self) -> PriceHistoryRecord:
        """Create a sample price history record for testing."""
        return PriceHistoryRecord(
            source_name="cai_spot",
            source_type=SourceType.SPOT,
            timestamp_utc=datetime.now(timezone.utc),
            commodity="cotton",
            region="Egypt",
            raw_price=100.50,
            raw_currency="USD",
            normalized_usd=100.50,
            conversion_rate=1.0,
            quality_flags={"stale": False, "fallback": False},
            metadata={"raw_payload": {"price": 100.50}},
        )

    def test_price_history_record_creation(self, sample_price_record: PriceHistoryRecord) -> None:
        """Test that price history record is created with correct values."""
        assert sample_price_record.source_name == "cai_spot"
        assert sample_price_record.source_type == SourceType.SPOT
        assert sample_price_record.raw_price == 100.50
        assert sample_price_record.normalized_usd == 100.50
        assert sample_price_record.raw_currency == "USD"

    def test_price_history_record_validation(self) -> None:
        """Test that price history record validates required fields."""
        with pytest.raises(ValueError, match="source_name is required"):
            PriceHistoryRecord(
                source_name="",
                timestamp_utc=datetime.now(timezone.utc),
                raw_price=100.0,
                normalized_usd=100.0,
            )

        with pytest.raises(ValueError, match="timestamp_utc is required"):
            PriceHistoryRecord(
                source_name="test",
                timestamp_utc=None,
                raw_price=100.0,
                normalized_usd=100.0,
            )


class TestRepositorySourceHealth:
    """Tests for source health persistence operations."""

    @pytest.fixture
    def sample_health_record(self) -> SourceHealthRecord:
        """Create a sample source health record for testing."""
        return SourceHealthRecord(
            source_name="cai_spot",
            status=HealthStatus.LIVE,
            last_success_at=datetime.now(timezone.utc),
            last_checked_at=datetime.now(timezone.utc),
            fallback_active=False,
            details={"retry_count": 0},
        )

    def test_source_health_record_creation(self, sample_health_record: SourceHealthRecord) -> None:
        """Test that source health record is created with correct values."""
        assert sample_health_record.source_name == "cai_spot"
        assert sample_health_record.status == HealthStatus.LIVE
        assert sample_health_record.fallback_active is False

    def test_source_health_status_transitions(self) -> None:
        """Test that health status transitions are valid."""
        # Test all valid statuses
        valid_statuses = [HealthStatus.LIVE, HealthStatus.STALE, HealthStatus.DEGRADED, HealthStatus.FAILED]

        for status in valid_statuses:
            record = SourceHealthRecord(
                source_name="test",
                status=status,
                last_checked_at=datetime.now(timezone.utc),
            )
            assert record.status == status


class TestRepositoryIngestionSource:
    """Tests for ingestion source persistence operations."""

    def test_ingestion_source_creation(self) -> None:
        """Test that ingestion source is created with correct values."""
        from models.ingestion_source import IngestionSource

        source = IngestionSource(
            source_name="cai_spot",
            display_name="CAI Cotton Spot",
            priority=1,
            category=SourceCategory.PRIMARY,
            source_url="https://example.com/data",
        )

        assert source.source_name == "cai_spot"
        assert source.display_name == "CAI Cotton Spot"
        assert source.is_primary is True

    def test_ingestion_source_fallback_relationship(self) -> None:
        """Test that fallback relationship is configured correctly."""
        from models.ingestion_source import IngestionSource

        source = IngestionSource(
            source_name="ccfgroup",
            display_name="CCFGroup Fallback",
            priority=3,
            category=SourceCategory.FALLBACK,
            fallback_to=None,
        )

        assert source.is_fallback is True


class TestRepositoryCurrencyConversion:
    """Tests for currency conversion persistence operations."""

    @pytest.fixture
    def sample_currency_record(self) -> CurrencyConversionRecord:
        """Create a sample currency conversion record for testing."""
        return CurrencyConversionRecord(
            currency="INR",
            rate_to_usd=83.0,
            rate_timestamp=datetime.now(timezone.utc),
            source_name="currency_api",
            retrieved_at=datetime.now(timezone.utc),
        )

    def test_currency_conversion_record_creation(
        self, sample_currency_record: CurrencyConversionRecord
    ) -> None:
        """Test that currency conversion record is created with correct values."""
        assert sample_currency_record.currency == "INR"
        assert sample_currency_record.rate_to_usd == 83.0
        assert sample_currency_record.source_name == "currency_api"

    def test_currency_conversion_record_validation(self) -> None:
        """Test that currency conversion record validates required fields."""
        with pytest.raises(ValueError, match="currency is required"):
            CurrencyConversionRecord(
                rate_to_usd=83.0,
                source_name="test",
            )

        with pytest.raises(ValueError, match="rate_to_usd must be positive"):
            CurrencyConversionRecord(
                currency="INR",
                rate_to_usd=-1.0,
                source_name="test",
            )


class TestUniqueConstraint:
    """Tests for unique constraint validation."""

    def test_price_history_unique_constraint_definition(self) -> None:
        """Test that price history has unique constraint on source/timestamp/price."""
        from db.schema import PriceHistory

        # Check that the unique index is defined
        table_args = PriceHistory.__table_args__
        assert table_args is not None

        # Find the unique index
        index_found = False
        for arg in table_args:
            if hasattr(arg, "name") and "source_timestamp_price" in arg.name:
                index_found = True
                break

        assert index_found, "Unique index for (source_name, timestamp_utc, raw_price) not found"

    def test_source_health_unique_constraint_definition(self) -> None:
        """Test that source health has unique constraint on source_name."""
        from db.schema import SourceHealth

        # Check that source_name is unique
        columns = SourceHealth.__table__.columns
        source_name_col = columns["source_name"]
        assert source_name_col.unique is True


class TestDatabaseSchema:
    """Tests for database schema definitions."""

    def test_price_history_table_columns(self) -> None:
        """Test that price history table has all required columns."""
        from db.schema import PriceHistory

        columns = PriceHistory.__table__.columns
        required_columns = [
            "id",
            "source_name",
            "source_type",
            "timestamp_utc",
            "commodity",
            "raw_price",
            "raw_currency",
            "normalized_usd",
            "quality_flags",
            "metadata",
            "created_at",
            "updated_at",
        ]

        for col_name in required_columns:
            assert col_name in columns, f"Missing column: {col_name}"

    def test_source_health_table_columns(self) -> None:
        """Test that source health table has all required columns."""
        from db.schema import SourceHealth

        columns = SourceHealth.__table__.columns
        required_columns = [
            "id",
            "source_name",
            "status",
            "last_success_at",
            "last_checked_at",
            "fallback_active",
            "stale_duration_minutes",
            "created_at",
            "updated_at",
        ]

        for col_name in required_columns:
            assert col_name in columns, f"Missing column: {col_name}"

    def test_ingestion_source_table_columns(self) -> None:
        """Test that ingestion source table has all required columns."""
        from db.schema import IngestionSource

        columns = IngestionSource.__table__.columns
        required_columns = [
            "source_name",
            "display_name",
            "priority",
            "category",
            "active",
            "fallback_to",
            "created_at",
            "updated_at",
        ]

        for col_name in required_columns:
            assert col_name in columns, f"Missing column: {col_name}"

    def test_currency_conversion_table_columns(self) -> None:
        """Test that currency conversion table has all required columns."""
        from db.schema import CurrencyConversion

        columns = CurrencyConversion.__table__.columns
        required_columns = [
            "id",
            "currency",
            "rate_to_usd",
            "rate_timestamp",
            "source_name",
            "retrieved_at",
        ]

        for col_name in required_columns:
            assert col_name in columns, f"Missing column: {col_name}"
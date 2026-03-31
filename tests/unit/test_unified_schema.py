"""Unit tests for unified schema consistency in Phase 2.

Validates that normalized records from freight and macro sources conform
to a unified structural contract.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from agents.normalizer import Normalizer
from models.freight_rate import FreightRate
from models.macro_feed_record import MacroFeedRecord
from models.price_history import PriceHistoryRecord


class TestUnifiedSchema:
    """Tests for schema consistency across different record types."""

    @pytest.fixture
    def normalizer(self) -> Normalizer:
        """Create a normalizer with mocked currency conversion."""
        from utils.usd_converter import USDConverter
        converter = MagicMock(spec=USDConverter)
        converter.convert_to_usd.return_value = (100.0, 1.0)
        return Normalizer(converter=converter)

    def test_freight_macro_unified_fields(self, normalizer: Normalizer) -> None:
        """Verify that freight and macro records share essential common fields."""
        freight_payload = {
            "source_name": "ccfi_med",
            "route": "Mediterranean",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "raw_price": 1150.5,
            "raw_currency": "USD",
        }
        macro_payload = {
            "source_name": "oil_spot",
            "commodity": "brent_oil",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "raw_price": 78.45,
            "raw_currency": "USD",
        }

        freight_record = normalizer.normalize_freight(freight_payload)
        macro_record = normalizer.normalize_macro(macro_payload)

        # Common fields that must exist in both for unified querying
        common_fields = [
            "source_name",
            "timestamp_utc",
            "normalized_usd",
            "conversion_rate",
            "quality_flags",
            "metadata",
        ]

        for field in common_fields:
            assert hasattr(freight_record, field), f"FreightRate missing field: {field}"
            assert hasattr(macro_record, field), f"MacroFeedRecord missing field: {field}"

        # Verify quality_flags structure
        for record in [freight_record, macro_record]:
            assert "stale" in record.quality_flags
            assert "fallback" in record.quality_flags

    def test_macro_record_matches_price_history_contract(self, normalizer: Normalizer) -> None:
        """Verify that MacroFeedRecord can be treated as a price history record."""
        macro_payload = {
            "source_name": "fx_usd_inr",
            "commodity": "usd_inr",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "raw_price": 83.15,
            "raw_currency": "INR",
        }

        record = normalizer.normalize_macro(macro_payload)
        
        # Macro records should have a source_type attribute set to SourceType.MACRO
        # if they are to be stored in price_history table or similar unified view
        assert hasattr(record, "source_type")
        from models.price_history import SourceType
        assert record.source_type == SourceType.MACRO

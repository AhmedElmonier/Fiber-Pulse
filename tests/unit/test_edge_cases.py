"""Unit tests for edge cases in Phase 2 ingestion and normalization.

Validates robust handling of partial data, out-of-order timestamps,
currency mismatches, and null/missing values.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from agents.normalizer import Normalizer, NormalizerError
from models.price_history import SourceType


class TestNormalizationEdgeCases:
    """Tests for edge cases in data normalization."""

    @pytest.fixture
    def normalizer(self) -> Normalizer:
        """Create a normalizer with mocked currency conversion."""
        from utils.usd_converter import USDConverter
        converter = MagicMock(spec=USDConverter)
        # Mock convert_to_usd to succeed for 'USD' and fail for 'XYZ'
        def mock_convert(amount, currency):
            if currency == "USD":
                return float(amount), 1.0
            raise ValueError(f"No rate for {currency}")
            
        converter.convert_to_usd.side_effect = mock_convert
        return Normalizer(converter=converter)

    def test_normalize_macro_missing_commodity(self, normalizer: Normalizer) -> None:
        """Test that missing 'commodity' in macro payload raises NormalizerError."""
        payload = {
            "source_name": "fx_usd_inr",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "raw_price": 83.15,
            "raw_currency": "USD",
        }
        with pytest.raises(NormalizerError, match="Missing required field: commodity"):
            normalizer.normalize_macro(payload)

    def test_normalize_freight_unsupported_currency(self, normalizer: Normalizer) -> None:
        """Test that unsupported currency raises NormalizerError."""
        payload = {
            "source_name": "ccfi_med",
            "route": "Mediterranean",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "raw_price": 1150.5,
            "raw_currency": "XYZ", # Unsupported
        }
        with pytest.raises(NormalizerError, match="Currency conversion failed"):
            normalizer.normalize_freight(payload)

    def test_normalize_out_of_order_timestamps(self, normalizer: Normalizer) -> None:
        """Test that normalization works regardless of timestamp relative to 'now'."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        payload = {
            "source_name": "oil_spot",
            "commodity": "brent_oil",
            "timestamp_utc": future_time.isoformat(),
            "raw_price": 78.45,
            "raw_currency": "USD",
        }
        # Normalizer should process future timestamps without error (ingestion allows historical/future data)
        record = normalizer.normalize_macro(payload)
        assert record.timestamp_utc.replace(microsecond=0) == future_time.replace(microsecond=0)

    def test_normalize_null_metadata(self, normalizer: Normalizer) -> None:
        """Test that null or missing metadata is handled gracefully."""
        payload = {
            "source_name": "oil_spot",
            "commodity": "brent_oil",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "raw_price": 78.45,
            "raw_currency": "USD",
            "metadata": None
        }
        record = normalizer.normalize_macro(payload)
        assert record.metadata["raw_payload"]["metadata"] is None
        assert "extraction_context" not in record.metadata

    def test_normalize_negative_price(self, normalizer: Normalizer) -> None:
        """Test that negative prices are caught in validation."""
        payload = {
            "source_name": "oil_spot",
            "commodity": "brent_oil",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "raw_price": -10.0, # Negative
            "raw_currency": "USD",
        }
        with pytest.raises(NormalizerError, match="non-negative"):
            normalizer.normalize_macro(payload)

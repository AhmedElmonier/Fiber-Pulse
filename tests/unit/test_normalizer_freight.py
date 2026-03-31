"""Unit tests for freight and macro normalization in Phase 2.

Validates route extraction, currency conversion, and quality flag assignment
for CCFI, Drewry, and macro payloads.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from agents.normalizer import Normalizer, NormalizerError
from models.freight_rate import FreightRate
from models.macro_feed_record import MacroFeedRecord
from utils.usd_converter import USDConverter


class TestNormalizerFreight:
    """Tests for normalize_freight() and normalize_macro() methods."""

    @pytest.fixture
    def normalizer(self) -> Normalizer:
        """Create a normalizer with mocked currency conversion."""
        converter = MagicMock(spec=USDConverter)
        # Mock convert_to_usd to return (normalized_amount, rate)
        # For simplicity, we'll return same amount and rate 1.0 for USD, 
        # and some fixed rate for others.
        def mock_convert(amount, currency):
            if currency == "USD":
                return float(amount), 1.0
            if currency == "INR":
                return float(amount) / 83.0, 83.0
            if currency == "CNY":
                return float(amount) / 7.2, 7.2
            return float(amount), 1.0
            
        converter.convert_to_usd.side_effect = mock_convert
        return Normalizer(converter=converter)

    def test_normalize_freight_ccfi_success(self, normalizer: Normalizer) -> None:
        """Test successful normalization of CCFI freight payload."""
        payload = {
            "source_name": "ccfi_med",
            "route": "Mediterranean",
            "timestamp_utc": "2024-05-20T10:00:00Z",
            "raw_price": 1150.5,
            "raw_currency": "USD",
            "metadata": {"original_route": "Med Service"}
        }

        record = normalizer.normalize_freight(payload)

        assert isinstance(record, FreightRate)
        assert record.source_name == "ccfi_med"
        assert record.route == "Mediterranean"
        assert record.raw_price == 1150.5
        assert record.raw_currency == "USD"
        assert record.normalized_usd == 1150.5
        assert record.conversion_rate == 1.0
        assert record.timestamp_utc == datetime(2024, 5, 20, 10, 0, tzinfo=timezone.utc)
        assert record.quality_flags["stale"] is False
        assert record.metadata["raw_payload"] == payload

    def test_normalize_freight_drewry_success(self, normalizer: Normalizer) -> None:
        """Test successful normalization of Drewry freight payload."""
        payload = {
            "source_name": "drewry_wci",
            "route": "Shanghai-Rotterdam",
            "timestamp_utc": "2024-05-20T12:00:00+00:00",
            "raw_price": 3500.0,
            "raw_currency": "USD",
        }

        record = normalizer.normalize_freight(payload)

        assert record.source_name == "drewry_wci"
        assert record.route == "Shanghai-Rotterdam"
        assert record.normalized_usd == 3500.0

    def test_normalize_freight_missing_fields(self, normalizer: Normalizer) -> None:
        """Test that missing required fields raise NormalizerError."""
        payload = {
            "source_name": "ccfi_med",
            # missing route
            "timestamp_utc": "2024-05-20T10:00:00Z",
            "raw_price": 1150.5,
            "raw_currency": "USD",
        }

        with pytest.raises(NormalizerError) as excinfo:
            normalizer.normalize_freight(payload)
        
        assert "Missing required field: route" in str(excinfo.value)

    def test_normalize_macro_fx_success(self, normalizer: Normalizer) -> None:
        """Test successful normalization of FX macro payload."""
        payload = {
            "source_name": "fx_usd_inr",
            "commodity": "usd_inr",
            "timestamp_utc": "2024-05-20T10:00:00Z",
            "raw_price": 83.15,
            "raw_currency": "INR",
        }

        record = normalizer.normalize_macro(payload)

        assert isinstance(record, MacroFeedRecord)
        assert record.source_name == "fx_usd_inr"
        assert record.commodity == "usd_inr"
        assert record.raw_price == 83.15
        assert record.raw_currency == "INR"
        # 83.15 / 83.0 = 1.0018...
        assert abs(record.normalized_usd - 1.0018) < 0.0001
        assert record.conversion_rate == 83.0

    def test_normalize_macro_oil_success(self, normalizer: Normalizer) -> None:
        """Test successful normalization of oil spot macro payload."""
        payload = {
            "source_name": "oil_spot",
            "commodity": "brent_oil",
            "timestamp_utc": "2024-05-20T10:00:00Z",
            "raw_price": 78.45,
            "raw_currency": "USD",
        }

        record = normalizer.normalize_macro(payload)

        assert record.source_name == "oil_spot"
        assert record.commodity == "brent_oil"
        assert record.normalized_usd == 78.45

    def test_normalize_with_quality_flags(self, normalizer: Normalizer) -> None:
        """Test that quality flags are correctly applied."""
        payload = {
            "source_name": "ccfi_med",
            "route": "Mediterranean",
            "timestamp_utc": "2024-05-20T10:00:00Z",
            "raw_price": 1150.5,
            "raw_currency": "USD",
        }
        flags = {"stale": True, "fallback": False}
        
        record = normalizer.normalize_freight(payload, quality_flags=flags)
        assert record.quality_flags["stale"] is True
        assert record.quality_flags["fallback"] is False

    def test_normalize_with_fallback_source(self, normalizer: Normalizer) -> None:
        """Test that fallback_source in payload sets fallback flag."""
        payload = {
            "source_name": "ccfi_med",
            "route": "Mediterranean",
            "timestamp_utc": "2024-05-20T10:00:00Z",
            "raw_price": 1150.5,
            "raw_currency": "USD",
            "fallback_source": "drewry_wci"
        }
        
        record = normalizer.normalize_freight(payload)
        assert record.quality_flags["fallback"] is True
        assert record.quality_flags["fallback_source"] == "drewry_wci"

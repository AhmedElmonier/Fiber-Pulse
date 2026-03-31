"""Shared fixtures for integration and unit tests."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.normalizer import Normalizer


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create a mock repository for testing."""
    repo = MagicMock()
    repo.insert_price_records_batch = AsyncMock(return_value=[])
    repo.get_price_records = AsyncMock(return_value=[])
    repo.get_source_health = AsyncMock(return_value=None)
    repo.get_ingestion_source = AsyncMock(return_value=None)
    repo.get_normalized_records = AsyncMock(return_value=[])
    repo.get_records_by_health_status = AsyncMock(return_value=[])
    repo.upsert_source_health = AsyncMock()
    repo.persist_freight_rate = AsyncMock()
    repo.persist_macro_feed = AsyncMock()
    repo.update_source_health = AsyncMock()
    repo.insert_price_record = AsyncMock()
    return repo


@pytest.fixture
def sample_payloads(ccfi_med_payload, drewry_wci_payload, fx_usd_inr_payload, oil_spot_payload, electricity_payload):
    """Aggregate of all sample payloads."""
    return [
        ccfi_med_payload,
        drewry_wci_payload,
        fx_usd_inr_payload,
        oil_spot_payload,
        electricity_payload
    ]


@pytest.fixture
def normalizer() -> Normalizer:
    """Create a normalizer with USD rates configured."""
    from utils.usd_converter import USDConverter

    converter = USDConverter()
    converter.set_rate("INR", 83.0)  # 1 USD = 83 INR
    converter.set_rate("CNY", 7.2)  # 1 USD = 7.2 CNY
    converter.set_rate("USD", 1.0)
    return Normalizer(converter=converter)


@pytest.fixture
def ccfi_med_payload():
    """Sample CCFI Mediterranean raw payload."""
    return {
        "source_name": "ccfi_med",
        "route": "Mediterranean",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "raw_price": 1150.5,
        "raw_currency": "USD",
        "metadata": {"original_route": "Mediterranean Service"}
    }


@pytest.fixture
def drewry_wci_payload():
    """Sample Drewry WCI raw payload."""
    return {
        "source_name": "drewry_wci",
        "route": "Shanghai-Rotterdam",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "raw_price": 3500.0,
        "raw_currency": "USD",
        "metadata": {"index_name": "WCI Shanghai to Rotterdam"}
    }


@pytest.fixture
def fx_usd_inr_payload():
    """Sample FX USD/INR raw payload."""
    return {
        "source_name": "fx_usd_inr",
        "commodity": "usd_inr",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "raw_price": 83.15,
        "raw_currency": "INR",
        "metadata": {"bank": "RBI"}
    }


@pytest.fixture
def oil_spot_payload():
    """Sample Brent Oil spot raw payload."""
    return {
        "source_name": "oil_spot",
        "commodity": "brent_oil",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "raw_price": 78.45,
        "raw_currency": "USD",
        "metadata": {"market": "ICE"}
    }


@pytest.fixture
def electricity_payload():
    """Sample electricity raw payload."""
    return {
        "source_name": "electricity",
        "commodity": "base_load",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "raw_price": 0.12,
        "raw_currency": "USD",
        "metadata": {"region": "US-TEXAS"}
    }

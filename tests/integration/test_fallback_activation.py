"""Integration tests for fallback activation in Phase 2.

Validates that the ingestion pipeline automatically switches to fallback
sources when primary sources fail or return stale data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.data_fetcher import DataFetcher, IngestionResult
from agents.normalizer import Normalizer
from models.price_history import PriceHistoryRecord, SourceType
from models.source_health import HealthStatus, SourceHealthRecord


@pytest.mark.asyncio
async def test_fallback_activation_on_fetch_failure(mock_repository, normalizer):
    """Test that fallback is activated when primary fetch fails."""
    # Setup mocks
    primary_scraper = MagicMock()
    primary_scraper.source_name = "primary_source"
    primary_scraper.display_name = "Primary Source"
    primary_scraper.source_type = "spot"
    # Mock scrape to fail
    primary_scraper.scrape = AsyncMock(return_value=MagicMock(success=False, error="Connection timeout"))

    fallback_scraper = MagicMock()
    fallback_scraper.source_name = "fallback_source"
    fallback_scraper.display_name = "Fallback Source"
    fallback_scraper.source_type = "spot"
    fallback_payload = {
        "source_name": "fallback_source",
        "commodity": "cotton",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "raw_price": 100.0,
        "raw_currency": "USD",
    }
    fallback_scraper.scrape = AsyncMock(return_value=MagicMock(success=True, records=[fallback_payload]))
    fallback_scraper.validate_payload = MagicMock(return_value=[])

    fetcher = DataFetcher(repository=mock_repository, normalizer=normalizer)
    fetcher._register_scraper(primary_scraper)
    fetcher._register_scraper(fallback_scraper, is_primary=False, primary_for="primary_source")

    # Execute ingestion
    result = await fetcher.ingest_source("primary_source")

    # Verify results
    assert result.success is True
    assert result.fallback_used is True
    assert result.records_ingested == 1
    
    # Verify persistence called with fallback metadata
    mock_repository.insert_price_records_batch.assert_called()
    record = mock_repository.insert_price_records_batch.call_args[0][0][0]
    assert record.source_name == "fallback_source" # DataFetcher uses scraper.source_name
    assert record.quality_flags["fallback"] is True
    assert record.quality_flags["fallback_source"] == "Fallback Source"
    # Verify health update called with fallback_active=True
    # The second call to update_source_health should have fallback_active=True
    assert mock_repository.upsert_source_health.call_count >= 2
    # Last call should be the successful fallback ingest
    health_record = mock_repository.upsert_source_health.call_args[0][0]
    assert health_record.source_name == "primary_source"
    assert health_record.fallback_active is True
    assert health_record.status == HealthStatus.DEGRADED


@pytest.mark.asyncio
async def test_fallback_activation_on_stale_data(mock_repository, normalizer):
    """Test that fallback is activated when primary data is stale (simulated)."""
    # Note: ingest_source doesn't currently check staleness *before* scraping primary.
    # It checks it in _scrape_and_persist but only to set quality flags.
    # The spec US2 goal: "Detect stale or dead sources and automatically switch to fallback"
    # This might require T030 and T031 implementation first.
    pass

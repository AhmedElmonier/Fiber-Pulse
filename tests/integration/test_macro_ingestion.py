"""Integration tests for macro ingestion in Phase 2.

Validates end-to-end ingestion of FX, oil, and electricity macro feeds.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.data_fetcher import DataFetcher
from models.macro_feed_record import MacroFeedRecord


@pytest.mark.asyncio
async def test_fx_usd_inr_ingestion(mock_repository, normalizer, fx_usd_inr_payload):
    """Test that FX USD/INR macro feed is ingested and persisted."""
    from agents.macro_feed_scraper import MacroFeedScraper
    
    with patch.object(MacroFeedScraper, "scrape", new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = MagicMock(
            success=True,
            records=[fx_usd_inr_payload],
            source_name="fx_usd_inr"
        )
        
        fetcher = DataFetcher(repository=mock_repository, normalizer=normalizer)
        result = await fetcher.ingest_source("fx_usd_inr")
        
        assert result.success is True
        assert result.records_ingested == 1
        
        mock_repository.persist_macro_feed.assert_called()
        record = mock_repository.persist_macro_feed.call_args[0][0]
        assert isinstance(record, MacroFeedRecord)
        assert record.source_name == "fx_usd_inr"
        assert record.commodity == "usd_inr"


@pytest.mark.asyncio
async def test_oil_spot_ingestion(mock_repository, normalizer, oil_spot_payload):
    """Test that oil spot macro feed is ingested and persisted."""
    from agents.macro_feed_scraper import MacroFeedScraper
    
    with patch.object(MacroFeedScraper, "scrape", new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = MagicMock(
            success=True,
            records=[oil_spot_payload],
            source_name="oil_spot"
        )
        
        fetcher = DataFetcher(repository=mock_repository, normalizer=normalizer)
        result = await fetcher.ingest_source("oil_spot")
        
        assert result.success is True
        assert result.records_ingested == 1
        
        mock_repository.persist_macro_feed.assert_called()
        record = mock_repository.persist_macro_feed.call_args[0][0]
        assert record.source_name == "oil_spot"
        assert record.commodity == "brent_oil"


@pytest.mark.asyncio
async def test_electricity_ingestion(mock_repository, normalizer, electricity_payload):
    """Test that electricity macro feed is ingested and persisted."""
    from agents.macro_feed_scraper import MacroFeedScraper
    
    with patch.object(MacroFeedScraper, "scrape", new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = MagicMock(
            success=True,
            records=[electricity_payload],
            source_name="electricity"
        )
        
        fetcher = DataFetcher(repository=mock_repository, normalizer=normalizer)
        result = await fetcher.ingest_source("electricity")
        
        assert result.success is True
        assert result.records_ingested == 1
        
        mock_repository.persist_macro_feed.assert_called()
        record = mock_repository.persist_macro_feed.call_args[0][0]
        assert record.source_name == "electricity"
        assert record.commodity == "base_load"

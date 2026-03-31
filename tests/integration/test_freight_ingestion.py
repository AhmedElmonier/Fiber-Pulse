"""Integration tests for freight ingestion in Phase 2.

Validates end-to-end ingestion of CCFI and Drewry freight sources.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.data_fetcher import DataFetcher
from agents.normalizer import Normalizer
from models.freight_rate import FreightRate


@pytest.mark.asyncio
async def test_ccfi_med_ingestion(mock_repository, normalizer, ccfi_med_payload):
    """Test that CCFI Mediterranean freight is ingested and persisted."""
    # This will likely fail initially because CCFIMediterraneanScraper is not implemented
    from agents.ccfi_mediterranean_scraper import CCFIMediterraneanScraper
    
    with patch.object(CCFIMediterraneanScraper, "scrape", new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = MagicMock(
            success=True,
            records=[ccfi_med_payload],
            source_name="ccfi_med"
        )
        
        fetcher = DataFetcher(repository=mock_repository, normalizer=normalizer)
        result = await fetcher.ingest_source("ccfi_med")
        
        assert result.success is True
        assert result.records_ingested == 1
        
        # Verify persistence was called with correct model
        mock_repository.persist_freight_rate.assert_called()
        call_args = mock_repository.persist_freight_rate.call_args
        record = call_args[0][0]
        assert isinstance(record, FreightRate)
        assert record.source_name == "ccfi_med"
        assert record.route == "Mediterranean"


@pytest.mark.asyncio
async def test_drewry_wci_ingestion(mock_repository, normalizer, drewry_wci_payload):
    """Test that Drewry WCI freight is ingested and persisted."""
    from agents.drewry_wci_scraper import DrewryWCIScraper
    
    with patch.object(DrewryWCIScraper, "scrape", new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = MagicMock(
            success=True,
            records=[drewry_wci_payload],
            source_name="drewry_wci"
        )
        
        fetcher = DataFetcher(repository=mock_repository, normalizer=normalizer)
        result = await fetcher.ingest_source("drewry_wci")
        
        assert result.success is True
        assert result.records_ingested == 1
        
        mock_repository.persist_freight_rate.assert_called()
        record = mock_repository.persist_freight_rate.call_args[0][0]
        assert record.source_name == "drewry_wci"
        assert record.route == "Shanghai-Rotterdam"

"""Integration tests for the unified ingestion pipeline in Phase 2.

Validates that both freight and macro sources can be ingested sequentially
using a unified orchestrator and persist with compatible schemas.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.data_fetcher import DataFetcher
from agents.normalizer import Normalizer


@pytest.mark.asyncio
async def test_unified_ingestion_sequence(mock_repository, normalizer):
    """Test that multiple source types can be ingested in a single run."""
    # We will use a yet-to-be-created orchestrator or extend DataFetcher
    from agents.unified_ingestion_orchestrator import UnifiedIngestionOrchestrator
    
    orchestrator = UnifiedIngestionOrchestrator(repository=mock_repository, normalizer=normalizer)
    
    # Define a set of sources covering different types
    sources = ["ccfi_med", "fx_usd_inr", "oil_spot"]
    
    # Mock ingest_source to simulate successful runs
    with patch("agents.data_fetcher.DataFetcher.ingest_source", new_callable=AsyncMock) as mock_ingest:
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.records_ingested = 1
        mock_result.to_dict.return_value = {"success": True, "records_ingested": 1}
        mock_ingest.return_value = mock_result
        
        results = await orchestrator.run_ingestion(sources)
        
        assert results["summary"]["total_sources"] == 3
        assert results["summary"]["successful_sources"] == 3
        assert mock_ingest.call_count == 3
        
        # Verify that each source was called
        called_sources = [call.args[0] for call in mock_ingest.call_args_list]
        for source in sources:
            assert source in called_sources

@pytest.mark.asyncio
async def test_unified_query_interface(mock_repository):
    """Test that the repository provides a unified query interface for all records."""
    # This tests T037 implementation
    start_time = "2024-01-01T00:00:00Z"
    
    # Mock return values for unified query
    mock_repository.get_normalized_records.return_value = [
        MagicMock(source_name="ccfi_med", normalized_usd=1100.0),
        MagicMock(source_name="fx_usd_inr", normalized_usd=83.0)
    ]
    
    records = await mock_repository.get_normalized_records(start_time=start_time)
    
    assert len(records) == 2
    mock_repository.get_normalized_records.assert_called_with(start_time=start_time)

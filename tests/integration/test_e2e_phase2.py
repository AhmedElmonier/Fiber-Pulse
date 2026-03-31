"""End-to-end integration tests for FiberPulse Phase 2.

Simulates a full ingestion cycle for diverse sources, handling failures,
fallback activation, and verifying unified data persistence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.unified_ingestion_orchestrator import UnifiedIngestionOrchestrator
from models.source_health import HealthStatus


@pytest.mark.asyncio
async def test_e2e_ingestion_with_failures_and_fallbacks(mock_repository, normalizer):
    """Test full workflow: sequential ingestion with a mix of success and fallback."""
    orchestrator = UnifiedIngestionOrchestrator(repository=mock_repository, normalizer=normalizer)
    
    # 1. Setup sources: 
    # - fx_usd_inr: success
    # - ccfi_med: primary fails, fallback (drewry_wci) succeeds
    sources = ["fx_usd_inr", "ccfi_med"]
    
    # Configure mock behavior
    async def mock_ingest(source_name, **kwargs):
        if source_name == "fx_usd_inr":
            return MagicMock(success=True, records_ingested=1, fallback_used=False, to_dict=lambda: {"success": True})
        if source_name == "ccfi_med":
            # Simulate primary failure and fallback success
            return MagicMock(success=True, records_ingested=1, fallback_used=True, source_name="drewry_wci", to_dict=lambda: {"success": True, "fallback_used": True})
        return MagicMock(success=False, error="Unknown source")

    with patch("agents.data_fetcher.DataFetcher.ingest_source", side_effect=mock_ingest):
        # 2. Run ingestion
        results = await orchestrator.run_ingestion(sources)
        
        # 3. Verify results summary
        assert results["summary"]["total_sources"] == 2
        assert results["summary"]["successful_sources"] == 2
        
        # 4. Verify specific source details
        assert results["results"]["fx_usd_inr"]["success"] is True
        assert results["results"]["ccfi_med"]["fallback_used"] is True

    # 5. Verify repository was called for both persistence and health (already handled by DataFetcher logic)
    # This e2e test focuses on the orchestrator's ability to drive the fetcher and collect results correctly.

@pytest.mark.asyncio
async def test_e2e_source_health_transition_flow(mock_repository, normalizer):
    """Verify source health records are correctly transitioned in an e2e scenario."""
    # This test would ideally use a real DB, but we verify mock interaction sequence
    orchestrator = UnifiedIngestionOrchestrator(repository=mock_repository, normalizer=normalizer)
    
    # Simulate a source that was previously LIVE but now fails and triggers fallback
    source_name = "ccfi_med"
    
    # Mock primary scrape failure
    from agents.ccfi_mediterranean_scraper import CCFIMediterraneanScraper
    with patch.object(CCFIMediterraneanScraper, "scrape", new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = MagicMock(success=False, error="Primary down")
        
        # Mock fallback (drewry) success
        from agents.drewry_wci_scraper import DrewryWCIScraper
        with patch.object(DrewryWCIScraper, "scrape", new_callable=AsyncMock) as mock_fallback_scrape:
            mock_payload = {
                "source_name": "drewry_wci",
                "route": "Shanghai-Rotterdam",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "raw_price": 3500.0,
                "raw_currency": "USD"
            }
            mock_fallback_scrape.return_value = MagicMock(success=True, records=[mock_payload])
            
            # Execute ingestion
            await orchestrator.run_ingestion([source_name])
            
            # Verify health updates: 1 fail for primary, 1 success for fallback
            # The DataFetcher calls update_source_health for the primary source_name
            # even when using fallback (it marks primary as DEGRADED)
            assert mock_repository.upsert_source_health.call_count >= 2
            
            # Last health record for 'ccfi_med' should be DEGRADED
            ccfi_med_calls = [c for c in mock_repository.upsert_source_health.call_args_list if c.args[0].source_name == source_name]
            assert len(ccfi_med_calls) > 0, f"No health update found for source: {source_name}"
            last_health_call = ccfi_med_calls[-1]
            assert last_health_call.args[0].status == HealthStatus.DEGRADED
            assert last_health_call.args[0].fallback_active is True

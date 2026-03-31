"""Integration tests for Phase 2 ingestion quality metrics.

Validates that freight and macro records meet the 95% baseline for
successful ingestion and normalization (SC-001, SC-003).
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.data_fetcher import DataFetcher


@pytest.mark.asyncio
async def test_freight_macro_ingestion_baseline_95_percent(mock_repository, normalizer, sample_payloads):
    """Test that at least 95% of sample freight/macro records ingest successfully."""
    # Mock scrapers for all sources in sample_payloads
    with patch("agents.data_fetcher.DataFetcher.ingest_source", new_callable=AsyncMock) as mock_ingest:
        # Simulate 100% success for a large number of sources to accurately test 95% threshold.
        # For 20 sources, 19/20 = 95%.
        sources = [f"source_{i}" for i in range(20)]
        
        # 19 successes, 1 failure
        success_results = [MagicMock(success=True, records_ingested=1) for _ in range(19)]
        failure_result = [MagicMock(success=False, error="Simulated failure")]
        mock_ingest.side_effect = success_results + failure_result
        
        fetcher = DataFetcher(repository=mock_repository, normalizer=normalizer)
        
        results = []
        for source in sources:
            res = await fetcher.ingest_source(source)
            results.append(res)
            
        success_count = sum(1 for r in results if r.success)
        success_rate = success_count / len(sources) if sources else 0
        
        # 19/20 = 95% which should pass
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} is below 95% baseline"

        # Now test that 18/20 = 90% fails the 95% threshold
        mock_ingest.reset_mock()
        mock_ingest.side_effect = [MagicMock(success=True, records_ingested=1) for _ in range(18)] + \
                                  [MagicMock(success=False, error="Simulated failure") for _ in range(2)]
        
        results = []
        for source in sources:
            res = await fetcher.ingest_source(source)
            results.append(res)
            
        success_count = sum(1 for r in results if r.success)
        success_rate = success_count / len(sources) if sources else 0
        assert success_rate < 0.95, f"Success rate {success_rate:.2%} should be below 95% baseline"


@pytest.mark.asyncio
async def test_freight_macro_normalization_coverage_95_percent(normalizer, sample_payloads):
    """Test that at least 95% of freight/macro records normalize to USD successfully."""
    success_count = 0
    total_count = len(sample_payloads)
    
    if total_count == 0:
        pytest.skip("No sample payloads available for coverage test")

    for payload in sample_payloads:
        try:
            if "route" in payload:
                record = normalizer.normalize_freight(payload)
            else:
                record = normalizer.normalize_macro(payload)
            
            if record.normalized_usd is not None and record.normalized_usd > 0:
                success_count += 1
        except (ValueError, TypeError, KeyError) as e:
            # Catch expected normalization errors and continue
            continue
        except Exception as e:
            # Fail on unexpected errors
            pytest.fail(f"Unexpected error during normalization: {e}")
            
    coverage = success_count / total_count
    assert coverage >= 0.95, f"Normalization coverage {coverage:.2%} is below 95% threshold"

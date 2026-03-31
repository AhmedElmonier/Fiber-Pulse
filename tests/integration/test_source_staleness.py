"""Integration tests for source staleness in Phase 2.

Validates that sources are marked as stale or failed based on 
ingestion outcomes and thresholds.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.data_fetcher import DataFetcher
from agents.source_health import DEFAULT_STALE_THRESHOLD_MINUTES, SourceHealthEvaluator
from models.source_health import HealthStatus, SourceHealthRecord


@pytest.mark.asyncio
async def test_stale_detection_after_48_hours(mock_repository, normalizer):
    """Test that source is marked stale after 48 hours without success."""
    source_name = "cai_spot"
    # Mock current health as live with old success
    old_success = datetime.now(timezone.utc) - timedelta(minutes=DEFAULT_STALE_THRESHOLD_MINUTES + 1)
    
    mock_repository.get_source_health = AsyncMock(return_value=SourceHealthRecord(
        source_name=source_name,
        status=HealthStatus.LIVE,
        last_success_at=old_success,
        last_checked_at=datetime.now(timezone.utc) - timedelta(minutes=60),
    ))
    
    # Mock primary scrape failure
    fetcher = DataFetcher(repository=mock_repository, normalizer=normalizer)
    fetcher.primary_scrapers[source_name].scrape = AsyncMock(return_value=MagicMock(success=False, error="Stale data detection"))
    
    # Execute ingestion without fallback
    await fetcher.ingest_source(source_name, use_fallback=False)
    
    # Verify health updated to STALE
    mock_repository.upsert_source_health.assert_called()
    record = mock_repository.upsert_source_health.call_args[0][0]
    assert record.status == HealthStatus.STALE
    assert record.stale_duration_minutes >= DEFAULT_STALE_THRESHOLD_MINUTES

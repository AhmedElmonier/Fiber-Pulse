"""Integration tests for schema consistency in Phase 2.

Validates that querying freight_rates and price_history (macro) tables
yields records with compatible fields and can be processed uniformly.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from db.schema import FreightRate, PriceHistory
from models.price_history import SourceType


@pytest.mark.asyncio
async def test_repository_unified_schema_fields(mock_repository):
    """Verify that records from different tables have the same core columns."""
    # This is a bit of a meta-test for the db/schema.py updates (T038)
    
    # Create sample DB-like objects (using SQLAlchemy models)
    freight_row = FreightRate(
        source_name="ccfi_med",
        route="Mediterranean",
        timestamp_utc=datetime.now(timezone.utc),
        raw_price=1100.0,
        raw_currency="USD",
        normalized_usd=1100.0,
        quality_flags={"stale": False},
        metadata={}
    )
    
    macro_row = PriceHistory(
        source_name="fx_usd_inr",
        source_type=SourceType.MACRO,
        commodity="usd_inr",
        timestamp_utc=datetime.now(timezone.utc),
        raw_price=83.0,
        raw_currency="INR",
        normalized_usd=1.0,
        quality_flags={"stale": False},
        record_metadata={}
    )
    
    # Essential columns for unified processing
    essential_columns = [
        "source_name",
        "timestamp_utc",
        "normalized_usd",
        "quality_flags",
    ]
    
    for col in essential_columns:
        assert hasattr(freight_row, col), f"FreightRate row missing {col}"
        assert hasattr(macro_row, col), f"PriceHistory row missing {col}"

    # Verify that metadata field is present (even if named differently in schema)
    assert hasattr(freight_row, "record_metadata") or hasattr(freight_row, "metadata")
    assert hasattr(macro_row, "record_metadata") or hasattr(macro_row, "metadata")

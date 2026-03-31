"""Performance benchmarks for Phase 2 ingestion.

Validates that normalization and processing of bulk records meets
performance requirements.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from agents.normalizer import Normalizer


def test_normalization_performance_bulk():
    """Benchmark normalization speed for 1000 records."""
    from utils.usd_converter import USDConverter
    converter = MagicMock(spec=USDConverter)
    converter.convert_to_usd.return_value = (100.0, 1.0)
    normalizer = Normalizer(converter=converter)
    
    payloads = []
    for i in range(1000):
        payloads.append({
            "source_name": "ccfi_med",
            "route": f"Route_{i}",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "raw_price": 1000.0 + i,
            "raw_currency": "USD",
        })
        
    start_time = time.perf_counter()
    for p in payloads:
        normalizer.normalize_freight(p)
    end_time = time.perf_counter()
    
    duration = end_time - start_time
    avg_per_record = duration / 1000
    
    print(f"\nBulk Normalization (1000 records): {duration:.4f}s total ({avg_per_record:.6f}s/record)")
    
    # Requirement: Ingestion and normalization should be efficient.
    # Typically < 1ms per record for local CPU processing.
    assert avg_per_record < 0.005 # 5ms limit per record

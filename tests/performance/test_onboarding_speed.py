"""Performance test for historical data onboarding (SC-004).

Validates that the system can ingest 1,000+ records in under 60 seconds.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

from agents.historical_onboarding import (
    parse_csv_rows,
    validate_csv_row,
)


def generate_test_csv(num_records: int) -> str:
    """Generate a test CSV with specified number of records."""
    lines = ["date,source,price,currency"]

    import random

    random.seed(42)

    base_date = datetime(2023, 1, 1, tzinfo=UTC)
    sources = ["cai_spot", "mcx_futures", "ccfi_med"]
    currencies = ["USD", "INR", "EUR"]

    for i in range(num_records):
        date = base_date.replace(day=((i % 30) + 1))
        source = sources[i % len(sources)]
        price = 80.0 + random.random() * 20
        currency = currencies[i % len(currencies)]
        lines.append(f"{date.isoformat()},{source},{price:.2f},{currency}")

    return "\n".join(lines)


def test_csv_parsing_performance_1000_records():
    """Test that CSV parsing for 1000 records completes quickly."""
    import io

    csv_content = generate_test_csv(1000)

    start_time = time.perf_counter()
    rows = parse_csv_rows(io.StringIO(csv_content))
    end_time = time.perf_counter()

    duration = end_time - start_time
    print(f"\nCSV parsing (1000 records): {duration:.4f}s")

    assert len(rows) == 1000
    assert duration < 10.0


def test_csv_validation_performance_1000_records():
    """Test that row validation for 1000 records completes quickly."""
    import io

    csv_content = generate_test_csv(1000)
    rows = parse_csv_rows(io.StringIO(csv_content))

    start_time = time.perf_counter()
    errors = []
    for row in rows:
        row_errors = validate_csv_row(row)
        errors.extend(row_errors)
    end_time = time.perf_counter()

    duration = end_time - start_time
    print(f"\nRow validation (1000 records): {duration:.4f}s")

    assert duration < 30.0


def test_ingestion_performance_1000_records():
    """Test that full ingestion of 1000 records meets SC-004 (< 60s).

    This tests the combined performance of parsing and validation
    for 1000 historical records.
    """
    import io

    csv_content = generate_test_csv(1000)

    start_time = time.perf_counter()

    rows = parse_csv_rows(io.StringIO(csv_content))
    errors = []
    validated_records = []
    for row in rows:
        row_errors = validate_csv_row(row)
        if not row_errors:
            validated_records.append(row)
        errors.extend(row_errors)

    end_time = time.perf_counter()

    duration = end_time - start_time
    records_per_second = len(validated_records) / duration if duration > 0 else 0

    print(f"\nFull pipeline (1000 records): {duration:.4f}s")
    print(f"Throughput: {records_per_second:.2f} records/second")
    print(f"Valid records: {len(validated_records)}/{len(rows)}")
    print(f"Validation errors: {len(errors)}")

    assert duration < 60.0, f"Ingestion took {duration:.2f}s, exceeds 60s limit"
    assert len(validated_records) >= 900, f"Expected >900 valid, got {len(validated_records)}"

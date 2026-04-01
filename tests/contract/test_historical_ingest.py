"""Contract tests for historical CSV ingestion format.

Validates that CSV rows conform to the historical-ingest.json contract:
- Required columns: date, source, price, currency
- ISO-8601 date format
- Positive price values
- 3-letter currency codes
"""

from __future__ import annotations

import io

import pytest

from agents.historical_onboarding import (
    CsvParseError,
    parse_csv_rows,
    validate_csv_row,
)

# Contract spec: required columns
REQUIRED_COLUMNS = {"date", "source", "price", "currency"}


class TestHistoricalIngestContract:
    """Validate CSV ingestion against historical-ingest.json contract."""

    def test_required_columns_present(self):
        """Contract: CSV must contain date, source, price, currency columns."""
        header = ["date", "source", "price", "currency"]
        for col in REQUIRED_COLUMNS:
            assert col in header, f"Missing required column: {col}"

    def test_missing_required_column_raises(self):
        """Contract: Missing required column must raise CsvParseError."""
        csv_text = "date,source,price\n2023-01-01,cai_spot,100.0"
        with pytest.raises(CsvParseError, match="Missing required column"):
            parse_csv_rows(io.StringIO(csv_text))

    def test_valid_row_accepted(self):
        """Contract: Valid row with ISO-8601 date, positive price, 3-letter currency."""
        csv_text = "date,source,price,currency\n2023-01-01T00:00:00Z,cai_spot,85.50,USD"
        rows = parse_csv_rows(io.StringIO(csv_text))
        assert len(rows) == 1
        assert rows[0]["source"] == "cai_spot"
        assert float(rows[0]["price"]) == 85.50

    def test_iso8601_date_parsing(self):
        """Contract: date must be ISO-8601 string."""
        valid_dates = [
            "2023-01-01",
            "2023-01-01T00:00:00Z",
            "2023-06-15T12:30:00+00:00",
        ]
        for d in valid_dates:
            csv_text = f"date,source,price,currency\n{d},cai_spot,100.0,USD"
            rows = parse_csv_rows(io.StringIO(csv_text))
            assert len(rows) == 1
            errors = validate_csv_row(rows[0])
            assert not errors, f"Unexpected errors for date '{d}': {errors}"

    @pytest.mark.parametrize("bad_date", ["not-a-date", "01-01-2023", ""])
    def test_invalid_date_rejected(self, bad_date):
        """Contract: Non-ISO-8601 date must be caught."""
        csv_text = f"date,source,price,currency\n{bad_date},cai_spot,100.0,USD"
        rows = parse_csv_rows(io.StringIO(csv_text))
        assert len(rows) == 1
        errors = validate_csv_row(rows[0])
        assert any("date" in e.lower() for e in errors), f"Expected date error for '{bad_date}'"

    @pytest.mark.parametrize("bad_price", ["-1", "0", "abc", ""])
    def test_non_positive_price_rejected(self, bad_price):
        """Contract: positive_price must be enforced."""
        csv_text = f"date,source,price,currency\n2023-01-01,cai_spot,{bad_price},USD"
        rows = parse_csv_rows(io.StringIO(csv_text))
        assert len(rows) == 1
        errors = validate_csv_row(rows[0])
        assert any("price" in e.lower() for e in errors), f"Expected price error for '{bad_price}'"

    @pytest.mark.parametrize("bad_currency", ["US", "USDX", "", "us"])
    def test_invalid_currency_rejected(self, bad_currency):
        """Contract: currency must be 3-letter code."""
        csv_text = f"date,source,price,currency\n2023-01-01,cai_spot,100.0,{bad_currency}"
        rows = parse_csv_rows(io.StringIO(csv_text))
        assert len(rows) == 1
        errors = validate_csv_row(rows[0])
        assert any("currency" in e.lower() for e in errors), (
            f"Expected currency error for '{bad_currency}'"
        )

    def test_empty_csv_raises(self):
        """Contract: Empty CSV must raise."""
        with pytest.raises(CsvParseError, match="empty"):
            parse_csv_rows(io.StringIO(""))

    def test_header_only_csv_raises(self):
        """Contract: Header-only CSV (no data rows) must raise."""
        with pytest.raises(CsvParseError, match="No data rows"):
            parse_csv_rows(io.StringIO("date,source,price,currency\n"))

    def test_multiple_valid_rows(self):
        """Contract: Multiple valid rows should all be accepted."""
        csv_text = (
            "date,source,price,currency\n"
            "2023-01-01,cai_spot,85.50,USD\n"
            "2023-01-02,cai_spot,86.00,USD\n"
            "2023-01-03,mcx_futures,6200.0,INR\n"
        )
        rows = parse_csv_rows(io.StringIO(csv_text))
        assert len(rows) == 3
        for row in rows:
            errors = validate_csv_row(row)
            assert not errors, f"Unexpected errors: {errors}"

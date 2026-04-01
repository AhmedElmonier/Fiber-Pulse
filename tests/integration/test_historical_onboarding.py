"""Integration tests for historical data onboarding flow.

Validates end-to-end CSV ingestion, parsing, validation, duplicate detection,
and the CLI command fiberpulse ingest-history.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from click.testing import CliRunner

from agents.historical_onboarding import (
    ingest_csv,
    ingest_history_cmd,
)

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")


@pytest.fixture
def sample_csv_file(tmp_path: Path) -> Path:
    """Create a temporary CSV file with valid historical data."""
    csv_content = (
        "date,source,price,currency\n"
        "2023-01-01,cai_spot,85.50,USD\n"
        "2023-01-02,cai_spot,86.00,USD\n"
        "2023-01-03,cai_spot,84.75,USD\n"
        "2023-01-01,mcx_futures,6200.0,INR\n"
        "2023-01-02,mcx_futures,6250.0,INR\n"
    )
    path = tmp_path / "test_data.csv"
    path.write_text(csv_content)
    return path


@pytest.fixture
def mixed_csv_file(tmp_path: Path) -> Path:
    """Create a CSV with both valid and invalid rows."""
    csv_content = (
        "date,source,price,currency\n"
        "2023-01-01,cai_spot,85.50,USD\n"
        "invalid-date,cai_spot,100.0,USD\n"
        "2023-01-03,cai_spot,-5.0,USD\n"
        "2023-01-04,,85.00,USD\n"
        "2023-01-05,cai_spot,90.0,XX\n"
        "2023-01-06,cai_spot,88.00,USD\n"
    )
    path = tmp_path / "mixed_data.csv"
    path.write_text(csv_content)
    return path


@pytest.fixture
def duplicate_csv_file(tmp_path: Path) -> Path:
    """Create a CSV with duplicate entries."""
    csv_content = (
        "date,source,price,currency\n"
        "2023-01-01,cai_spot,85.50,USD\n"
        "2023-01-01,cai_spot,85.50,USD\n"
        "2023-01-02,cai_spot,86.00,USD\n"
        "2023-01-01,cai_spot,85.50,USD\n"
    )
    path = tmp_path / "dup_data.csv"
    path.write_text(csv_content)
    return path


class TestIngestCSV:
    """Integration tests for CSV ingestion pipeline."""

    def test_valid_csv_produces_all_records(self, sample_csv_file):
        """All valid rows should produce PriceHistoryRecords."""
        records, skipped, raw_rows = ingest_csv(sample_csv_file)
        assert len(raw_rows) == 5
        assert len(records) == 5
        assert len(skipped) == 0

    def test_records_have_correct_fields(self, sample_csv_file):
        """Records should have correct source names and prices."""
        records, _, _ = ingest_csv(sample_csv_file)
        sources = [r.source_name for r in records]
        assert sources.count("cai_spot") == 3
        assert sources.count("mcx_futures") == 2

    def test_mixed_csv_skips_invalid_rows(self, mixed_csv_file):
        """Invalid rows should be skipped with error reasons."""
        records, skipped, raw_rows = ingest_csv(mixed_csv_file)
        assert len(raw_rows) == 6
        assert len(records) == 2  # Only valid rows
        assert len(skipped) == 4  # Invalid rows

        skip_errors = [s["errors"] for s in skipped]
        assert any("date" in e.lower() for e in skip_errors)
        assert any("price" in e.lower() for e in skip_errors)
        assert any("source" in e.lower() for e in skip_errors)
        assert any("currency" in e.lower() for e in skip_errors)

    def test_duplicate_detection(self, duplicate_csv_file):
        """Duplicate rows should be detected and skipped."""
        records, skipped, raw_rows = ingest_csv(duplicate_csv_file)
        assert len(raw_rows) == 4  # 4 data rows
        assert len(records) == 2  # 2 unique records
        assert len(skipped) == 2  # 2 duplicates
        for s in skipped:
            assert "duplicate" in s["errors"].lower()

    def test_source_override(self, sample_csv_file):
        """Source name should be overridden when provided."""
        records, _, _ = ingest_csv(sample_csv_file, source_name="custom_source")
        for record in records:
            assert record.source_name == "custom_source"

    def test_usd_records_have_rate_1(self, sample_csv_file):
        """USD-priced records should have conversion rate of 1.0."""
        records, _, _ = ingest_csv(sample_csv_file)
        usd_records = [r for r in records if r.raw_currency == "USD"]
        for r in usd_records:
            assert r.conversion_rate == 1.0

    def test_nonexistent_file_raises(self):
        """Missing file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            ingest_csv("/nonexistent/path/data.csv")

    def test_records_have_quality_flags(self, sample_csv_file):
        """Records should have onboarded quality flag."""
        records, _, _ = ingest_csv(sample_csv_file)
        for r in records:
            assert r.quality_flags.get("onboarded") is True

    def test_records_have_metadata(self, sample_csv_file):
        """Records should have onboarding metadata."""
        records, _, _ = ingest_csv(sample_csv_file)
        for r in records:
            assert r.metadata.get("source") == "historical_onboarding"
            assert "row_id" in r.metadata


class TestIngestHistoryCLI:
    """Integration tests for the ingest-history CLI command."""

    def test_cli_dry_run(self, sample_csv_file):
        """Dry run should parse and validate without persisting."""
        runner = CliRunner()
        result = runner.invoke(ingest_history_cmd, [str(sample_csv_file), "--dry-run"])
        assert result.exit_code == 0
        assert "Valid: 5" in result.output
        assert "Dry run" in result.output

    def test_cli_with_invalid_csv(self, mixed_csv_file):
        """CLI should report skipped rows for invalid data."""
        runner = CliRunner()
        result = runner.invoke(ingest_history_cmd, [str(mixed_csv_file), "--dry-run"])
        assert result.exit_code == 0
        assert "Valid: 2" in result.output
        assert "Skipped: 4" in result.output

    def test_cli_missing_file(self):
        """CLI should fail for non-existent file."""
        runner = CliRunner()
        result = runner.invoke(ingest_history_cmd, ["/nonexistent/file.csv"])
        assert result.exit_code != 0

    def test_cli_source_override(self, sample_csv_file):
        """CLI --source should override source name."""
        runner = CliRunner()
        result = runner.invoke(
            ingest_history_cmd,
            [str(sample_csv_file), "--dry-run", "--source", "override_src"],
        )
        assert result.exit_code == 0
        assert "Valid: 5" in result.output

    def test_cli_persist_with_mock_repo(self, sample_csv_file):
        """CLI should persist records when repository is available."""
        mock_repo = MagicMock()
        mock_repo.insert_price_record = AsyncMock()
        mock_repo.insert_onboarding_log = AsyncMock()

        runner = CliRunner()
        ctx_obj = {"repository": mock_repo}
        result = runner.invoke(
            ingest_history_cmd,
            [str(sample_csv_file)],
            obj=ctx_obj,
        )
        assert result.exit_code == 0
        assert "Persisted 5 record(s)" in result.output
        assert mock_repo.insert_price_record.call_count == 5
        assert mock_repo.insert_onboarding_log.call_count == 1

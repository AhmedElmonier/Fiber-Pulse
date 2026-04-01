"""Historical data onboarding agent for FiberPulse CLI.

Parses CSV files containing historical cotton market data, validates integrity,
normalizes currencies to USD, and persists records via the repository.
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO
from uuid import uuid4

import click

from models.historical_onboarding_log import HistoricalOnboardingLog, OnboardingStatus
from models.price_history import PriceHistoryRecord, SourceType
from utils.usd_converter import get_converter

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"date", "source", "price", "currency"}


class CsvParseError(Exception):
    """Raised when CSV parsing or validation fails."""


def parse_csv_rows(file_obj: TextIO) -> list[dict[str, str]]:
    """Parse a CSV file into a list of row dictionaries.

    Args:
        file_obj: A file-like object containing CSV data.

    Returns:
        List of row dictionaries keyed by column name.

    Raises:
        CsvParseError: If the CSV is empty or missing required columns.
    """
    content = file_obj.read().strip()
    if not content:
        raise CsvParseError("CSV file is empty")

    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        raise CsvParseError("CSV file has no header row")

    missing = REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        raise CsvParseError(f"Missing required column(s): {', '.join(sorted(missing))}")

    rows = [row for row in reader]
    if not rows:
        raise CsvParseError("No data rows found in CSV file")

    return rows


def validate_csv_row(row: dict[str, str]) -> list[str]:
    """Validate a single CSV row against the historical-ingest contract.

    Args:
        row: A dictionary mapping column names to values.

    Returns:
        List of validation error messages (empty if valid).
    """
    errors: list[str] = []

    # Validate date
    date_str = row.get("date", "").strip()
    if not date_str:
        errors.append("date is required")
    else:
        try:
            datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"date '{date_str}' is not a valid ISO-8601 format")

    # Validate price
    price_str = row.get("price", "").strip()
    if not price_str:
        errors.append("price is required")
    else:
        try:
            price = float(price_str)
            if price <= 0:
                errors.append("price must be positive")
        except ValueError:
            errors.append(f"price '{price_str}' is not a valid number")

    # Validate currency
    currency = row.get("currency", "").strip()
    if not currency:
        errors.append("currency is required")
    elif len(currency) != 3 or not currency.isalpha() or not currency.isupper():
        errors.append(f"currency must be a 3-letter uppercase ISO code, got '{currency}'")

    # Validate source
    if not row.get("source", "").strip():
        errors.append("source is required")

    return errors


def _row_to_record(
    row: dict[str, str],
    dedup_index: dict[tuple[str, str, float], bool],
) -> tuple[PriceHistoryRecord | None, str | None]:
    """Convert a validated CSV row to a PriceHistoryRecord.

    Args:
        row: Validated CSV row dictionary.
        dedup_index: Existing record keys for duplicate detection.
                     Updated in-place when a new unique record is created.

    Returns:
        Tuple of (record or None, skip reason or None).
    """
    date_str = row["date"].strip().replace("Z", "+00:00")
    timestamp = datetime.fromisoformat(date_str)
    source_name = row["source"].strip()
    raw_price = float(row["price"].strip())
    raw_currency = row["currency"].strip().upper()

    # Ensure timestamp is UTC-aware for consistent dedup keys
    if not timestamp.tzinfo:
        timestamp = timestamp.replace(tzinfo=UTC)

    # Duplicate detection
    dedup_key = (source_name, timestamp.isoformat(), raw_price)
    if dedup_key in dedup_index:
        return None, "duplicate"

    # Mark as seen before building the record
    dedup_index[dedup_key] = True

    # Currency conversion
    converter = get_converter()
    try:
        normalized_usd, conversion_rate = converter.convert_to_usd(raw_price, raw_currency)
    except ValueError:
        normalized_usd = raw_price
        conversion_rate = None
        raw_currency = raw_currency or "USD"

    record = PriceHistoryRecord(
        source_name=source_name,
        timestamp_utc=timestamp,
        raw_price=raw_price,
        normalized_usd=normalized_usd,
        source_type=SourceType.SPOT,
        raw_currency=raw_currency,
        conversion_rate=conversion_rate,
        commodity="cotton",
        quality_flags={"stale": False, "fallback": False, "onboarded": True},
        metadata={"source": "historical_onboarding", "row_id": str(uuid4())},
    )

    return record, None


def ingest_csv(
    file_path: str | Path,
    source_name: str | None = None,
) -> tuple[list[PriceHistoryRecord], list[dict[str, str]], list[dict[str, Any]]]:
    """Parse and validate a historical CSV file.

    Args:
        file_path: Path to the CSV file.
        source_name: Optional override for the source name column.

    Returns:
        Tuple of (valid_records, skipped_rows_with_reasons, raw_rows).

    Raises:
        CsvParseError: If the CSV cannot be parsed.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    with open(path, newline="", encoding="utf-8-sig") as f:
        raw_rows = parse_csv_rows(f)

    valid_records: list[PriceHistoryRecord] = []
    skipped: list[dict[str, str]] = []
    dedup_index: dict[tuple[str, str, float], bool] = {}

    for i, row in enumerate(raw_rows, start=2):
        # Validate row
        errors = validate_csv_row(row)
        if errors:
            skipped.append({"row": str(i), "errors": "; ".join(errors)})
            continue

        # Override source if provided
        if source_name:
            row["source"] = source_name

        record, skip_reason = _row_to_record(row, dedup_index)
        if skip_reason:
            skipped.append({"row": str(i), "errors": skip_reason})
            continue

        if record:
            valid_records.append(record)

    return valid_records, skipped, raw_rows


@click.command("ingest-history")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--source", default=None, help="Override source name for all rows")
@click.option("--dry-run", is_flag=True, help="Parse and validate without persisting")
@click.pass_context
def ingest_history_cmd(
    ctx: click.Context, file_path: str, source: str | None, dry_run: bool
) -> None:
    """Ingest historical cotton market data from a CSV file.

    FILE_PATH: Path to the CSV file with columns: date, source, price, currency.
    """
    repo = ctx.obj.get("repository") if ctx.obj else None

    click.echo(f"Parsing CSV: {file_path}")
    try:
        valid_records, skipped, raw_rows = ingest_csv(file_path, source_name=source)
    except (CsvParseError, FileNotFoundError) as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)
        return

    click.echo(f"Total rows: {len(raw_rows)}, Valid: {len(valid_records)}, Skipped: {len(skipped)}")

    if skipped:
        click.echo("\nSkipped rows:")
        for s in skipped:
            click.echo(f"  Row {s['row']}: {s['errors']}")

    if dry_run:
        click.echo("\nDry run — no records persisted.")
        return

    if not valid_records:
        click.echo("No valid records to persist.")
        return

    if repo is None:
        click.echo("Error: database repository not available", err=True)
        ctx.exit(1)
        return

    # Persist records
    import asyncio

    async def _persist() -> int:
        count = 0
        for record in valid_records:
            try:
                await repo.insert_price_record(record)
                count += 1
            except Exception:
                logger.exception("Failed to persist record %s", record.source_name)
        return count

    persisted = asyncio.run(_persist())

    # Log the onboarding run
    log_entry = HistoricalOnboardingLog(
        file_name=Path(file_path).name,
        timestamp_utc=datetime.now(UTC),
        record_count=persisted,
        status=OnboardingStatus.SUCCESS
        if persisted == len(valid_records)
        else OnboardingStatus.PARTIAL,
        error_summary="; ".join(f"Row {s['row']}: {s['errors']}" for s in skipped)
        if skipped
        else None,
        metadata={
            "total_rows": len(raw_rows),
            "valid": len(valid_records),
            "skipped": len(skipped),
        },
    )

    async def _log() -> None:
        await repo.insert_onboarding_log(log_entry)

    asyncio.run(_log())

    click.echo(f"\nPersisted {persisted} record(s).")
    if persisted < len(valid_records):
        click.echo(
            f"Warning: {len(valid_records) - persisted} record(s) failed to persist.", err=True
        )

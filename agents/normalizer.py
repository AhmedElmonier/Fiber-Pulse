"""Data normalizer agent for FiberPulse ingestion.

Validates incoming source payloads, applies USD conversion,
annotates audit metadata, and prepares normalized records for persistence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from db.repository import PRICE_EPSILON
from models.freight_rate import FreightRate
from models.macro_feed_record import MacroFeedRecord
from models.price_history import PriceHistoryRecord, SourceType
from utils.usd_converter import USDConverter, get_converter


class NormalizerError(Exception):
    """Error raised during normalization."""


class Normalizer:
    """Normalizes raw price data for persistence.

    Validates incoming payloads, converts currency to USD,
    and prepares record objects with proper metadata.
    """

    def __init__(self, converter: USDConverter | None = None) -> None:
        """Initialize the normalizer.

        Args:
            converter: Optional USD converter instance (uses global if not provided).
        """
        self.converter = converter or get_converter()

    def validate_payload(self, payload: dict[str, Any], required_fields: list[str] | None = None) -> list[str]:
        """Validate a raw source payload.

        Args:
            payload: The raw payload from a data source.
            required_fields: Optional list of required fields.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: list[str] = []

        # Required fields per contract
        fields = required_fields or ["source_name", "timestamp_utc", "commodity", "raw_price", "raw_currency"]
        for field in fields:
            if field not in payload:
                errors.append(f"Missing required field: {field}")

        # Validate timestamp format
        if "timestamp_utc" in payload:
            timestamp = payload["timestamp_utc"]
            if isinstance(timestamp, str):
                try:
                    datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"Invalid timestamp format: {timestamp}")
            elif not isinstance(timestamp, datetime):
                errors.append(f"timestamp_utc must be datetime or ISO string, got {type(timestamp)}")

        # Validate price/rate is non-negative
        price_field = "raw_price"
        if price_field in payload:
            try:
                price = float(payload[price_field])
                if price < 0:
                    errors.append(f"{price_field} must be non-negative, got {price}")
            except (TypeError, ValueError):
                errors.append(f"Invalid {price_field} value: {payload[price_field]}")

        # Validate currency is a valid code
        if "raw_currency" in payload:
            currency = payload["raw_currency"]
            if not isinstance(currency, str) or len(currency) != 3:
                errors.append(f"raw_currency must be a 3-letter currency code, got {currency}")

        return errors

    def _parse_timestamp(self, timestamp_raw: Any) -> datetime:
        """Parse raw timestamp into UTC datetime."""
        if isinstance(timestamp_raw, str):
            return datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
        if isinstance(timestamp_raw, datetime):
            return timestamp_raw
        raise ValueError(f"Invalid timestamp type: {type(timestamp_raw)}")

    def _convert_currency(self, amount: float, currency: str) -> tuple[float, float]:
        """Convert amount to USD and return (normalized_amount, rate)."""
        try:
            return self.converter.convert_to_usd(amount, currency.upper())
        except ValueError as e:
            raise NormalizerError(f"Currency conversion failed: {e}") from e

    def _normalize_core(
        self,
        payload: dict[str, Any],
        raw_price_field: str,
        quality_flags: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Core normalization logic shared across all record types.

        Returns:
            Dictionary of normalized fields and metadata.
        """
        source_name = payload["source_name"]
        raw_price = float(payload[raw_price_field])
        raw_currency = payload["raw_currency"]
        timestamp_utc = self._parse_timestamp(payload["timestamp_utc"])

        # Convert to USD
        normalized_usd, conversion_rate = self._convert_currency(raw_price, raw_currency)

        normalized_at = datetime.now(timezone.utc)
        metadata = {
            "raw_payload": payload,
            "normalized_at": normalized_at.isoformat(),
        }
        if payload.get("metadata"):
            metadata["extraction_context"] = payload["metadata"]

        flags = quality_flags or {"stale": False, "fallback": False}
        if payload.get("fallback_source"):
            flags["fallback"] = True
            flags["fallback_source"] = payload["fallback_source"]

        return {
            "source_name": source_name,
            "timestamp_utc": timestamp_utc,
            "raw_price": raw_price,
            "raw_currency": raw_currency,
            "normalized_usd": normalized_usd,
            "conversion_rate": conversion_rate,
            "normalized_at": normalized_at,
            "quality_flags": flags,
            "metadata": metadata,
        }

    def normalize(
        self,
        payload: dict[str, Any],
        source_type: SourceType = SourceType.SPOT,
        quality_flags: dict[str, Any] | None = None,
    ) -> PriceHistoryRecord:
        """Normalize a raw payload into a PriceHistoryRecord.

        Args:
            payload: The raw payload from a data source.
            source_type: The type of source (spot, future, fallback, macro).
            quality_flags: Optional quality flags to apply.

        Returns:
            A normalized PriceHistoryRecord ready for persistence.

        Raises:
            NormalizerError: If validation fails or conversion is unavailable.
        """
        # Validate payload first
        errors = self.validate_payload(payload)
        if errors:
            raise NormalizerError(f"Payload validation failed: {'; '.join(errors)}")

        normalized = self._normalize_core(payload, "raw_price", quality_flags)
        normalized["metadata"]["source_type"] = source_type.value

        return PriceHistoryRecord(
            source_name=normalized["source_name"],
            source_type=source_type,
            timestamp_utc=normalized["timestamp_utc"],
            commodity=payload.get("commodity", "cotton"),
            region=payload.get("region"),
            raw_price=normalized["raw_price"],
            raw_currency=normalized["raw_currency"],
            normalized_usd=normalized["normalized_usd"],
            conversion_rate=normalized["conversion_rate"],
            normalized_at=normalized["normalized_at"],
            quality_flags=normalized["quality_flags"],
            metadata=normalized["metadata"],
        )

    def normalize_freight(
        self,
        payload: dict[str, Any],
        quality_flags: dict[str, Any] | None = None,
    ) -> FreightRate:
        """Normalize a raw freight payload into a FreightRate.

        Args:
            payload: Raw freight payload (source_name, route, timestamp_utc, raw_price, raw_currency).
            quality_flags: Optional quality flags.

        Returns:
            A normalized FreightRate ready for persistence.
        """
        required = ["source_name", "route", "timestamp_utc", "raw_price", "raw_currency"]
        errors = self.validate_payload(payload, required_fields=required)
        if errors:
            raise NormalizerError(f"Freight validation failed: {'; '.join(errors)}")

        normalized = self._normalize_core(payload, "raw_price", quality_flags)

        return FreightRate(
            source_name=normalized["source_name"],
            route=payload["route"],
            timestamp_utc=normalized["timestamp_utc"],
            raw_price=normalized["raw_price"],
            raw_currency=normalized["raw_currency"],
            normalized_usd=normalized["normalized_usd"],
            conversion_rate=normalized["conversion_rate"],
            quality_flags=normalized["quality_flags"],
            metadata=normalized["metadata"],
        )

    def normalize_macro(
        self,
        payload: dict[str, Any],
        quality_flags: dict[str, Any] | None = None,
    ) -> MacroFeedRecord:
        """Normalize a raw macro payload into a MacroFeedRecord.

        Args:
            payload: Raw macro payload (source_name, commodity, timestamp_utc, raw_price, raw_currency).
            quality_flags: Optional quality flags.

        Returns:
            A normalized MacroFeedRecord ready for persistence.
        """
        # Macro use same fields as standard normalization for now
        errors = self.validate_payload(payload)
        if errors:
            raise NormalizerError(f"Macro validation failed: {'; '.join(errors)}")

        normalized = self._normalize_core(payload, "raw_price", quality_flags)
        normalized["metadata"]["source_type"] = SourceType.MACRO.value

        return MacroFeedRecord(
            source_name=normalized["source_name"],
            commodity=payload["commodity"],
            timestamp_utc=normalized["timestamp_utc"],
            raw_price=normalized["raw_price"],
            raw_currency=normalized["raw_currency"],
            normalized_usd=normalized["normalized_usd"],
            conversion_rate=normalized["conversion_rate"],
            normalized_at=normalized["normalized_at"],
            quality_flags=normalized["quality_flags"],
            metadata=normalized["metadata"],
        )


    def normalize_batch(
        self,
        payloads: list[dict[str, Any]],
        source_type: SourceType = SourceType.SPOT,
        quality_flags: dict[str, Any] | None = None,
    ) -> tuple[list[PriceHistoryRecord], list[tuple[dict[str, Any], str]]]:
        """Normalize multiple payloads, separating successes from failures.

        Args:
            payloads: List of raw payloads from data sources.
            source_type: The type of source.
            quality_flags: Optional quality flags to apply.

        Returns:
            Tuple of (successful_records, failed_payloads_with_errors).
        """
        successful: list[PriceHistoryRecord] = []
        failed: list[tuple[dict[str, Any], str]] = []

        for payload in payloads:
            try:
                record = self.normalize(payload, source_type, quality_flags)
                successful.append(record)
            except NormalizerError as e:
                failed.append((payload, str(e)))

        return successful, failed

    def detect_duplicate(
        self, payload: dict[str, Any], existing_timestamps: set[tuple[str, datetime, float]]
    ) -> bool:
        """Check if a payload would be a duplicate based on source, timestamp, and price.

        Args:
            payload: The raw payload to check.
            existing_timestamps: Set of (source_name, timestamp, raw_price) tuples.

        Returns:
            True if the payload is a duplicate, False otherwise.
        """
        source_name = payload.get("source_name")
        if not source_name or not isinstance(source_name, str):
            return False

        raw_price_value = payload.get("raw_price")
        try:
            raw_price = float(raw_price_value)
        except (TypeError, ValueError):
            return False

        timestamp_raw = payload.get("timestamp_utc")
        if isinstance(timestamp_raw, str):
            try:
                timestamp = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
            except ValueError:
                return False
        elif isinstance(timestamp_raw, datetime):
            timestamp = timestamp_raw
        else:
            return False

        for existing_source, existing_timestamp, existing_raw_price in existing_timestamps:
            if (
                existing_source == source_name
                and existing_timestamp == timestamp
                and abs(raw_price - existing_raw_price) <= PRICE_EPSILON
            ):
                return True

        return False


def normalize_payload(
    payload: dict[str, Any],
    source_type: SourceType = SourceType.SPOT,
    quality_flags: dict[str, Any] | None = None,
) -> PriceHistoryRecord:
    """Convenience function to normalize a single payload.

    Args:
        payload: The raw payload from a data source.
        source_type: The type of source.
        quality_flags: Optional quality flags to apply.

    Returns:
        A normalized PriceHistoryRecord ready for persistence.
    """
    normalizer = Normalizer()
    return normalizer.normalize(payload, source_type, quality_flags)
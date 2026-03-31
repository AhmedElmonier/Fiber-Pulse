"""USD conversion utility for FiberPulse ingestion.

Normalizes raw currency values into USD using exchange rate data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.currency_conversion import CurrencyConversionRecord


class USDConverter:
    """Converts raw currency values to USD using exchange rate data.

    Provides currency normalization for the ingestion pipeline,
    supporting multiple currencies with rate lookup from the
    currency_conversion table.
    """

    def __init__(self) -> None:
        """Initialize the USD converter with an empty rate cache."""
        self._rate_cache: dict[str, float] = {"USD": 1.0}
        self._rate_timestamps: dict[str, datetime] = {}

    def set_rate(self, currency: str, rate_to_usd: float, timestamp: datetime | None = None) -> None:
        """Set the conversion rate for a currency.

        Args:
            currency: ISO currency code (e.g., 'INR', 'CNY', 'EUR').
            rate_to_usd: Exchange rate to USD (e.g., 83.0 for INR).
            timestamp: Timestamp of the rate (defaults to now).
        """
        if rate_to_usd <= 0:
            raise ValueError(f"rate_to_usd must be positive, got {rate_to_usd}")

        self._rate_cache[currency.upper()] = rate_to_usd
        self._rate_timestamps[currency.upper()] = timestamp or datetime.now(timezone.utc)

    def get_rate(self, currency: str) -> float | None:
        """Get the conversion rate for a currency.

        Args:
            currency: ISO currency code.

        Returns:
            The exchange rate to USD, or None if not available.
        """
        return self._rate_cache.get(currency.upper())

    def convert_to_usd(
        self,
        raw_price: float,
        raw_currency: str,
        rate: float | None = None,
    ) -> tuple[float, float | None]:
        """Convert a raw price value to USD.

        Args:
            raw_price: The original price value.
            raw_currency: The original currency code.
            rate: Optional explicit rate (uses cached rate if not provided).

        Returns:
            Tuple of (normalized_usd, conversion_rate).

        Raises:
            ValueError: If no conversion rate is available for the currency.
        """
        currency = raw_currency.upper()

        if currency == "USD":
            return raw_price, 1.0

        # Use explicit rate if provided
        if rate is not None:
            if rate <= 0:
                raise ValueError(f"rate must be positive, got {rate}")
            normalized_usd = raw_price / rate
            return normalized_usd, rate

        # Use cached rate
        cached_rate = self._rate_cache.get(currency)
        if cached_rate is None:
            raise ValueError(f"No conversion rate available for currency: {currency}")

        normalized_usd = raw_price / cached_rate
        return normalized_usd, cached_rate

    def load_rates_from_records(self, records: list["CurrencyConversionRecord"]) -> None:
        """Load conversion rates from database records.

        Args:
            records: List of CurrencyConversionRecord objects.
        """
        for record in records:
            if record.rate_to_usd > 0:
                self._rate_cache[record.currency.upper()] = record.rate_to_usd
                self._rate_timestamps[record.currency.upper()] = record.rate_timestamp or datetime.now(
                    timezone.utc
                )

    def get_supported_currencies(self) -> list[str]:
        """Get list of supported currencies.

        Returns:
            List of currency codes with available conversion rates.
        """
        return sorted(self._rate_cache.keys())

    def clear_cache(self) -> None:
        """Clear all cached conversion rates except USD."""
        self._rate_cache = {"USD": 1.0}
        self._rate_timestamps = {}


# Global converter instance
_converter: USDConverter | None = None


def get_converter() -> USDConverter:
    """Get the global USD converter instance.

    Lazily initializes the converter on first access.
    """
    global _converter
    if _converter is None:
        _converter = USDConverter()
    return _converter


def reset_converter() -> None:
    """Reset the global USD converter instance.

    Useful for testing or reloading rates.
    """
    global _converter
    _converter = None
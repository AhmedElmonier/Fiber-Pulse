"""Base scraper interface for FiberPulse data ingestion.

Defines the contract that all source adapters must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class SourceCategory(str, Enum):
    """Category of data source."""

    PRIMARY = "primary"
    FALLBACK = "fallback"
    CURRENCY_RATE = "currency_rate"
    UTILITY = "utility"


@dataclass
class ScraperResult:
    """Result from a scraper ingestion attempt.

    Attributes:
        success: Whether the scrape was successful.
        records: List of raw payload dictionaries from the source.
        error: Error message if the scrape failed.
        metadata: Additional context about the scrape (e.g., response time, headers).
        timestamp: When the scrape was performed.
        source_name: The source identifier.
    """

    success: bool
    records: list[dict[str, Any]]
    error: str | None = None
    metadata: dict[str, Any] | None = None
    timestamp: datetime | None = None
    source_name: str = ""

    def __post_init__(self) -> None:
        """Set default timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class BaseScraper(ABC):
    """Abstract base class for all data source scrapers.

    All source adapters must implement this interface to be used
    by the data fetcher orchestration layer.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the canonical source identifier."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Return the human-friendly source name."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return the source type (spot, future, etc.)."""
        pass

    @property
    def category(self) -> SourceCategory:
        """Return the source category (primary, fallback, etc.)."""
        return SourceCategory.PRIMARY

    @property
    def fallback_to(self) -> str | None:
        """Return the fallback source name if this source fails."""
        return None

    @property
    def source_url(self) -> str | None:
        """Return the source URL if applicable."""
        return None

    @abstractmethod
    async def fetch(self, **kwargs: Any) -> ScraperResult:
        """Fetch data from the source.

        Args:
            **kwargs: Additional parameters for the fetch operation.

        Returns:
            ScraperResult with the fetched data or error.
        """
        pass

    @abstractmethod
    def parse(self, raw_data: Any) -> list[dict[str, Any]]:
        """Parse raw data from the source into standardized payloads.

        Args:
            raw_data: Raw data from the source (HTML, JSON, etc.).

        Returns:
            List of standardized payload dictionaries matching the
            ingestion contract.
        """
        pass

    async def scrape(self, **kwargs: Any) -> ScraperResult:
        """Execute the full scrape pipeline: fetch + parse.

        Args:
            **kwargs: Additional parameters for the scrape operation.

        Returns:
            ScraperResult with the parsed records.
        """
        import time

        start_time = time.time()

        try:
            # Fetch raw data
            fetch_result = await self.fetch(**kwargs)

            if not fetch_result.success:
                return ScraperResult(
                    success=False,
                    records=[],
                    error=fetch_result.error,
                    source_name=self.source_name,
                )

            # Parse into standardized format
            records = self.parse(fetch_result.records)

            elapsed_time = time.time() - start_time

            return ScraperResult(
                success=True,
                records=records,
                metadata={
                    "elapsed_seconds": elapsed_time,
                    "source_url": self.source_url,
                    "records_count": len(records),
                    **(fetch_result.metadata or {}),
                },
                source_name=self.source_name,
            )

        except Exception as e:
            return ScraperResult(
                success=False,
                records=[],
                error=f"Scrape failed: {e}",
                source_name=self.source_name,
            )

    def validate_payload(self, payload: dict[str, Any]) -> list[str]:
        """Validate a parsed payload against the ingestion contract.

        Args:
            payload: The parsed payload to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        errors: list[str] = []

        required_fields = ["source_name", "timestamp_utc", "commodity", "raw_price", "raw_currency"]
        for field in required_fields:
            if field not in payload:
                errors.append(f"Missing required field: {field}")

        if "raw_price" in payload:
            try:
                price = float(payload["raw_price"])
                if price <= 0:
                    errors.append("raw_price must be positive")
            except (TypeError, ValueError):
                errors.append("raw_price must be a number")

        if "raw_currency" in payload:
            currency = payload["raw_currency"]
            if not isinstance(currency, str) or len(currency) != 3:
                errors.append("raw_currency must be a 3-letter currency code")

        return errors
"""Drewry WCI freight scraper for FiberPulse ingestion.

Implements the adapter contract for the Drewry WCI (World Container Index)
freight rates.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from agents.base_scraper import BaseScraper, ScraperResult, SourceCategory


class DrewryWCIScraper(BaseScraper):
    """Scraper for Drewry World Container Index (WCI) freight rates.

    Fetches global freight indices from Drewry. Implements the BaseScraper
    interface for Phase 2 logistics data collection.

    Attributes:
        _source_url (str): The URL used to fetch Drewry WCI data.
        _timeout (float): Request timeout in seconds.
    """

    def __init__(
        self,
        source_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Drewry WCI scraper.

        Args:
            source_url: Override the default source URL.
            timeout: Request timeout in seconds for data fetching.
        """
        self._source_url = source_url or "https://www.drewry.co.uk/supply-chain-advisors/world-container-index"
        self._timeout = timeout

    @property
    def source_name(self) -> str:
        """Return the canonical source identifier for Drewry WCI."""
        return "drewry_wci"

    @property
    def display_name(self) -> str:
        """Return the human-friendly source name."""
        return "Drewry WCI"

    @property
    def source_type(self) -> str:
        """Return the source type as 'freight'."""
        return "freight"

    @property
    def category(self) -> SourceCategory:
        """Return the source category as PRIMARY."""
        return SourceCategory.PRIMARY

    @property
    def source_url(self) -> str:
        """Return the source URL being scraped."""
        return self._source_url

    async def fetch(self, **kwargs: Any) -> ScraperResult:
        """Fetch raw freight data from the Drewry source.

        Currently provides MVP placeholder logic returning static records
        simulating a successful fetch of Shanghai-Rotterdam indices.

        Args:
            **kwargs: Additional parameters for the fetch operation.

        Returns:
            ScraperResult containing success status and raw records.
        """
        # For MVP, we provide a placeholder.
        try:
            return ScraperResult(
                success=True,
                records=[{
                    "route": "Shanghai-Rotterdam",
                    "index": 3500.0,
                    "currency": "USD",
                    "date": datetime.now(timezone.utc).isoformat()
                }],
                source_name=self.source_name,
            )
        except Exception as e:
            return ScraperResult(
                success=False,
                records=[],
                error=f"Fetch failed: {e}",
                source_name=self.source_name,
            )

    def parse(self, raw_data: Any) -> list[dict[str, Any]]:
        """Parse raw Drewry data into standardized freight payloads.

        Extracts route, index, and date metadata into a dictionary format
        conforming to the Raw Source Payload Contract.

        Args:
            raw_data: The data returned by the fetch method.

        Returns:
            A list of standardized freight payload dictionaries.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        for item in raw_data:
            try:
                raw_price = float(item.get("index", 0))
            except (ValueError, TypeError):
                raw_price = 0.0

            records.append({
                "source_name": self.source_name,
                "route": item.get("route", "Shanghai-Rotterdam"),
                "timestamp_utc": item.get("date", now.isoformat()),
                "raw_price": raw_price,
                "raw_currency": item.get("currency", "USD"),
                "metadata": {
                    "original_payload": item
                }
            })
        return records

    def validate_payload(self, payload: dict[str, Any]) -> list[str]:
        """Validate a freight payload for required Drewry fields.

        Ensures presence of route, raw_price, and currency fields.

        Args:
            payload: The parsed payload to validate.

        Returns:
            A list of error messages, empty if valid.
        """
        errors: list[str] = []
        required = ["source_name", "route", "timestamp_utc", "raw_price", "raw_currency"]
        for field in required:
            if field not in payload:
                errors.append(f"Missing required field: {field}")
        return errors

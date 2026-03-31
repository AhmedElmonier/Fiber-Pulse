"""Macro feed scraper for FiberPulse ingestion.

Implements the adapter contract for various macroeconomic feeds:
FX rates (USD/INR, USD/CNY), oil spot prices, and electricity rates.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from agents.base_scraper import BaseScraper, ScraperResult, SourceCategory


class MacroFeedScraper(BaseScraper):
    """Scraper for various macroeconomic feeds.

    Supports fx_usd_inr, fx_usd_cny, oil_spot, and electricity. Implements
    the BaseScraper interface for Phase 2 macroeconomic data collection.

    Attributes:
        _source_name (str): Canonical identifier for the macro source.
        _source_url (str): The URL used to fetch macro data.
        _timeout (float): Request timeout in seconds.
    """

    def __init__(
        self,
        source_name: str,
        source_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the macro feed scraper.

        Args:
            source_name: Canonical identifier for the macro source.
            source_url: Override the default source URL.
            timeout: Request timeout in seconds for data fetching.
        """
        self._source_name = source_name
        self._source_url = source_url or "https://api.macro-feed.example/v1/data"
        self._timeout = timeout

    @property
    def source_name(self) -> str:
        """Return the canonical source identifier for this macro feed."""
        return self._source_name

    @property
    def display_name(self) -> str:
        """Return the human-friendly source name mapping."""
        mapping = {
            "fx_usd_inr": "FX USD/INR",
            "fx_usd_cny": "FX USD/CNY",
            "oil_spot": "Brent Oil Spot",
            "electricity": "Base Load Electricity",
        }
        return mapping.get(self._source_name, f"Macro {self._source_name}")

    @property
    def source_type(self) -> str:
        """Return the source type as 'macro'."""
        return "macro"

    @property
    def category(self) -> SourceCategory:
        """Return the source category as PRIMARY."""
        return SourceCategory.PRIMARY

    @property
    def source_url(self) -> str:
        """Return the source URL being scraped."""
        return self._source_url

    async def fetch(self, **kwargs: Any) -> ScraperResult:
        """Fetch raw macro data from the configured source.

        Currently provides MVP placeholder logic returning static records
        mapped to the specific macro source name.

        Args:
            **kwargs: Additional parameters for the fetch operation.

        Returns:
            ScraperResult containing success status and raw records.
        """
        # For MVP, provide placeholder data based on source_name.
        now = datetime.now(timezone.utc)
        
        data_mapping = {
            "fx_usd_inr": {"commodity": "usd_inr", "price": 83.15, "currency": "INR"},
            "fx_usd_cny": {"commodity": "usd_cny", "price": 7.23, "currency": "CNY"},
            "oil_spot": {"commodity": "brent_oil", "price": 78.45, "currency": "USD"},
            "electricity": {"commodity": "base_load", "price": 0.12, "currency": "USD"},
        }
        
        record = data_mapping.get(self._source_name)
        if record:
            record["date"] = now.isoformat()
            return ScraperResult(
                success=True,
                records=[record],
                source_name=self.source_name,
            )
        else:
            return ScraperResult(
                success=False,
                records=[],
                error=f"Unsupported macro source: {self._source_name}",
                source_name=self.source_name,
            )

    def parse(self, raw_data: Any) -> list[dict[str, Any]]:
        """Parse raw macro data into standardized macro payloads.

        Extracts commodity, price, and date metadata into a dictionary format
        conforming to the Raw Source Payload Contract.

        Args:
            raw_data: The data returned by the fetch method.

        Returns:
            A list of standardized macro payload dictionaries.
        """
        records: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        for item in raw_data:
            try:
                raw_price = float(item.get("price", 0))
            except (ValueError, TypeError):
                raw_price = 0.0

            records.append({
                "source_name": self.source_name,
                "commodity": item.get("commodity", "macro"),
                "timestamp_utc": item.get("date", now.isoformat()),
                "raw_price": raw_price,
                "raw_currency": item.get("currency", "USD"),
                "metadata": {
                    "original_payload": item
                }
            })
        return records

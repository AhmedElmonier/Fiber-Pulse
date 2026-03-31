"""MCX cotton futures price scraper for FiberPulse ingestion.

Implements the adapter contract for the MCX (Multi Commodity Exchange)
cotton futures price feed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

import httpx

from agents.base_scraper import BaseScraper, ScraperResult, SourceCategory


class MCXFuturesScraper(BaseScraper):
    """Scraper for MCX cotton futures prices.

    Fetches cotton futures prices from the Multi Commodity Exchange of India.
    This is a primary data source for Indian cotton futures prices.
    """

    def __init__(
        self,
        source_url: str | None = None,
        timeout: float = 30.0,
        fallback_source: str | None = "fibre2fashion",
        use_mock_fallback: bool = False,
    ) -> None:
        """Initialize the MCX futures scraper.

        Args:
            source_url: Override the default source URL.
            timeout: Request timeout in seconds.
            fallback_source: Name of the fallback source if this fails.
        """
        self._source_url = source_url or "https://www.mcxindia.com/marketdata/cotton"
        self._timeout = timeout
        self._fallback_source = fallback_source
        self.use_mock_fallback = use_mock_fallback

    @property
    def source_name(self) -> str:
        """Return the canonical source identifier."""
        return "mcx_futures"

    @property
    def display_name(self) -> str:
        """Return the human-friendly source name."""
        return "MCX Cotton Futures"

    @property
    def source_type(self) -> str:
        """Return the source type."""
        return "future"

    @property
    def category(self) -> SourceCategory:
        """Return the source category."""
        return SourceCategory.PRIMARY

    @property
    def fallback_to(self) -> str | None:
        """Return the fallback source name."""
        return self._fallback_source

    @property
    def source_url(self) -> str:
        """Return the source URL."""
        return self._source_url

    async def fetch(self, **kwargs: Any) -> ScraperResult:
        """Fetch data from the MCX source.

        This is a placeholder implementation. In production, this would
        make an actual HTTP request to the MCX endpoint.

        Args:
            **kwargs: Additional parameters (e.g., contract month).

        Returns:
            ScraperResult with raw HTML/JSON data.
        """
        headers = {
            "User-Agent": "FiberPulse/1.0 (Market Data Ingestion)",
            "Accept": "application/json, text/html",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(self._source_url, headers=headers)
                response.raise_for_status()

                # Try to parse as JSON first
                try:
                    data = response.json()
                except Exception:
                    # Fall back to HTML parsing
                    data = {"html": response.text, "content_type": "text/html"}

                return ScraperResult(
                    success=True,
                    records=[data] if isinstance(data, dict) else data,
                    metadata={
                        "status_code": response.status_code,
                        "content_type": response.headers.get("content-type"),
                    },
                    source_name=self.source_name,
                )

            except httpx.HTTPStatusError as e:
                return ScraperResult(
                    success=False,
                    records=[],
                    error=f"HTTP error: {e.response.status_code}",
                    source_name=self.source_name,
                )

            except httpx.RequestError as e:
                return ScraperResult(
                    success=False,
                    records=[],
                    error=f"Request error: {e}",
                    source_name=self.source_name,
                )

    def parse(self, raw_data: Any) -> list[dict[str, Any]]:
        """Parse raw MCX data into standardized payloads.

        This is a placeholder implementation. In production, this would
        parse the actual HTML/JSON structure from MCX.

        Args:
            raw_data: Raw data from the fetch operation.

        Returns:
            List of standardized payload dictionaries.
        """
        now = datetime.now(timezone.utc)
        records: list[dict[str, Any]] = []

        # Handle mock/test data
        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict) and "price" in item:
                    payload = self._create_payload(item, now)
                    if payload is not None:
                        records.append(payload)
        elif isinstance(raw_data, dict):
            if "contracts" in raw_data:
                for contract in raw_data["contracts"]:
                    payload = self._create_payload(contract, now)
                    if payload is not None:
                        records.append(payload)
            elif "prices" in raw_data:
                for item in raw_data["prices"]:
                    payload = self._create_payload(item, now)
                    if payload is not None:
                        records.append(payload)
            elif "price" in raw_data:
                payload = self._create_payload(raw_data, now)
                if payload is not None:
                    records.append(payload)

        if not records:
            if self.use_mock_fallback:
                records.append(self._create_mock_payload(now))
            else:
                logger.warning(
                    "No MCX records parsed from raw_data; returning empty list. raw_data=%r",
                    raw_data,
                )

        return records

    def _create_payload(self, data: dict[str, Any], timestamp: datetime) -> dict[str, Any] | None:
        """Create a standardized payload from parsed data.

        Args:
            data: Parsed data from the source.
            timestamp: Timestamp for the record.

        Returns:
            Standardized payload dictionary, or None when the price is invalid.
        """
        price_raw = data.get("price")
        raw_price = None
        if price_raw is not None:
            try:
                price_value = float(price_raw)
                if price_value > 0:
                    raw_price = price_value
            except (TypeError, ValueError):
                raw_price = None

        if raw_price is None:
            return None

        return {
            "source_name": self.source_name,
            "timestamp_utc": data.get("timestamp", timestamp).isoformat()
            if isinstance(data.get("timestamp"), datetime)
            else timestamp.isoformat(),
            "commodity": "cotton",
            "raw_price": raw_price,
            "raw_currency": data.get("currency", "INR"),
            "region": data.get("region", "India"),
            "metadata": {
                "contract": data.get("contract"),
                "expiry": data.get("expiry"),
                "open_interest": data.get("open_interest"),
                "volume": data.get("volume"),
            },
        }

    def _create_mock_payload(self, timestamp: datetime) -> dict[str, Any]:
        """Create a mock payload for testing.

        Args:
            timestamp: Timestamp for the record.

        Returns:
            Mock payload dictionary.
        """
        return {
            "source_name": self.source_name,
            "timestamp_utc": timestamp.isoformat(),
            "commodity": "cotton",
            "raw_price": 58800.0,  # Approximate INR per bale (170 kg)
            "raw_currency": "INR",
            "region": "India",
            "metadata": {
                "contract": "KAPAS",
                "expiry": "2024-05",
                "open_interest": 12500,
                "volume": 50000,
                "mock": True,
            },
        }


# Factory function for easier instantiation
def create_mcx_futures_scraper(**kwargs: Any) -> MCXFuturesScraper:
    """Create an MCX futures scraper instance.

    Args:
        **kwargs: Arguments passed to MCXFuturesScraper.

    Returns:
        Configured MCXFuturesScraper instance.
    """
    return MCXFuturesScraper(**kwargs)
"""CAI cotton spot price scraper for FiberPulse ingestion.

Implements the adapter contract for the CAI (Cotton Association of India)
spot price feed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from agents.base_scraper import BaseScraper, ScraperResult, SourceCategory


class CAISpotScraper(BaseScraper):
    """Scraper for CAI cotton spot prices.

    Fetches cotton spot prices from the Cotton Association of India.
    This is a primary data source for Indian cotton spot prices.
    """

    def __init__(
        self,
        source_url: str | None = None,
        timeout: float = 30.0,
        fallback_source: str | None = "ccfgroup",
        use_mock_fallback: bool = False,
    ) -> None:
        """Initialize the CAI spot scraper.

        Args:
            source_url: Override the default source URL.
            timeout: Request timeout in seconds.
            fallback_source: Name of the fallback source if this fails.
        """
        self._source_url = source_url or "https://cai.mci.org.in/spot-prices"
        self._timeout = timeout
        self._fallback_source = fallback_source
        self.use_mock_fallback = use_mock_fallback

    @property
    def source_name(self) -> str:
        """Return the canonical source identifier."""
        return "cai_spot"

    @property
    def display_name(self) -> str:
        """Return the human-friendly source name."""
        return "CAI Cotton Spot"

    @property
    def source_type(self) -> str:
        """Return the source type."""
        return "spot"

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
        """Fetch data from the CAI source.

        This is a placeholder implementation. In production, this would
        make an actual HTTP request to the CAI endpoint.

        Args:
            **kwargs: Additional parameters (e.g., date range).

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
        """Parse raw CAI data into standardized payloads.

        This is a placeholder implementation. In production, this would
        parse the actual HTML/JSON structure from CAI.

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
            if "prices" in raw_data:
                for item in raw_data["prices"]:
                    payload = self._create_payload(item, now)
                    if payload is not None:
                        records.append(payload)
            elif "price" in raw_data:
                payload = self._create_payload(raw_data, now)
                if payload is not None:
                    records.append(payload)

        if not records and self.use_mock_fallback:
            records.append(self._create_mock_payload(now))

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
                "grade": data.get("grade"),
                "variety": data.get("variety"),
                "market": data.get("market"),
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
            "raw_price": 58500.0,  # Approximate INR per candy (355 kg)
            "raw_currency": "INR",
            "region": "India",
            "metadata": {
                "grade": "J-34",
                "variety": "Shankar-6",
                "market": "Rajkot",
                "mock": True,
            },
        }


# Factory function for easier instantiation
def create_cai_spot_scraper(**kwargs: Any) -> CAISpotScraper:
    """Create a CAI spot scraper instance.

    Args:
        **kwargs: Arguments passed to CAISpotScraper.

    Returns:
        Configured CAISpotScraper instance.
    """
    return CAISpotScraper(**kwargs)
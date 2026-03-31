"""IEA (International Energy Agency) data scraper for FiberPulse ingestion.

Implements the adapter contract for IEA data as a utility/fallback source.
Note: IEA is primarily energy-focused but may provide macro indicators.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

from agents.base_scraper import BaseScraper, ScraperResult, SourceCategory


class IEAScraper(BaseScraper):
    """Scraper for IEA data.

    Fetches macro indicators from IEA as a utility source
    for macroeconomic context.
    """

    def __init__(
        self,
        source_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the IEA scraper.

        Args:
            source_url: Override the default source URL.
            timeout: Request timeout in seconds.
        """
        self._source_url = source_url or "https://api.iea.org/data"
        self._timeout = timeout

    @property
    def source_name(self) -> str:
        """Return the canonical source identifier."""
        return "iea"

    @property
    def display_name(self) -> str:
        """Return the human-friendly source name."""
        return "IEA Macro Indicators"

    @property
    def source_type(self) -> str:
        """Return the source type."""
        return "macro"

    @property
    def category(self) -> SourceCategory:
        """Return the source category."""
        return SourceCategory.UTILITY

    @property
    def source_url(self) -> str:
        """Return the source URL."""
        return self._source_url

    async def fetch(self, **kwargs: Any) -> ScraperResult:
        """Fetch data from the IEA source.

        Args:
            **kwargs: Additional parameters.

        Returns:
            ScraperResult with raw data.
        """
        headers = {
            "User-Agent": "FiberPulse/1.0 (Market Data Ingestion)",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(self._source_url, headers=headers)
                response.raise_for_status()

                try:
                    data = response.json()
                except Exception:
                    data = {"content": response.text}

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
        """Parse raw IEA data into standardized payloads.

        Args:
            raw_data: Raw data from the fetch operation.

        Returns:
            List of standardized payload dictionaries.
        """
        now = datetime.now(timezone.utc)
        records: list[dict[str, Any]] = []

        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict) and "value" in item:
                    payload = self._create_payload(item, now)
                    if payload is not None:
                        records.append(payload)
        elif isinstance(raw_data, dict):
            if "indicators" in raw_data:
                for item in raw_data["indicators"]:
                    payload = self._create_payload(item, now)
                    if payload is not None:
                        records.append(payload)
            elif "value" in raw_data:
                payload = self._create_payload(raw_data, now)
                if payload is not None:
                    records.append(payload)

        if not records:
            logger.error(
                "No parsed records from %s at %s; raw_data=%r",
                self.source_name,
                now.isoformat(),
                raw_data,
            )
            raise ValueError(
                f"No records parsed from {self.source_name} at {now.isoformat()}"
            )

        return records

    def _create_payload(self, data: dict[str, Any], timestamp: datetime) -> dict[str, Any] | None:
        """Create a standardized payload from parsed data."""
        value_raw = data.get("value")
        raw_price = None
        if value_raw is not None:
            try:
                value = float(value_raw)
                if value > 0:
                    raw_price = value
            except (TypeError, ValueError):
                raw_price = None

        if raw_price is None:
            return None

        return {
            "source_name": self.source_name,
            "timestamp_utc": timestamp.isoformat(),
            "commodity": "macro",
            "raw_price": raw_price,
            "raw_currency": "USD",
            "region": data.get("region", "Global"),
            "metadata": {
                "indicator": data.get("indicator"),
                "unit": data.get("unit"),
                "fallback_source": True,
            },
        }

    def _create_mock_payload(self, timestamp: datetime) -> dict[str, Any]:
        """Create a mock payload for testing."""
        return {
            "source_name": self.source_name,
            "timestamp_utc": timestamp.isoformat(),
            "commodity": "macro",
            "raw_price": 75.0,  # Example macro indicator value
            "raw_currency": "USD",
            "region": "Global",
            "metadata": {
                "indicator": "energy_price_index",
                "unit": "index",
                "mock": True,
                "fallback_source": True,
            },
        }


def create_iea_scraper(**kwargs: Any) -> IEAScraper:
    """Create an IEA scraper instance."""
    return IEAScraper(**kwargs)
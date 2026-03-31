"""CCFGroup cotton price scraper for FiberPulse ingestion.

Implements the adapter contract for the CCFGroup fallback price feed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from agents.base_scraper import BaseScraper, ScraperResult, SourceCategory

logger = logging.getLogger(__name__)


class CCFGroupScraper(BaseScraper):
    """Scraper for CCFGroup cotton prices.

    Fetches cotton prices from CCFGroup as a fallback source
    when primary CAI data is unavailable.
    """

    def __init__(
        self,
        source_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the CCFGroup scraper.

        Args:
            source_url: Override the default source URL.
            timeout: Request timeout in seconds.
        """
        self._source_url = source_url or "https://www.ccfgroup.com/data/cotton"
        self._timeout = timeout

    @property
    def source_name(self) -> str:
        """Return the canonical source identifier."""
        return "ccfgroup"

    @property
    def display_name(self) -> str:
        """Return the human-friendly source name."""
        return "CCFGroup Cotton"

    @property
    def source_type(self) -> str:
        """Return the source type."""
        return "spot"

    @property
    def category(self) -> SourceCategory:
        """Return the source category."""
        return SourceCategory.FALLBACK

    @property
    def source_url(self) -> str:
        """Return the source URL."""
        return self._source_url

    async def fetch(self, **kwargs: Any) -> ScraperResult:
        """Fetch data from the CCFGroup source.

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
                    data = {"html": response.text}

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
        """Parse raw CCFGroup data into standardized payloads.

        Args:
            raw_data: Raw data from the fetch operation.

        Returns:
            List of standardized payload dictionaries.
        """
        now = datetime.now(timezone.utc)
        records: list[dict[str, Any]] = []

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
        price_raw = data.get("price")
        try:
            raw_price = float(price_raw)
            if raw_price <= 0:
                return None
        except (TypeError, ValueError):
            return None

        return {
            "source_name": self.source_name,
            "timestamp_utc": timestamp.isoformat(),
            "commodity": "cotton",
            "raw_price": raw_price,
            "raw_currency": data.get("currency", "CNY"),
            "region": data.get("region", "China"),
            "metadata": {
                "grade": data.get("grade"),
                "market": data.get("market"),
                "fallback_source": True,
            },
        }

    def _create_mock_payload(self, timestamp: datetime) -> dict[str, Any]:
        """Create a mock payload for testing."""
        return {
            "source_name": self.source_name,
            "timestamp_utc": timestamp.isoformat(),
            "commodity": "cotton",
            "raw_price": 15800.0,  # Approximate CNY per ton
            "raw_currency": "CNY",
            "region": "China",
            "metadata": {
                "grade": "328",
                "market": "Zhangjiagang",
                "mock": True,
                "fallback_source": True,
            },
        }


def create_ccfgroup_scraper(**kwargs: Any) -> CCFGroupScraper:
    """Create a CCFGroup scraper instance."""
    return CCFGroupScraper(**kwargs)
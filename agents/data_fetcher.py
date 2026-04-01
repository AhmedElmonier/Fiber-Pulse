"""Data fetcher orchestrator for FiberPulse ingestion.

Orchestrates primary source ingestion, normalization, and persistence
with fallback activation when primary feeds fail.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from agents.base_scraper import BaseScraper
from agents.cai_spot_scraper import CAISpotScraper
from agents.ccfgroup_scraper import CCFGroupScraper
from agents.ccfi_mediterranean_scraper import CCFIMediterraneanScraper
from agents.drewry_wci_scraper import DrewryWCIScraper
from agents.fibre2fashion_scraper import Fibre2FashionScraper
from agents.iea_scraper import IEAScraper
from agents.macro_feed_scraper import MacroFeedScraper
from agents.mcx_futures_scraper import MCXFuturesScraper
from agents.normalizer import Normalizer
from agents.source_health import SourceHealthEvaluator, get_evaluator
from models.freight_rate import FreightRate
from models.macro_feed_record import MacroFeedRecord
from models.price_history import PriceHistoryRecord, SourceType
from models.source_health import HealthStatus

if TYPE_CHECKING:
    from db.repository import Repository

logger = logging.getLogger(__name__)


class IngestionResult:
    """Result from an ingestion run.

    Attributes:
        success: Whether the ingestion succeeded.
        records_ingested: Number of records successfully ingested.
        records_failed: Number of records that failed.
        source_name: Name of the source.
        fallback_used: Whether fallback was activated.
        error: Error message if ingestion failed.
        details: Additional details about the ingestion.
    """

    def __init__(
        self,
        success: bool,
        records_ingested: int = 0,
        records_failed: int = 0,
        source_name: str = "",
        fallback_used: bool = False,
        error: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the ingestion result."""
        self.success = success
        self.records_ingested = records_ingested
        self.records_failed = records_failed
        self.source_name = source_name
        self.fallback_used = fallback_used
        self.error = error
        self.details = details or {}
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "records_ingested": self.records_ingested,
            "records_failed": self.records_failed,
            "source_name": self.source_name,
            "fallback_used": self.fallback_used,
            "error": self.error,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class DataFetcher:
    """Orchestrates data ingestion from multiple sources.

    Manages primary and fallback sources, normalizes data,
    persists to database, and tracks source health.
    """

    def __init__(
        self,
        repository: Repository,
        normalizer: Normalizer | None = None,
        health_evaluator: SourceHealthEvaluator | None = None,
    ) -> None:
        """Initialize the data fetcher.

        Args:
            repository: Database repository for persistence.
            normalizer: Optional normalizer instance (creates new if None).
            health_evaluator: Optional health evaluator instance.
        """
        self.repository = repository
        self.normalizer = normalizer or Normalizer()
        self.health_evaluator = health_evaluator or get_evaluator()

        # Primary scrapers
        self.primary_scrapers: dict[str, BaseScraper] = {}

        # Fallback scrapers (keyed by primary source name)
        self.fallback_scrapers: dict[str, BaseScraper] = {}

        # All scrapers by name
        self.all_scrapers: dict[str, BaseScraper] = {}

        # Retry tracking
        self.retry_counts: dict[str, int] = {}

        self._initialize_scrapers()

    def _register_scraper(
        self, scraper: BaseScraper, is_primary: bool = True, primary_for: str | None = None
    ) -> None:
        """Register a scraper in the orchestrator.

        Args:
            scraper: The scraper instance.
            is_primary: Whether this is a primary source.
            primary_for: If fallback, which primary source it's for.
        """
        name = scraper.source_name
        self.all_scrapers[name] = scraper
        if is_primary:
            self.primary_scrapers[name] = scraper
        if primary_for:
            self.fallback_scrapers[primary_for] = scraper

    def _initialize_scrapers(self) -> None:
        """Initialize all configured scrapers."""

        # Primary sources
        self._register_scraper(CAISpotScraper())
        self._register_scraper(MCXFuturesScraper())
        self._register_scraper(CCFIMediterraneanScraper())
        self._register_scraper(DrewryWCIScraper())
        self._register_scraper(MacroFeedScraper("fx_usd_inr"))
        self._register_scraper(MacroFeedScraper("fx_usd_cny"))
        self._register_scraper(MacroFeedScraper("oil_spot"))
        self._register_scraper(MacroFeedScraper("electricity"))

        # Fallback sources
        self._register_scraper(CCFGroupScraper(), is_primary=False, primary_for="cai_spot")
        self._register_scraper(Fibre2FashionScraper(), is_primary=False, primary_for="mcx_futures")
        # Note: DrewryWCIScraper is already registered as primary,
        # but it can also be a fallback for ccfi_med
        drewry = self.all_scrapers["drewry_wci"]
        self.fallback_scrapers["ccfi_med"] = drewry

        # Utility sources (not used for primary price data)
        self.utility_scrapers: dict[str, BaseScraper] = {
            "iea": IEAScraper(),
        }
        self.all_scrapers["iea"] = self.utility_scrapers["iea"]

    async def ingest_source(
        self,
        source_name: str,
        use_fallback: bool = True,
        **kwargs: Any,
    ) -> IngestionResult:
        """Ingest data from a specific source.

        Args:
            source_name: The source to ingest from.
            use_fallback: Whether to use fallback if primary fails.
            **kwargs: Additional parameters for the scraper.

        Returns:
            IngestionResult with details of the operation.
        """
        scraper = self.primary_scrapers.get(source_name)
        if not scraper:
            return IngestionResult(
                success=False,
                source_name=source_name,
                error=f"Unknown source: {source_name}",
            )

        # Attempt primary ingestion
        result = await self._scrape_and_persist(scraper, **kwargs)

        if result.success:
            # Reset retry count on success
            self.retry_counts[source_name] = 0
            return result

        # Primary failed, try fallback chain if enabled
        if use_fallback:
            fallback_chain = await self.health_evaluator.resolve_fallback_chain(
                self.repository, source_name
            )

            # If no chain in DB, try the hardcoded fallback if it exists
            if not fallback_chain:
                hardcoded_fallback = self.fallback_scrapers.get(source_name)
                if hardcoded_fallback:
                    fallback_chain = [hardcoded_fallback.source_name]

            for fallback_name in fallback_chain:
                fallback_scraper = self.all_scrapers.get(fallback_name)
                if fallback_scraper:
                    logger.warning(
                        f"Primary source {source_name} failed, trying fallback {fallback_name}"
                    )
                    fallback_result = await self._scrape_and_persist(
                        fallback_scraper, primary_source_name=source_name, **kwargs
                    )
                    if fallback_result.success:
                        fallback_result.fallback_used = True
                        return fallback_result
                else:
                    logger.error(
                        f"Fallback source {fallback_name} not found in registered scrapers"
                    )

        return result

    async def _scrape_and_persist(
        self,
        scraper: BaseScraper,
        primary_source_name: str | None = None,
        **kwargs: Any,
    ) -> IngestionResult:
        """Scrape data from a source and persist to database.

        Args:
            scraper: The scraper to use.
            primary_source_name: The primary source name if this is a fallback.
            **kwargs: Additional parameters for the scraper.

        Returns:
            IngestionResult with details of the operation.
        """
        source_name = scraper.source_name
        is_fallback = primary_source_name is not None
        target_source_name = primary_source_name or source_name
        last_attempt = datetime.now(UTC)
        logger.info(f"Starting fetch for source: {source_name}, is_fallback: {is_fallback}")

        # 1. Health check before persistence: get current health status of TARGET source
        current_health = await self.repository.get_source_health(target_source_name)
        is_currently_stale = False
        if current_health and current_health.status == HealthStatus.STALE:
            is_currently_stale = True

        try:
            # 2. Scrape the source
            scrape_result = await scraper.scrape(**kwargs)

            if not scrape_result.success:
                logger.error(f"Fetch failed for {source_name}: {scrape_result.error}")
                # Increment retry count for the TARGET source
                self.retry_counts[target_source_name] = (
                    self.retry_counts.get(target_source_name, 0) + 1
                )
                retry_count = self.retry_counts[target_source_name]

                # Update source health
                await self.health_evaluator.update_source_health(
                    repository=self.repository,
                    source_name=target_source_name,
                    ingestion_success=False,
                    last_attempt=last_attempt,
                    fallback_active=is_fallback,
                    retry_count=retry_count,
                )

                return IngestionResult(
                    success=False,
                    source_name=source_name,
                    error=scrape_result.error,
                    details={"retry_count": retry_count},
                )

            logger.info(
                f"Payload received from {source_name}: {len(scrape_result.records)} records"
            )

            # 3. Validate and normalize payloads
            valid_records: list[Any] = []
            failed_payloads: list[tuple[dict[str, Any], str]] = []

            for payload in scrape_result.records:
                # Add source metadata
                if is_fallback:
                    payload["fallback_source"] = scraper.display_name

                # Validate using scraper's logic
                errors = scraper.validate_payload(payload)
                if errors:
                    failed_payloads.append((payload, "; ".join(errors)))
                    continue

                try:
                    # Determine source type
                    source_type_str = scraper.source_type
                    source_type = self._get_source_type(source_type_str)

                    # Build quality flags
                    # If we just successfully scraped from primary, it's NOT stale anymore
                    # But if we are in fallback, we might still consider the PRIMARY stale
                    quality_flags: dict[str, bool | str] = {
                        "stale": is_currently_stale if is_fallback else False,
                        "fallback": is_fallback,
                    }
                    if is_fallback:
                        quality_flags["fallback_source"] = scraper.display_name

                    # Route to appropriate normalization method
                    if source_type_str == "freight":
                        record = self.normalizer.normalize_freight(payload, quality_flags)
                    elif source_type_str == "macro":
                        record = self.normalizer.normalize_macro(payload, quality_flags)
                    else:
                        record = self.normalizer.normalize(payload, source_type, quality_flags)

                    valid_records.append(record)
                except Exception as e:
                    failed_payloads.append((payload, str(e)))

            if failed_payloads:
                logger.warning(
                    f"Normalization partially failed for {source_name}: {len(failed_payloads)} failures"
                )
            else:
                logger.info(
                    f"Normalization success for {source_name}: {len(valid_records)} records"
                )

            # 4. Persist valid records using appropriate repository methods
            ingested_count = 0
            if valid_records:
                try:
                    # Separate price history records for batch insertion
                    price_history_records = [
                        r for r in valid_records if isinstance(r, PriceHistoryRecord)
                    ]
                    if price_history_records:
                        await self.repository.insert_price_records_batch(price_history_records)
                        ingested_count += len(price_history_records)

                    # Persist other types individually
                    for record in valid_records:
                        if isinstance(record, FreightRate):
                            await self.repository.persist_freight_rate(record)
                            ingested_count += 1
                        elif isinstance(record, MacroFeedRecord):
                            await self.repository.persist_macro_feed(record)
                            ingested_count += 1
                        # PriceHistoryRecord already handled in batch

                    logger.info(
                        f"Persistence outcome for {source_name}: {ingested_count} records saved"
                    )
                except Exception as e:
                    logger.error(f"Failed to persist records for {source_name}: {e}")
                    return IngestionResult(
                        success=False,
                        source_name=source_name,
                        error=f"Persistence failed: {e}",
                        details={
                            "records_validated": len(valid_records),
                            "records_failed": len(failed_payloads),
                        },
                    )

            # Reset retry count on success
            self.retry_counts[target_source_name] = 0

            # 5. Update source health after ingest
            health_record = await self.health_evaluator.update_source_health(
                repository=self.repository,
                source_name=target_source_name,
                ingestion_success=True,
                last_attempt=last_attempt,
                fallback_active=is_fallback,
                retry_count=0,
            )

            logger.info(
                f"Source health update for {target_source_name}: status={health_record.status}, "
                f"stale={health_record.status == HealthStatus.STALE}"
            )

            return IngestionResult(
                success=True,
                records_ingested=ingested_count,
                records_failed=len(failed_payloads),
                source_name=source_name,
                fallback_used=is_fallback,
                details={
                    "scrape_metadata": scrape_result.metadata,
                    "failed_payloads": [{"payload": p, "error": e} for p, e in failed_payloads],
                },
            )

        except Exception as e:
            logger.exception(f"Ingestion failed for {source_name}")
            return IngestionResult(
                success=False,
                source_name=source_name,
                error=f"Ingestion error: {e}",
            )

    async def ingest_all_primary(self, **kwargs: Any) -> dict[str, IngestionResult]:
        """Ingest from all primary sources.

        Args:
            **kwargs: Additional parameters for scrapers.

        Returns:
            Dictionary mapping source names to results.
        """
        results: dict[str, IngestionResult] = {}

        for source_name in self.primary_scrapers:
            result = await self.ingest_source(source_name, use_fallback=True, **kwargs)
            results[source_name] = result

        return results

    async def verify_ingestion(self, source_name: str) -> dict[str, Any]:
        """Verify that ingestion succeeded for a source.

        Args:
            source_name: The source to verify.

        Returns:
            Verification details including record counts and health status.
        """
        # Get recent records for this source
        recent_records = await self.repository.get_price_records(
            source_name=source_name,
            limit=10,
        )

        # Get current health status
        health_record = await self.repository.get_source_health(source_name)

        return {
            "source_name": source_name,
            "recent_record_count": len(recent_records),
            "latest_record": recent_records[0].timestamp_utc.isoformat()
            if recent_records
            else None,
            "health_status": health_record.status.value if health_record else "unknown",
            "last_success": health_record.last_success_at.isoformat()
            if health_record and health_record.last_success_at
            else None,
        }

    def _get_source_type(self, source_type_str: str) -> SourceType:
        """Convert source type string to enum.

        Args:
            source_type_str: Source type string from scraper.

        Returns:
            SourceType enum value.
        """
        type_mapping = {
            "spot": SourceType.SPOT,
            "future": SourceType.FUTURE,
            "fallback": SourceType.FALLBACK,
            "macro": SourceType.MACRO,
        }
        return type_mapping.get(source_type_str.lower(), SourceType.SPOT)

    def get_source_status(self, source_name: str) -> dict[str, Any]:
        """Get the current status of a source.

        Args:
            source_name: The source to check.

        Returns:
            Status details for the source.
        """
        return {
            "source_name": source_name,
            "retry_count": self.retry_counts.get(source_name, 0),
            "has_fallback": source_name in self.fallback_scrapers,
        }


class SentimentResult:
    """Result from sentiment scoring of a headline."""

    def __init__(
        self,
        success: bool,
        headline: str = "",
        source_name: str = "",
        sentiment_label: str = "",
        confidence: float = 0.0,
        polarity: float = 0.0,
        matched_keywords: list[str] | None = None,
        error: str | None = None,
    ) -> None:
        self.success = success
        self.headline = headline
        self.source_name = source_name
        self.sentiment_label = sentiment_label
        self.confidence = confidence
        self.polarity = polarity
        self.matched_keywords = matched_keywords or []
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "headline": self.headline,
            "source_name": self.source_name,
            "sentiment_label": self.sentiment_label,
            "confidence": self.confidence,
            "polarity": self.polarity,
            "matched_keywords": self.matched_keywords,
            "error": self.error,
        }


async def score_headline_sentiment(
    repository: Repository,
    headline: str,
    source_name: str,
    timestamp_utc: datetime | None = None,
) -> SentimentResult:
    """Score a headline and persist the sentiment event.

    Args:
        repository: Database repository.
        headline: The headline text to score.
        source_name: Source identifier.
        timestamp_utc: When the headline was published (UTC).

    Returns:
        SentimentResult with scoring outcome.
    """
    from datetime import UTC

    from models.sentiment_event import SentimentEvent, SentimentLabel
    from nlp.keyword_scorer import KeywordScorer

    if timestamp_utc is None:
        timestamp_utc = datetime.now(UTC)

    try:
        scorer = KeywordScorer()
        scoring_result = scorer.score(headline)

        event = SentimentEvent(
            headline=headline,
            source_name=source_name,
            timestamp_utc=timestamp_utc,
            sentiment_score=SentimentLabel(scoring_result.label.value),
            confidence=scoring_result.confidence,
            metadata={
                "polarity": scoring_result.polarity,
                "matched_keywords": scoring_result.matched_keywords,
            },
        )

        await repository.insert_sentiment_event(event)

        return SentimentResult(
            success=True,
            headline=headline,
            source_name=source_name,
            sentiment_label=scoring_result.label.value,
            confidence=scoring_result.confidence,
            polarity=scoring_result.polarity,
            matched_keywords=scoring_result.matched_keywords,
        )

    except Exception as e:
        logger.error(f"Failed to score headline: {e}")
        return SentimentResult(
            success=False,
            headline=headline,
            source_name=source_name,
            error=str(e),
        )


async def process_market_headlines(
    repository: Repository,
    headlines: list[dict[str, Any]],
) -> list[SentimentResult]:
    """Process multiple market headlines and score their sentiment.

    Args:
        repository: Database repository for persistence.
        headlines: List of headline dicts with 'text', 'source', 'timestamp' keys.

    Returns:
        List of SentimentResult for each headline.
    """
    results = []
    for hl in headlines:
        headline_text = hl.get("text", "")
        source = hl.get("source", "unknown")
        raw_timestamp = hl.get("timestamp")

        if raw_timestamp:
            if isinstance(raw_timestamp, str):
                timestamp = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
            else:
                if raw_timestamp.tzinfo is None:
                    timestamp = raw_timestamp.replace(tzinfo=UTC)
                else:
                    timestamp = raw_timestamp
        else:
            timestamp = datetime.now(UTC)

        if not headline_text:
            results.append(
                SentimentResult(
                    success=False,
                    source_name=source,
                    error="Empty headline text",
                )
            )
            continue

        result = await score_headline_sentiment(
            repository,
            headline_text,
            source,
            timestamp,
        )
        results.append(result)

    return results


async def run_ingestion(
    repository: Repository, sources: list[str] | None = None
) -> dict[str, IngestionResult]:
    """Run the ingestion pipeline for specified sources.

    Args:
        repository: Database repository for persistence.
        sources: Optional list of sources to ingest (all primary if None).

    Returns:
        Dictionary mapping source names to results.
    """
    fetcher = DataFetcher(repository=repository)

    if sources:
        results = {}
        for source_name in sources:
            if source_name in fetcher.primary_scrapers:
                result = await fetcher.ingest_source(source_name)
                results[source_name] = result
            else:
                results[source_name] = IngestionResult(
                    success=False,
                    source_name=source_name,
                    error=f"Unknown source: {source_name}",
                )
        return results

    return await fetcher.ingest_all_primary()

"""FiberPulse database repository for persistence operations.

Provides persistence methods for price records, health records, source metadata,
and currency conversion records using async SQLAlchemy.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.schema import (
    Base,
    CurrencyConversion,
    FreightRate,
    IngestionSource,
    MacroFeedRecord,
    PriceHistory,
    SourceHealth,
)
from models.currency_conversion import CurrencyConversionRecord
from models.freight_rate import FreightRate as FreightRateModel
from models.ingestion_source import IngestionSource as IngestionSourceModel
from models.macro_feed_record import MacroFeedRecord as MacroFeedRecordModel
from models.price_history import PriceHistoryRecord, SourceType
from models.source_health import HealthStatus, SourceHealthRecord

if TYPE_CHECKING:
    from collections.abc import Sequence


PRICE_EPSILON = 1e-6


class Repository:
    """Async repository for FiberPulse persistence operations.

    Provides CRUD operations for all FiberPulse entities:
    - PriceHistoryRecord
    - SourceHealthRecord
    - IngestionSource
    - CurrencyConversionRecord
    - FreightRateModel
    - MacroFeedRecordModel
    """

    def __init__(self, database_url: str) -> None:
        """Initialize the repository with a database URL.

        Args:
            database_url: PostgreSQL connection URL (async format).
        """
        # Convert sync URL to async if needed
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def insert_price_record(self, record: PriceHistoryRecord) -> PriceHistory:
        """Insert a price history record.

        Args:
            record: The price history record to insert.

        Returns:
            The inserted database row.
        """
        async with self.async_session() as session:
            db_record = PriceHistory(
                source_name=record.source_name,
                source_type=record.source_type,
                timestamp_utc=record.timestamp_utc,
                commodity=record.commodity,
                region=record.region,
                raw_price=record.raw_price,
                raw_currency=record.raw_currency,
                normalized_usd=record.normalized_usd,
                conversion_rate=record.conversion_rate,
                normalized_at=record.normalized_at,
                quality_flags=record.quality_flags,
                record_metadata=record.metadata,
            )
            session.add(db_record)
            await session.commit()
            await session.refresh(db_record)
            return db_record

    async def persist_freight_rate(self, record: FreightRateModel) -> FreightRate:
        """Persist a logistics freight rate record.

        Args:
            record: The freight rate record to persist.

        Returns:
            The persisted database row.
        """
        async with self.async_session() as session:
            db_record = FreightRate(
                source_name=record.source_name,
                route=record.route,
                timestamp_utc=record.timestamp_utc,
                raw_price=record.raw_price,
                raw_currency=record.raw_currency,
                normalized_usd=record.normalized_usd,
                conversion_rate=record.conversion_rate,
                quality_flags=record.quality_flags,
                record_metadata=record.metadata,
            )
            session.add(db_record)
            await session.commit()
            await session.refresh(db_record)
            return db_record

    async def persist_macro_feed(self, record: MacroFeedRecordModel) -> MacroFeedRecord:
        """Persist a macroeconomic feed record.

        Args:
            record: The macro feed record to persist.

        Returns:
            The persisted database row.
        """
        async with self.async_session() as session:
            db_record = MacroFeedRecord(
                source_name=record.source_name,
                source_type=record.source_type,
                timestamp_utc=record.timestamp_utc,
                commodity=record.commodity,
                raw_price=record.raw_price,
                raw_currency=record.raw_currency,
                normalized_usd=record.normalized_usd,
                conversion_rate=record.conversion_rate,
                normalized_at=record.normalized_at,
                quality_flags=record.quality_flags,
                record_metadata=record.metadata,
            )
            session.add(db_record)
            await session.commit()
            await session.refresh(db_record)
            return db_record

    async def insert_price_records_batch(
        self, records: list[PriceHistoryRecord]
    ) -> list[PriceHistory]:
        """Insert multiple price history records in a batch.

        Args:
            records: List of price history records to insert.

        Returns:
            The inserted database rows.
        """
        async with self.async_session() as session:
            db_records = [
                PriceHistory(
                    source_name=r.source_name,
                    source_type=r.source_type,
                    timestamp_utc=r.timestamp_utc,
                    commodity=r.commodity,
                    region=r.region,
                    raw_price=r.raw_price,
                    raw_currency=r.raw_currency,
                    normalized_usd=r.normalized_usd,
                    conversion_rate=r.conversion_rate,
                    normalized_at=r.normalized_at,
                    quality_flags=r.quality_flags,
                    record_metadata=r.metadata,
                )
                for r in records
            ]
            session.add_all(db_records)
            await session.commit()
            for db_record in db_records:
                await session.refresh(db_record)
            return db_records

    async def get_price_records(
        self,
        source_name: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[PriceHistory]:
        """Query price history records with optional filters.

        Args:
            source_name: Filter by source name.
            start_time: Filter records after this time.
            end_time: Filter records before this time.
            limit: Maximum number of records to return.

        Returns:
            List of matching price history records.
        """
        async with self.async_session() as session:
            query = select(PriceHistory)

            if source_name:
                query = query.where(PriceHistory.source_name == source_name)
            if start_time:
                query = query.where(PriceHistory.timestamp_utc >= start_time)
            if end_time:
                query = query.where(PriceHistory.timestamp_utc <= end_time)

            query = query.order_by(PriceHistory.timestamp_utc.desc()).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_normalized_records(
        self,
        source_types: list[str] | None = None,
        source_name: str | None = None,
        source_names: list[str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """Query across multiple record types (price history, freight, macro) using a unified interface.

        Args:
            source_types: List of source types to include ('spot', 'future', 'freight', 'macro').
            source_name: Filter by single source name.
            source_names: Filter by multiple source names.
            start_time: Filter records after this time.
            end_time: Filter records before this time.
            limit: Maximum number of records to return.

        Returns:
            Aggregated list of normalized records.
        """
        async with self.async_session() as session:
            results = []
            
            names_filter = source_names or ([source_name] if source_name else None)

            # 1. Query PriceHistory (spot, future, macro if in this table)
            if not source_types or any(t in source_types for t in ["spot", "future", "macro"]):
                query = select(PriceHistory)
                if names_filter:
                    query = query.where(PriceHistory.source_name.in_(names_filter))
                if start_time:
                    query = query.where(PriceHistory.timestamp_utc >= start_time)
                if end_time:
                    query = query.where(PriceHistory.timestamp_utc <= end_time)
                if source_types:
                    relevant_types = [SourceType[t.upper()] for t in source_types if t in ["spot", "future", "macro"]]
                    if relevant_types:
                        query = query.where(PriceHistory.source_type.in_(relevant_types))
                
                query = query.order_by(PriceHistory.timestamp_utc.desc()).limit(limit)
                res = await session.execute(query)
                results.extend(res.scalars().all())

            # 2. Query FreightRate
            if not source_types or "freight" in source_types:
                query = select(FreightRate)
                if names_filter:
                    query = query.where(FreightRate.source_name.in_(names_filter))
                if start_time:
                    query = query.where(FreightRate.timestamp_utc >= start_time)
                if end_time:
                    query = query.where(FreightRate.timestamp_utc <= end_time)
                
                query = query.order_by(FreightRate.timestamp_utc.desc()).limit(limit)
                res = await session.execute(query)
                results.extend(res.scalars().all())

            # 3. Query MacroFeedRecord (if stored separately)
            if not source_types or "macro" in source_types:
                query = select(MacroFeedRecord)
                if names_filter:
                    query = query.where(MacroFeedRecord.source_name.in_(names_filter))
                if start_time:
                    query = query.where(MacroFeedRecord.timestamp_utc >= start_time)
                if end_time:
                    query = query.where(MacroFeedRecord.timestamp_utc <= end_time)
                
                query = query.order_by(MacroFeedRecord.timestamp_utc.desc()).limit(limit)
                res = await session.execute(query)
                results.extend(res.scalars().all())

            # Sort aggregated results by timestamp descending
            results.sort(key=lambda x: x.timestamp_utc, reverse=True)
            return results[:limit]

    async def get_records_by_health_status(
        self,
        status: str,
        limit: int = 100
    ) -> list[Any]:
        """Query records filtered by the health status of their source.

        Args:
            status: Health status to filter by ('live', 'stale', 'degraded', 'failed').
            limit: Maximum number of records to return.

        Returns:
            List of normalized records from sources matching the status.
        """
        # First get sources with this status
        async with self.async_session() as session:
            health_query = select(SourceHealth).where(SourceHealth.status == HealthStatus(status))
            health_res = await session.execute(health_query)
            source_names = [h.source_name for h in health_res.scalars().all()]
            
            if not source_names:
                return []
                
            # Then get records for these sources
            return await self.get_normalized_records(source_names=source_names, limit=limit)

    async def update_source_health(self, record: SourceHealthRecord) -> SourceHealth:
        """Update or insert a source health record.

        Args:
            record: The source health record to update.

        Returns:
            The upserted database row.
        """
        return await self.upsert_source_health(record)

    async def upsert_source_health(self, record: SourceHealthRecord) -> SourceHealth:
        """Upsert a source health record.

        Creates a new record or updates an existing one for the source.

        Args:
            record: The source health record to upsert.

        Returns:
            The upserted database row.
        """
        async with self.async_session() as session:
            stmt = insert(SourceHealth).values(
                source_name=record.source_name,
                status=record.status,
                last_success_at=record.last_success_at,
                last_checked_at=record.last_checked_at,
                fallback_active=record.fallback_active,
                stale_duration_minutes=record.stale_duration_minutes,
                remarks=record.remarks,
                details=record.details,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["source_name"],
                set_={
                    "status": stmt.excluded.status,
                    "last_success_at": stmt.excluded.last_success_at,
                    "last_checked_at": stmt.excluded.last_checked_at,
                    "fallback_active": stmt.excluded.fallback_active,
                    "stale_duration_minutes": stmt.excluded.stale_duration_minutes,
                    "remarks": stmt.excluded.remarks,
                    "details": stmt.excluded.details,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            result = await session.execute(stmt)
            await session.commit()
            # Fetch the upserted record
            query = select(SourceHealth).where(SourceHealth.source_name == record.source_name)
            fetched = await session.execute(query)
            return fetched.scalar_one()

    async def get_source_health(self, source_name: str) -> SourceHealth | None:
        """Get the health record for a source.

        Args:
            source_name: The source name to look up.

        Returns:
            The source health record, or None if not found.
        """
        async with self.async_session() as session:
            query = select(SourceHealth).where(SourceHealth.source_name == source_name)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_all_source_health(self) -> list[SourceHealth]:
        """Get all source health records.

        Returns:
            List of all source health records.
        """
        async with self.async_session() as session:
            query = select(SourceHealth)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_sources_by_status(self, status: HealthStatus) -> list[SourceHealth]:
        """Get source health records filtered by status.

        Args:
            status: The health status to filter by.

        Returns:
            List of matching source health records.
        """
        async with self.async_session() as session:
            query = select(SourceHealth).where(SourceHealth.status == status)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def upsert_ingestion_source(self, source: IngestionSourceModel) -> IngestionSource:
        """Upsert an ingestion source configuration.

        Args:
            source: The ingestion source to upsert.

        Returns:
            The upserted database row.
        """
        async with self.async_session() as session:
            stmt = insert(IngestionSource).values(
                source_name=source.source_name,
                display_name=source.display_name,
                priority=source.priority,
                source_url=source.source_url,
                category=source.category,
                active=source.active,
                fallback_to=source.fallback_to,
                config=source.config,
            )
            stmt = stmt.on_conflict_do_update(
                constraint="pk_ingestion_source",
                set_={
                    "display_name": stmt.excluded.display_name,
                    "priority": stmt.excluded.priority,
                    "source_url": stmt.excluded.source_url,
                    "category": stmt.excluded.category,
                    "active": stmt.excluded.active,
                    "fallback_to": stmt.excluded.fallback_to,
                    "config": stmt.excluded.config,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            result = await session.execute(stmt)
            await session.commit()
            query = select(IngestionSource).where(
                IngestionSource.source_name == source.source_name
            )
            fetched = await session.execute(query)
            return fetched.scalar_one()

    async def get_ingestion_source(self, source_name: str) -> IngestionSource | None:
        """Get an ingestion source by name.

        Args:
            source_name: The source name to look up.

        Returns:
            The ingestion source, or None if not found.
        """
        async with self.async_session() as session:
            query = select(IngestionSource).where(IngestionSource.source_name == source_name)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_active_sources(self) -> list[IngestionSource]:
        """Get all active ingestion sources.

        Returns:
            List of active ingestion sources.
        """
        async with self.async_session() as session:
            query = select(IngestionSource).where(IngestionSource.active == True)
            query = query.order_by(IngestionSource.priority)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def insert_currency_conversion(self, record: CurrencyConversionRecord) -> CurrencyConversion:
        """Insert a currency conversion rate record.

        Args:
            record: The currency conversion record to insert.

        Returns:
            The inserted database row.
        """
        async with self.async_session() as session:
            db_record = CurrencyConversion(
                currency=record.currency,
                rate_to_usd=record.rate_to_usd,
                rate_timestamp=record.rate_timestamp,
                source_name=record.source_name,
                retrieved_at=record.retrieved_at,
                rate_metadata=record.metadata,
            )
            session.add(db_record)
            await session.commit()
            await session.refresh(db_record)
            return db_record

    async def get_latest_rate(self, currency: str) -> CurrencyConversion | None:
        """Get the latest conversion rate for a currency.

        Args:
            currency: The currency code to look up.

        Returns:
            The latest currency conversion record, or None if not found.
        """
        async with self.async_session() as session:
            query = (
                select(CurrencyConversion)
                .where(CurrencyConversion.currency == currency.upper())
                .order_by(CurrencyConversion.rate_timestamp.desc())
                .limit(1)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def check_price_duplicate(
        self, source_name: str, timestamp_utc: datetime, raw_price: float
    ) -> bool:
        """Check if a price record already exists (duplicate detection).

        Args:
            source_name: The source name.
            timestamp_utc: The timestamp.
            raw_price: The raw price value.

        Returns:
            True if a duplicate exists, False otherwise.
        """
        async with self.async_session() as session:
            query = select(PriceHistory).where(
                PriceHistory.source_name == source_name,
                PriceHistory.timestamp_utc == timestamp_utc,
                func.abs(PriceHistory.raw_price - raw_price) < PRICE_EPSILON,
            )
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None

    async def close(self) -> None:
        """Close the database connection."""
        await self.engine.dispose()
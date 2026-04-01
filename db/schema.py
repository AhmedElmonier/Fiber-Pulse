"""FiberPulse database schema definitions.

Defines PostgreSQL tables for price_history, source_health, ingestion_source,
and currency_conversion using SQLAlchemy.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Import enums from models
from models.ingestion_source import SourceCategory
from models.price_history import SourceType
from models.sentiment_event import SentimentLabel
from models.source_health import HealthStatus

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class for all FiberPulse database models."""

    metadata = metadata


class PriceHistory(Base):
    """Table for storing normalized price history records.

    Each record represents a canonical price point from a configured ingestion source,
    normalized to USD with full audit metadata.
    """

    __tablename__ = "price_history"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    commodity: Mapped[str] = mapped_column(String(50), nullable=False, default="cotton")
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_price: Mapped[float] = mapped_column(Float, nullable=False)
    raw_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    normalized_usd: Mapped[float] = mapped_column(Float, nullable=False)
    conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    quality_flags: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    record_metadata: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, name="metadata"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Unique constraint to prevent duplicate price records
    __table_args__ = (
        Index(
            "uq_price_history_source_timestamp_price",
            "source_name",
            "timestamp_utc",
            "raw_price",
            unique=True,
        ),
    )


class FreightRate(Base):
    """Table for storing normalized logistics freight rates.

    Each record represents a freight rate for a specific route and source,
    normalized to USD with full provenance.
    """

    __tablename__ = "freight_rates"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    route: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    raw_price: Mapped[float] = mapped_column(Float, nullable=False)
    raw_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    normalized_usd: Mapped[float] = mapped_column(Float, nullable=False)
    conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_flags: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    record_metadata: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, name="metadata"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (Index("ix_freight_rates_source_timestamp", "source_name", "timestamp_utc"),)


class MacroFeedRecord(Base):
    """Table for storing macroeconomic feed records.

    Stores normalized values for FX, oil, electricity, and other macro indicators.
    """

    __tablename__ = "macro_feed_records"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType), nullable=False, default=SourceType.MACRO
    )
    timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    commodity: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    raw_price: Mapped[float] = mapped_column(Float, nullable=False)
    raw_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    normalized_usd: Mapped[float] = mapped_column(Float, nullable=False)
    conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    quality_flags: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    record_metadata: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, name="metadata"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_macro_feed_records_source_timestamp", "source_name", "timestamp_utc"),
    )


class SourceHealth(Base):
    """Table for tracking the operational health state of ingestion sources.

    Each record represents the current health status of a configured data source,
    including fallback activation state and staleness tracking.
    """

    __tablename__ = "source_health"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    status: Mapped[HealthStatus] = mapped_column(
        Enum(HealthStatus), nullable=False, default=HealthStatus.LIVE, index=True
    )
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    fallback_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stale_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class IngestionSource(Base):
    """Table for storing configured ingestion source metadata.

    Each record represents a data source configuration including priority,
    category, and fallback relationships.
    """

    __tablename__ = "ingestion_source"

    source_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[SourceCategory] = mapped_column(
        Enum(SourceCategory), nullable=False, default=SourceCategory.PRIMARY
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fallback_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class CurrencyConversion(Base):
    """Table for storing currency exchange rate records.

    Each record represents a currency-to-USD conversion rate at a specific point in time,
    used for normalizing raw price values to USD.
    """

    __tablename__ = "currency_conversion"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    rate_to_usd: Mapped[float] = mapped_column(Float, nullable=False)
    rate_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rate_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True, name="metadata")

    # Index for efficient rate lookups by currency and timestamp
    __table_args__ = (
        Index("ix_currency_conversion_currency_timestamp", "currency", "rate_timestamp"),
    )


class AlertLogDB(Base):
    """Table for capturing all notifications sent to Telegram users."""

    __tablename__ = "alert_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    instrument_name: Mapped[str] = mapped_column(String(100), nullable=False)
    trigger_reason: Mapped[str] = mapped_column(String(100), nullable=False)
    target_chat_id: Mapped[int] = mapped_column(Integer, nullable=False)
    message_payload: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (Index("idx_alert_log_suppression", "instrument_name", "timestamp"),)


class BotCommandLogDB(Base):
    """Table for tracking Telegram bot command interactions."""

    __tablename__ = "bot_command_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    command_name: Mapped[str] = mapped_column(String(50), nullable=False)
    arguments: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (Index("idx_bot_command_user", "user_id", "timestamp"),)


class ForecastDB(Base):
    """Table for storing price forecasts with confidence intervals."""

    __tablename__ = "forecasts"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    target_source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    target_timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    lower_bound: Mapped[float] = mapped_column(Float, nullable=False)
    upper_bound: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_level: Mapped[float] = mapped_column(Float, nullable=False, default=0.95)
    model_version: Mapped[str] = mapped_column(
        String(100), nullable=False, default="baseline-1.0.0"
    )
    is_decayed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_forecasts_target_timestamp", "target_source", "target_timestamp_utc"),
    )


class HistoricalOnboardingLogDB(Base):
    """Table for tracking CSV ingestion runs."""

    __tablename__ = "historical_onboarding_log"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    onboarding_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    __table_args__ = (Index("ix_historical_onboarding_timestamp", "timestamp_utc"),)


class SentimentEvent(Base):
    """Table for storing sentiment-scored market headlines."""

    __tablename__ = "sentiment_events"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    sentiment_score: Mapped[SentimentLabel] = mapped_column(Enum(SentimentLabel), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    event_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )


def create_tables(database_url: str) -> None:
    """Create all database tables.

    Args:
        database_url: PostgreSQL connection URL.
    """
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    # Allow running this module directly to create tables
    import os

    from dotenv import load_dotenv

    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        create_tables(db_url)
        print("Tables created successfully")
    else:
        print("DATABASE_URL environment variable not set")

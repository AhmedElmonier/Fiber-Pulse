"""Source health model for FiberPulse ingestion.

Defines the SourceHealthRecord entity representing the operational health state
of a configured ingestion source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class HealthStatus(str, Enum):
    """Health status of an ingestion source based on 48-hour threshold.

    Values:
        LIVE: Source is actively providing fresh data (within 48h).
        STALE: Data age exceeds 48-hour threshold but primary source is still attempted.
        DEGRADED: Primary source is stale or failing, but fallback is successfully active.
        FAILED: Maximum retry attempts exceeded without any recovery.
        DEAD: Source has been permanently inactive or disabled.
    """

    LIVE = "live"
    STALE = "stale"
    DEGRADED = "degraded"
    FAILED = "failed"
    DEAD = "dead"


@dataclass
class SourceHealthRecord:
    """Represents the operational health state of a configured ingestion source.

    Tracks transitions between health states (live, stale, etc.) and provides
    diagnostic metadata for the ingestion orchestrator.

    Attributes:
        id (UUID): Unique primary key for the health record.
        source_name (str): Canonical identifier for the data source.
        status (HealthStatus): Current health state from the state machine.
        last_success_at (datetime, optional): Timestamp of the last successful fetch (UTC).
        last_checked_at (datetime): Most recent health evaluation or attempt time (UTC).
        fallback_active (bool): True if fallback data is currently being ingested for this source.
        stale_duration_minutes (int, optional): Calculated minutes since last success.
        remarks (str, optional): Human-readable summary of the current health state.
        details (dict): Diagnostic metadata (retry counts, error logs, fallback source).
        created_at (datetime, optional): Insertion timestamp.
        updated_at (datetime, optional): Last update timestamp.
    """

    id: UUID = field(default_factory=uuid4)
    source_name: str = ""
    status: HealthStatus = HealthStatus.LIVE
    last_success_at: datetime | None = None
    last_checked_at: datetime | None = None
    fallback_active: bool = False
    stale_duration_minutes: int | None = None
    remarks: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate required fields after initialization.

        Raises:
            ValueError: If source_name or last_checked_at is missing.
        """
        if not self.source_name:
            raise ValueError("source_name is required")
        if self.last_checked_at is None:
            raise ValueError("last_checked_at is required")

    def to_dict(self) -> dict[str, Any]:
        """Convert the record to a dictionary representation.

        Useful for monitoring dashboards and health check APIs.

        Returns:
            A dictionary containing health state and diagnostic data.
        """
        return {
            "id": str(self.id),
            "source_name": self.source_name,
            "status": self.status.value,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_checked_at": self.last_checked_at.isoformat() if self.last_checked_at else None,
            "fallback_active": self.fallback_active,
            "stale_duration_minutes": self.stale_duration_minutes,
            "remarks": self.remarks,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
"""Historical onboarding log model for FiberPulse CLI ingestion.

Defines the HistoricalOnboardingLog entity tracking CSV ingestion runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class OnboardingStatus(str, Enum):
    """Status of a historical data onboarding run."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class HistoricalOnboardingLog:
    """A log entry for a CSV ingestion run.

    Attributes:
        id: Unique primary key.
        file_name: Name of the ingested file.
        timestamp_utc: When ingestion occurred (UTC).
        record_count: Number of records successfully ingested.
        status: Ingestion outcome (success, failed, partial).
        error_summary: Details of validation failures (nullable).
        metadata: Ingestion parameters and user who triggered it.
    """

    file_name: str
    timestamp_utc: datetime
    record_count: int
    status: OnboardingStatus
    id: UUID = field(default_factory=uuid4)
    error_summary: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        if not self.file_name:
            raise ValueError("file_name is required")
        if self.record_count < 0:
            raise ValueError("record_count must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        """Convert log entry to dictionary representation."""
        return {
            "id": str(self.id),
            "file_name": self.file_name,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None,
            "record_count": self.record_count,
            "status": self.status.value,
            "error_summary": self.error_summary,
            "metadata": self.metadata,
        }

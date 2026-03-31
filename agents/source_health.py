"""Source health evaluation agent for FiberPulse ingestion.

Evaluates source state transitions and determines live, stale,
degraded, or failed statuses based on ingestion outcomes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from models.source_health import HealthStatus, SourceHealthRecord

if TYPE_CHECKING:
    from db.repository import Repository


# Default thresholds for health evaluation per Phase 2 spec (48 hours)
DEFAULT_STALE_THRESHOLD_MINUTES = 2880  # 48 hours
DEFAULT_FAILED_THRESHOLD_MINUTES = 5760  # 96 hours
DEFAULT_MAX_RETRY_ATTEMPTS = 3


class SourceHealthEvaluator:
    """Evaluates and updates source health state using a state machine.

    Implements health logic for FiberPulse ingestion sources, determining status
    transitions based on data freshness (48-hour threshold) and attempt outcomes.

    The state machine handles:
    - LIVE: Fresh data received recently.
    - STALE: Data age exceeds 48-hour threshold.
    - DEGRADED: Primary source is stale/failed, but fallback is successfully active.
    - FAILED: Max retries exceeded or source completely non-responsive.

    Attributes:
        stale_threshold_minutes (int): Minutes before data is marked STALE.
        failed_threshold_minutes (int): Minutes before data is marked FAILED.
        max_retry_attempts (int): Maximum retry limit for ingestion.
    """

    def __init__(
        self,
        stale_threshold_minutes: int = DEFAULT_STALE_THRESHOLD_MINUTES,
        failed_threshold_minutes: int = DEFAULT_FAILED_THRESHOLD_MINUTES,
        max_retry_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS,
    ) -> None:
        """Initialize the health evaluator with specific thresholds.

        Args:
            stale_threshold_minutes: Minutes without data before marking stale (default 48h).
            failed_threshold_minutes: Minutes without data before marking failed (default 96h).
            max_retry_attempts: Maximum retry attempts before triggering failure status.
        """
        self.stale_threshold_minutes = stale_threshold_minutes
        self.failed_threshold_minutes = failed_threshold_minutes
        self.max_retry_attempts = max_retry_attempts

    async def resolve_fallback_chain(
        self, repository: "Repository", source_name: str
    ) -> list[str]:
        """Resolve the chain of fallback sources for a given primary source.

        Queries the ingestion source configuration to find linked fallbacks,
        ensuring no circular dependencies exist in the chain.

        Args:
            repository: Database repository to query source configurations.
            source_name: The primary source name to resolve fallbacks for.

        Returns:
            An ordered list of fallback source names (e.g. ['drewry_wci']).
        """
        chain: list[str] = []
        visited: set[str] = {source_name}
        current_name = source_name

        while True:
            source_config = await repository.get_ingestion_source(current_name)
            if not source_config or not source_config.fallback_to:
                break
            
            fallback_name = source_config.fallback_to
            if fallback_name in visited:
                # Circular fallback detected
                break
                
            chain.append(fallback_name)
            visited.add(fallback_name)
            current_name = fallback_name

        return chain

    def get_stale_duration_minutes(self, last_success: datetime | None) -> int | None:
        """Calculate elapsed time in minutes since the last successful ingestion.

        Args:
            last_success: Timestamp of the most recent successful data fetch (UTC).

        Returns:
            Minutes since last success, or None if no success has been recorded.
        """
        if last_success is None:
            return None
        now = datetime.now(timezone.utc)
        time_since_success = now - last_success
        return int(time_since_success.total_seconds() / 60)

    def evaluate_source_health(
        self,
        current_record: SourceHealthRecord | None,
        last_success: datetime | None,
        last_attempt: datetime | None,
        retry_count: int,
        fallback_active: bool = False,
    ) -> tuple[HealthStatus, int | None, str | None]:
        """Evaluate the current health status of a source based on history and thresholds.

        Applies the logic for state transitions (e.g. live -> stale) and generates
        human-readable remarks describing the health state.

        Args:
            current_record: Most recent health record from database.
            last_success: Timestamp of last successful ingestion.
            last_attempt: Timestamp of the current/last ingestion attempt.
            retry_count: Number of consecutive failed attempts.
            fallback_active: Flag indicating if fallback source is providing data.

        Returns:
            A tuple of (HealthStatus, stale_duration_minutes, remarks).
        """
        now = datetime.now(timezone.utc)
        stale_minutes = self.get_stale_duration_minutes(last_success)

        # 1. Check for failed state (highest priority)
        if retry_count >= self.max_retry_attempts:
            if last_success is None:
                return HealthStatus.FAILED, stale_minutes, "Exceeded retry limits without any successful ingestion"
            if stale_minutes is not None and stale_minutes >= self.failed_threshold_minutes:
                return HealthStatus.FAILED, stale_minutes, f"Source dead/failed (Stale: {stale_minutes} min)"

        # 2. Check for degraded state (fallback active)
        if fallback_active:
            # Transition stale -> degraded if fallback is used
            if current_record and current_record.status == HealthStatus.STALE:
                return HealthStatus.DEGRADED, stale_minutes, "Fallback activated due to stale primary"
            return HealthStatus.DEGRADED, stale_minutes, "Fallback data source active"

        # 3. Check for recovery
        if current_record and current_record.status in (HealthStatus.STALE, HealthStatus.DEGRADED, HealthStatus.FAILED):
            if stale_minutes is not None and stale_minutes < self.stale_threshold_minutes:
                # If we just had a successful primary ingest, we are LIVE again
                if not fallback_active:
                    return HealthStatus.LIVE, stale_minutes, "Source recovered"

        # 4. Check for stale state (48 hours)
        if stale_minutes is not None and stale_minutes >= self.stale_threshold_minutes:
            remarks = f"Data is stale (> {self.stale_threshold_minutes} min old)"
            return HealthStatus.STALE, stale_minutes, remarks

        # 5. Default to live if we have recent success
        if last_attempt is None:
            return HealthStatus.LIVE, None, "Awaiting initial ingestion"
        
        return HealthStatus.LIVE, stale_minutes, None

    def activate_fallback(
        self, 
        source_name: str, 
        fallback_source: str,
        current_record: SourceHealthRecord | None
    ) -> SourceHealthRecord:
        """Create a new health record marking the activation of a fallback source.

        Args:
            source_name: The primary source name undergoing fallback.
            fallback_source: The identifier of the fallback source being used.
            current_record: Current health state of the primary source.

        Returns:
            A new SourceHealthRecord in DEGRADED status with fallback metadata.
        """
        now = datetime.now(timezone.utc)
        last_success = current_record.last_success_at if current_record else None
        stale_minutes = self.get_stale_duration_minutes(last_success)

        details = dict(current_record.details) if current_record and current_record.details else {}
        details["fallback_activated_at"] = now.isoformat()
        details["fallback_source_name"] = fallback_source

        return SourceHealthRecord(
            source_name=source_name,
            status=HealthStatus.DEGRADED,
            last_success_at=last_success,
            last_checked_at=now,
            fallback_active=True,
            stale_duration_minutes=stale_minutes,
            remarks=f"Fallback activated using {fallback_source}",
            details=details
        )

    def compute_health_transition(
        self,
        source_name: str,
        current_record: SourceHealthRecord | None,
        ingestion_success: bool,
        last_attempt: datetime,
        fallback_active: bool = False,
        retry_count: int = 0,
    ) -> SourceHealthRecord:
        """Compute the next health record state based on ingestion outcome.

        Wraps evaluate_source_health to produce a full model instance ready
        for persistence.

        Args:
            source_name: Canonical source identifier.
            current_record: Existing health state for this source.
            ingestion_success: Whether the current ingestion attempt succeeded.
            last_attempt: Timestamp of the ingestion attempt (UTC).
            fallback_active: Flag for fallback usage.
            retry_count: Number of consecutive ingestion failures.

        Returns:
            A populated SourceHealthRecord reflecting the new state.
        """
        # Determine last success time
        if ingestion_success:
            last_success = last_attempt
        elif current_record:
            last_success = current_record.last_success_at
        else:
            last_success = None

        # Evaluate health
        status, stale_minutes, remarks = self.evaluate_source_health(
            current_record=current_record,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=retry_count,
            fallback_active=fallback_active,
        )

        # Build details
        details: dict[str, Any] = {}
        if current_record and current_record.details:
            details = dict(current_record.details)
        details["retry_count"] = retry_count
        details["last_attempt"] = last_attempt.isoformat()
        if fallback_active:
            details["fallback_active"] = True

        return SourceHealthRecord(
            source_name=source_name,
            status=status,
            last_success_at=last_success,
            last_checked_at=datetime.now(timezone.utc),
            fallback_active=fallback_active,
            stale_duration_minutes=stale_minutes,
            remarks=remarks,
            details=details,
        )

    async def update_source_health(
        self,
        repository: "Repository",
        source_name: str,
        ingestion_success: bool,
        last_attempt: datetime,
        fallback_active: bool = False,
        retry_count: int = 0,
    ) -> SourceHealthRecord:
        """Evaluate, transition, and persist the health state of a source.

        Main entry point for health tracking after an ingestion attempt.

        Args:
            repository: Database repository for I/O.
            source_name: Canonical source identifier.
            ingestion_success: Outcome of the ingestion fetch/parse.
            last_attempt: Timestamp of the attempt.
            fallback_active: Whether a fallback was used.
            retry_count: Current failure streak.

        Returns:
            The newly persisted SourceHealthRecord.
        """
        # Get current record
        current = await repository.get_source_health(source_name)
        current_record = None
        if current:
            # Convert SQLAlchemy object to dataclass if needed, 
            # though repository.get_source_health might already return it.
            # Assuming it returns SourceHealthRecord dataclass based on Phase 1 tasks.
            current_record = current

        # Compute new health
        new_record = self.compute_health_transition(
            source_name=source_name,
            current_record=current_record,
            ingestion_success=ingestion_success,
            last_attempt=last_attempt,
            fallback_active=fallback_active,
            retry_count=retry_count,
        )

        # Persist to database
        await repository.upsert_source_health(new_record)

        return new_record



# Global evaluator instance
_evaluator: SourceHealthEvaluator | None = None


def get_evaluator() -> SourceHealthEvaluator:
    """Get the global health evaluator instance."""
    global _evaluator
    if _evaluator is None:
        _evaluator = SourceHealthEvaluator()
    return _evaluator


def reset_evaluator() -> None:
    """Reset the global health evaluator instance."""
    global _evaluator
    _evaluator = None
"""Unit tests for FiberPulse source health evaluation.

Tests health state transitions, fallback activation, and stale detection
for the SourceHealthEvaluator.
"""

from datetime import datetime, timedelta, timezone

import pytest

from agents.source_health import (
    DEFAULT_FAILED_THRESHOLD_MINUTES,
    DEFAULT_MAX_RETRY_ATTEMPTS,
    DEFAULT_STALE_THRESHOLD_MINUTES,
    SourceHealthEvaluator,
    get_evaluator,
    reset_evaluator,
)
from models.source_health import HealthStatus, SourceHealthRecord


class TestHealthStatusTransitions:
    """Tests for health status state transitions."""

    @pytest.fixture
    def evaluator(self) -> SourceHealthEvaluator:
        """Create a fresh evaluator for each test."""
        return SourceHealthEvaluator()

    @pytest.fixture
    def now(self) -> datetime:
        """Get current UTC time."""
        return datetime.now(timezone.utc)

    def test_new_source_starts_as_live(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test that a source with no prior attempts is marked as live."""
        status, stale_mins, remarks = evaluator.evaluate_source_health(
            current_record=None,
            last_success=None,
            last_attempt=None,
            retry_count=0,
        )
        assert status == HealthStatus.LIVE
        assert stale_mins is None
        assert "Awaiting initial ingestion" in (remarks or "")

    def test_live_remains_live_with_recent_success(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test that a source with recent success stays live."""
        last_success = now - timedelta(minutes=30)
        last_attempt = now

        status, stale_mins, remarks = evaluator.evaluate_source_health(
            current_record=None,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=0,
        )
        assert status == HealthStatus.LIVE
        assert stale_mins == 30

    def test_live_to_stale_when_data_age_exceeds_threshold(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test transition from live to stale when data becomes old."""
        last_success = now - timedelta(minutes=DEFAULT_STALE_THRESHOLD_MINUTES + 10)
        last_attempt = now

        status, stale_mins, remarks = evaluator.evaluate_source_health(
            current_record=None,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=0,
        )
        assert status == HealthStatus.STALE
        assert stale_mins == DEFAULT_STALE_THRESHOLD_MINUTES + 10
        assert "min old" in (remarks or "")

    def test_stale_to_degraded_when_fallback_activated(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test transition from stale to degraded when fallback is used."""
        last_success = now - timedelta(minutes=DEFAULT_STALE_THRESHOLD_MINUTES + 10)
        last_attempt = now

        # Create a current record in STALE state
        current_record = SourceHealthRecord(
            source_name="cai_spot",
            status=HealthStatus.STALE,
            last_success_at=last_success,
            last_checked_at=now,
            stale_duration_minutes=DEFAULT_STALE_THRESHOLD_MINUTES + 10,
        )

        status, stale_mins, remarks = evaluator.evaluate_source_health(
            current_record=current_record,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=0,
            fallback_active=True,
        )
        assert status == HealthStatus.DEGRADED
        assert "Fallback" in (remarks or "")

    def test_degraded_to_live_when_primary_recovered(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test transition from degraded back to live when primary source recovers."""
        # Create a current record in DEGRADED state
        current_record = SourceHealthRecord(
            source_name="cai_spot",
            status=HealthStatus.DEGRADED,
            last_success_at=now - timedelta(minutes=30),
            last_checked_at=now - timedelta(minutes=5),
            fallback_active=True,
        )

        # Recent successful ingestion
        last_success = now - timedelta(minutes=10)
        last_attempt = now

        status, stale_mins, remarks = evaluator.evaluate_source_health(
            current_record=current_record,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=0,
            fallback_active=False,
        )
        assert status == HealthStatus.LIVE
        assert "recovered" in (remarks or "").lower()

    def test_stale_to_live_when_recent_success(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test transition from stale back to live with recent success."""
        # Create a current record in STALE state
        current_record = SourceHealthRecord(
            source_name="cai_spot",
            status=HealthStatus.STALE,
            last_success_at=now - timedelta(minutes=120),
            last_checked_at=now - timedelta(minutes=5),
            stale_duration_minutes=120,
        )

        # Recent successful ingestion within threshold
        last_success = now - timedelta(minutes=30)
        last_attempt = now

        status, stale_mins, remarks = evaluator.evaluate_source_health(
            current_record=current_record,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=0,
        )
        assert status == HealthStatus.LIVE

    def test_any_to_failed_when_retry_limits_exceeded(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test transition to failed when retry limits are exceeded."""
        last_attempt = now

        status, stale_mins, remarks = evaluator.evaluate_source_health(
            current_record=None,
            last_success=None,
            last_attempt=last_attempt,
            retry_count=DEFAULT_MAX_RETRY_ATTEMPTS,
        )
        assert status == HealthStatus.FAILED
        assert "retry limits" in (remarks or "").lower()

    def test_failed_state_with_stale_data(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test failed state when source had previous success but now stale."""
        last_success = now - timedelta(minutes=DEFAULT_FAILED_THRESHOLD_MINUTES + 60)
        last_attempt = now

        status, stale_mins, remarks = evaluator.evaluate_source_health(
            current_record=None,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=DEFAULT_MAX_RETRY_ATTEMPTS,
        )
        assert status == HealthStatus.FAILED


class TestFallbackActivation:
    """Tests for fallback activation tracking."""

    @pytest.fixture
    def evaluator(self) -> SourceHealthEvaluator:
        """Create a fresh evaluator for each test."""
        return SourceHealthEvaluator()

    @pytest.fixture
    def now(self) -> datetime:
        """Get current UTC time."""
        return datetime.now(timezone.utc)

    def test_fallback_active_marks_degraded(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test that fallback_active flag results in degraded status."""
        last_success = now - timedelta(minutes=30)
        last_attempt = now

        status, stale_mins, remarks = evaluator.evaluate_source_health(
            current_record=None,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=0,
            fallback_active=True,
        )
        assert status == HealthStatus.DEGRADED
        assert "Fallback" in (remarks or "")

    def test_fallback_with_stale_primary(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test fallback activation with stale primary source."""
        last_success = now - timedelta(minutes=DEFAULT_STALE_THRESHOLD_MINUTES + 30)
        last_attempt = now

        # Create a stale record
        current_record = SourceHealthRecord(
            source_name="cai_spot",
            status=HealthStatus.STALE,
            last_success_at=last_success,
            last_checked_at=now - timedelta(minutes=5),
            stale_duration_minutes=DEFAULT_STALE_THRESHOLD_MINUTES + 30,
        )

        status, stale_mins, remarks = evaluator.evaluate_source_health(
            current_record=current_record,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=0,
            fallback_active=True,
        )
        assert status == HealthStatus.DEGRADED
        assert stale_mins == DEFAULT_STALE_THRESHOLD_MINUTES + 30

    def test_fallback_inactive_uses_primary_status(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test that normal status is used when fallback is not active."""
        last_success = now - timedelta(minutes=30)
        last_attempt = now

        status, stale_mins, remarks = evaluator.evaluate_source_health(
            current_record=None,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=0,
            fallback_active=False,
        )
        assert status == HealthStatus.LIVE


class TestStaleDetection:
    """Tests for stale detection and duration tracking."""

    @pytest.fixture
    def evaluator(self) -> SourceHealthEvaluator:
        """Create a fresh evaluator for each test."""
        return SourceHealthEvaluator()

    @pytest.fixture
    def now(self) -> datetime:
        """Get current UTC time."""
        return datetime.now(timezone.utc)

    def test_stale_duration_calculated_correctly(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test that stale duration is calculated correctly."""
        minutes_stale = DEFAULT_STALE_THRESHOLD_MINUTES + 30
        last_success = now - timedelta(minutes=minutes_stale)
        last_attempt = now

        status, stale_mins, remarks = evaluator.evaluate_source_health(
            current_record=None,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=0,
        )
        assert status == HealthStatus.STALE
        assert stale_mins == minutes_stale

    def test_stale_threshold_boundary(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test behavior at exactly the stale threshold."""
        # Just below threshold - should be live
        last_success = now - timedelta(minutes=DEFAULT_STALE_THRESHOLD_MINUTES - 1)
        last_attempt = now

        status, stale_mins, _ = evaluator.evaluate_source_health(
            current_record=None,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=0,
        )
        assert status == HealthStatus.LIVE

        # At threshold - should be stale
        last_success = now - timedelta(minutes=DEFAULT_STALE_THRESHOLD_MINUTES)
        status, stale_mins, _ = evaluator.evaluate_source_health(
            current_record=None,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=0,
        )
        assert status == HealthStatus.STALE

    def test_custom_stale_threshold(self, now: datetime) -> None:
        """Test that custom stale threshold is respected."""
        custom_threshold = 30  # 30 minutes
        evaluator = SourceHealthEvaluator(stale_threshold_minutes=custom_threshold)

        # Just below custom threshold
        last_success = now - timedelta(minutes=custom_threshold - 1)
        last_attempt = now

        status, _, _ = evaluator.evaluate_source_health(
            current_record=None,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=0,
        )
        assert status == HealthStatus.LIVE

        # Above custom threshold
        last_success = now - timedelta(minutes=custom_threshold + 1)
        status, _, _ = evaluator.evaluate_source_health(
            current_record=None,
            last_success=last_success,
            last_attempt=last_attempt,
            retry_count=0,
        )
        assert status == HealthStatus.STALE

    def test_no_stale_duration_without_success(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test that stale duration is 0 when there's no prior success and no failures."""
        last_attempt = now

        status, stale_mins, remarks = evaluator.evaluate_source_health(
            current_record=None,
            last_success=None,
            last_attempt=last_attempt,
            retry_count=0,
        )
        # Should be live since no success but also no failures
        # stale_mins is None because there's no success time
        assert status == HealthStatus.LIVE
        assert stale_mins is None


class TestComputeHealthTransition:
    """Tests for the compute_health_transition method."""

    @pytest.fixture
    def evaluator(self) -> SourceHealthEvaluator:
        """Create a fresh evaluator for each test."""
        return SourceHealthEvaluator()

    @pytest.fixture
    def now(self) -> datetime:
        """Get current UTC time."""
        return datetime.now(timezone.utc)

    def test_successful_ingestion_creates_live_record(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test that successful ingestion creates a live health record."""
        record = evaluator.compute_health_transition(
            source_name="cai_spot",
            current_record=None,
            ingestion_success=True,
            last_attempt=now,
        )
        assert record.source_name == "cai_spot"
        assert record.status == HealthStatus.LIVE
        assert record.last_success_at == now
        assert record.fallback_active is False

    def test_failed_ingestion_without_retries(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test failed ingestion with no prior failures."""
        record = evaluator.compute_health_transition(
            source_name="cai_spot",
            current_record=None,
            ingestion_success=False,
            last_attempt=now,
            retry_count=1,
        )
        # Single failure doesn't trigger failed status
        assert record.status == HealthStatus.LIVE
        assert record.last_success_at is None
        assert record.details["retry_count"] == 1

    def test_failed_ingestion_with_max_retries(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test failed ingestion when max retries exceeded."""
        record = evaluator.compute_health_transition(
            source_name="cai_spot",
            current_record=None,
            ingestion_success=False,
            last_attempt=now,
            retry_count=DEFAULT_MAX_RETRY_ATTEMPTS,
        )
        assert record.status == HealthStatus.FAILED

    def test_fallback_ingestion_sets_flag(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test that fallback ingestion sets the fallback_active flag."""
        record = evaluator.compute_health_transition(
            source_name="cai_spot",
            current_record=None,
            ingestion_success=True,
            last_attempt=now,
            fallback_active=True,
        )
        assert record.fallback_active is True
        assert record.status == HealthStatus.DEGRADED

    def test_preserves_existing_details(
        self, evaluator: SourceHealthEvaluator, now: datetime
    ) -> None:
        """Test that existing details are preserved and updated."""
        current_record = SourceHealthRecord(
            source_name="cai_spot",
            status=HealthStatus.LIVE,
            last_success_at=now - timedelta(minutes=30),
            last_checked_at=now - timedelta(minutes=5),
            details={"previous_key": "previous_value"},
        )

        record = evaluator.compute_health_transition(
            source_name="cai_spot",
            current_record=current_record,
            ingestion_success=True,
            last_attempt=now,
        )
        assert "previous_key" in record.details
        assert "retry_count" in record.details
        assert "last_attempt" in record.details


class TestEvaluatorInstance:
    """Tests for global evaluator instance management."""

    def test_get_evaluator_returns_instance(self) -> None:
        """Test that get_evaluator returns an instance."""
        reset_evaluator()
        evaluator = get_evaluator()
        assert evaluator is not None
        assert isinstance(evaluator, SourceHealthEvaluator)

    def test_get_evaluator_returns_same_instance(self) -> None:
        """Test that get_evaluator returns the same instance."""
        reset_evaluator()
        evaluator1 = get_evaluator()
        evaluator2 = get_evaluator()
        assert evaluator1 is evaluator2

    def test_reset_evaluator_clears_instance(self) -> None:
        """Test that reset_evaluator clears the instance."""
        evaluator1 = get_evaluator()
        reset_evaluator()
        evaluator2 = get_evaluator()
        assert evaluator1 is not evaluator2


class TestCustomThresholds:
    """Tests for custom threshold configuration."""

    def test_custom_stale_threshold(self) -> None:
        """Test custom stale threshold."""
        evaluator = SourceHealthEvaluator(stale_threshold_minutes=30)
        assert evaluator.stale_threshold_minutes == 30

    def test_custom_failed_threshold(self) -> None:
        """Test custom failed threshold."""
        evaluator = SourceHealthEvaluator(failed_threshold_minutes=720)
        assert evaluator.failed_threshold_minutes == 720

    def test_custom_max_retry_attempts(self) -> None:
        """Test custom max retry attempts."""
        evaluator = SourceHealthEvaluator(max_retry_attempts=5)
        assert evaluator.max_retry_attempts == 5

    def test_default_thresholds(self) -> None:
        """Test default threshold values."""
        evaluator = SourceHealthEvaluator()
        assert evaluator.stale_threshold_minutes == DEFAULT_STALE_THRESHOLD_MINUTES
        assert evaluator.failed_threshold_minutes == DEFAULT_FAILED_THRESHOLD_MINUTES
        assert evaluator.max_retry_attempts == DEFAULT_MAX_RETRY_ATTEMPTS

"""Contract tests for forecast record schema.

Validates that Forecast records conform to the forecast-record.json contract:
- target_source: string
- horizon_hours: integer
- predicted_value: float (positive)
- lower_bound: float (positive)
- upper_bound: float (positive)
- confidence_level: float (e.g., 0.95)
- model_version: string
- is_decayed: boolean
- Upper bound >= predicted value
- Lower bound <= predicted value
- target_timestamp_utc must be in the future
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from models.forecast import Forecast


class TestForecastSchemaContract:
    """Validate forecast records against forecast-record.json contract."""

    def test_target_source_required(self):
        """Contract: target_source is required."""
        now = datetime.now(UTC)
        target_ts = now + timedelta(days=1)
        with pytest.raises(ValueError, match="target_source"):
            Forecast(
                target_source="",
                timestamp_utc=now,
                target_timestamp_utc=target_ts,
                horizon_hours=24,
                predicted_value=85.0,
                lower_bound=80.0,
                upper_bound=90.0,
            )

    def test_positive_predicted_value_required(self):
        """Contract: predicted_value must be positive."""
        now = datetime.now(UTC)
        target_ts = now + timedelta(days=1)
        with pytest.raises(ValueError, match="positive"):
            Forecast(
                target_source="cai_spot",
                timestamp_utc=now,
                target_timestamp_utc=target_ts,
                horizon_hours=24,
                predicted_value=-10.0,
                lower_bound=80.0,
                upper_bound=90.0,
            )

    def test_positive_lower_bound_required(self):
        """Contract: lower_bound must be positive."""
        now = datetime.now(UTC)
        target_ts = now + timedelta(days=1)
        with pytest.raises(ValueError, match="lower_bound"):
            Forecast(
                target_source="cai_spot",
                timestamp_utc=now,
                target_timestamp_utc=target_ts,
                horizon_hours=24,
                predicted_value=85.0,
                lower_bound=-5.0,
                upper_bound=90.0,
            )

    def test_positive_upper_bound_required(self):
        """Contract: upper_bound must be positive."""
        now = datetime.now(UTC)
        target_ts = now + timedelta(days=1)
        with pytest.raises(ValueError, match="upper_bound"):
            Forecast(
                target_source="cai_spot",
                timestamp_utc=now,
                target_timestamp_utc=target_ts,
                horizon_hours=24,
                predicted_value=85.0,
                lower_bound=80.0,
                upper_bound=-5.0,
            )

    def test_upper_bound_greater_equal_predicted(self):
        """Contract: upper_bound must be >= predicted_value."""
        now = datetime.now(UTC)
        target_ts = now + timedelta(days=1)
        with pytest.raises(ValueError, match="upper_bound"):
            Forecast(
                target_source="cai_spot",
                timestamp_utc=now,
                target_timestamp_utc=target_ts,
                horizon_hours=24,
                predicted_value=85.0,
                lower_bound=80.0,
                upper_bound=84.0,
            )

    def test_lower_bound_less_equal_predicted(self):
        """Contract: lower_bound must be <= predicted_value."""
        now = datetime.now(UTC)
        target_ts = now + timedelta(days=1)
        with pytest.raises(ValueError, match="lower_bound"):
            Forecast(
                target_source="cai_spot",
                timestamp_utc=now,
                target_timestamp_utc=target_ts,
                horizon_hours=24,
                predicted_value=85.0,
                lower_bound=86.0,
                upper_bound=90.0,
            )

    def test_target_timestamp_in_future(self):
        """Contract: target_timestamp_utc must be in the future relative to timestamp_utc."""
        now = datetime.now(UTC)
        with pytest.raises(ValueError, match="future"):
            Forecast(
                target_source="cai_spot",
                timestamp_utc=now,
                target_timestamp_utc=now - timedelta(hours=1),
                horizon_hours=24,
                predicted_value=85.0,
                lower_bound=80.0,
                upper_bound=90.0,
            )

    def test_forecast_to_dict_includes_all_fields(self):
        """Contract: to_dict must include all required fields."""
        now = datetime.now(UTC)
        target_ts = now + timedelta(hours=24)
        forecast = Forecast(
            target_source="cai_spot",
            timestamp_utc=now,
            target_timestamp_utc=target_ts,
            horizon_hours=24,
            predicted_value=85.50,
            lower_bound=80.00,
            upper_bound=91.00,
            confidence_level=0.95,
            model_version="baseline-1.0.0",
            is_decayed=False,
        )
        forecast.created_at = now
        result = forecast.to_dict()

        assert "target_source" in result
        assert "predicted_value" in result
        assert "lower_bound" in result
        assert "upper_bound" in result
        assert "confidence_level" in result
        assert "model_version" in result
        assert "is_decayed" in result

    def test_confidence_level_95_valid(self):
        """Contract: confidence_level 0.95 should be accepted."""
        now = datetime.now(UTC)
        target_ts = now + timedelta(days=1)
        forecast = Forecast(
            target_source="cai_spot",
            timestamp_utc=now,
            target_timestamp_utc=target_ts,
            horizon_hours=24,
            predicted_value=85.0,
            lower_bound=80.0,
            upper_bound=90.0,
            confidence_level=0.95,
        )
        assert forecast.confidence_level == 0.95

    def test_default_model_version(self):
        """Contract: model_version has default 'baseline-1.0.0'."""
        now = datetime.now(UTC)
        target_ts = now + timedelta(days=1)
        forecast = Forecast(
            target_source="cai_spot",
            timestamp_utc=now,
            target_timestamp_utc=target_ts,
            horizon_hours=24,
            predicted_value=85.0,
            lower_bound=80.0,
            upper_bound=90.0,
        )
        assert forecast.model_version == "baseline-1.0.0"

    def test_default_is_decayed_false(self):
        """Contract: is_decayed defaults to False."""
        now = datetime.now(UTC)
        target_ts = now + timedelta(days=1)
        forecast = Forecast(
            target_source="cai_spot",
            timestamp_utc=now,
            target_timestamp_utc=target_ts,
            horizon_hours=24,
            predicted_value=85.0,
            lower_bound=80.0,
            upper_bound=90.0,
        )
        assert not forecast.is_decayed

    def test_forecast_id_unique_auto_generated(self):
        """Contract: UUID is auto-generated for id."""
        now = datetime.now(UTC)
        target_ts = now + timedelta(days=1)
        forecast1 = Forecast(
            target_source="cai_spot",
            timestamp_utc=now,
            target_timestamp_utc=target_ts,
            horizon_hours=24,
            predicted_value=85.0,
            lower_bound=80.0,
            upper_bound=90.0,
        )
        forecast2 = Forecast(
            target_source="cai_spot",
            timestamp_utc=now,
            target_timestamp_utc=target_ts,
            horizon_hours=24,
            predicted_value=85.0,
            lower_bound=80.0,
            upper_bound=90.0,
        )
        assert forecast1.id != forecast2.id

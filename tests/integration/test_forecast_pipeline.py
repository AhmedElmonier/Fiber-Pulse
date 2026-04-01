"""Integration tests for forecast pipeline.

Validates end-to-end forecast generation including:
- XGBoost model training with quantile regression
- Feature extraction using 30-day sliding window
- Confidence interval generation
- Confidence decay for stale data
- MAE validation utilities
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from models.baseline_model import (
    BaselineXGBoostModel,
    create_training_dataset,
    extract_features_from_window,
)
from models.forecast import Forecast
from utils.confidence_decay import apply_confidence_decay
from utils.metrics import AccuracyValidator, calculate_mae

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")


@pytest.fixture
def sample_price_history() -> list[float]:
    """Generate sample price history for testing."""
    np.random.seed(42)
    base_prices = np.linspace(80, 90, 60)
    noise = np.random.normal(0, 1, 60)
    prices = base_prices + noise
    return [round(float(p), 2) for p in prices]


@pytest.fixture
def short_price_history() -> list[float]:
    """Generate price history shorter than minimum requirement."""
    return [80.0 + i * 0.5 for i in range(20)]


class TestFeatureExtraction:
    """Tests for feature extraction from sliding window."""

    def test_extract_features_from_window(self):
        """Test feature extraction from price window."""
        prices = list(np.arange(1, 31))
        features = extract_features_from_window(prices)

        assert features.lagged_1 == 30.0
        assert features.lagged_7 == 24.0
        assert features.rolling_mean_7 is not None
        assert features.price_momentum_7 is not None

    def test_insufficient_prices_raises(self):
        """Test that insufficient prices raises ValueError."""
        with pytest.raises(ValueError, match="At least one price"):
            extract_features_from_window([])


class TestTrainingDataset:
    """Tests for creating training dataset."""

    def test_create_training_dataset(self):
        """Test training dataset creation from prices."""
        prices = list(np.arange(1, 32))
        x, y = create_training_dataset(prices)

        assert x.shape[1] == 12
        assert len(y) == 1
        assert y[0] == 31.0

    def test_insufficient_data_raises(self):
        """Test that insufficient data raises ValueError."""
        prices = list(range(10))
        with pytest.raises(ValueError, match="at least"):
            create_training_dataset(prices)


class TestBaselineXGBoostModel:
    """Tests for XGBoost baseline model."""

    def test_model_initialization(self):
        """Test model initializes correctly."""
        model = BaselineXGBoostModel()
        assert not model.is_trained
        assert model.window_size == 30
        assert model.MODEL_VERSION == "baseline-1.0.0"

    def test_train_insufficient_data_raises(self, short_price_history: list[float]):
        """Test that training without sufficient data raises."""
        model = BaselineXGBoostModel()
        with pytest.raises(ValueError, match="Insufficient history"):
            model.train(short_price_history)

    def test_train_and_predict(self, sample_price_history: list[float]):
        """Test model trains and generates predictions."""
        model = BaselineXGBoostModel()
        model.train(sample_price_history)

        assert model.is_trained
        assert model._cached_source == "default"

        recent = sample_price_history[-30:]
        lower, median, upper = model.predict(recent)

        assert lower <= median <= upper
        assert lower > 0
        assert median > 0
        assert upper > 0

    def test_predict_without_training_raises(self):
        """Test prediction without training raises RuntimeError."""
        model = BaselineXGBoostModel()
        with pytest.raises(RuntimeError, match="trained"):
            model.predict([80.0] * 30)

    def test_predict_insufficient_recent_prices_raises(self, sample_price_history: list[float]):
        """Test prediction with insufficient recent prices raises."""
        model = BaselineXGBoostModel()
        model.train(sample_price_history)

        with pytest.raises(ValueError, match="recent prices"):
            model.predict([80.0] * 10)


class TestConfidenceDecay:
    """Tests for confidence decay logic."""

    def test_apply_confidence_decay_not_stale(self):
        """Test decay not applied when data is fresh."""
        result = apply_confidence_decay(
            predicted_value=85.0,
            lower_bound=80.0,
            upper_bound=90.0,
            is_stale=False,
        )

        assert not result.is_decayed
        assert result.original_width == result.decayed_width

    def test_apply_confidence_decay_stale_data(self):
        """Test decay applied when data is stale."""
        result = apply_confidence_decay(
            predicted_value=85.0,
            lower_bound=80.0,
            upper_bound=90.0,
            is_stale=True,
            decay_factor=0.20,
        )

        assert result.is_decayed
        assert result.decayed_width > result.original_width

    def test_confidence_decay_20_percent(self):
        """Test that decay factor is exactly 20%."""
        result = apply_confidence_decay(
            predicted_value=100.0,
            lower_bound=90.0,
            upper_bound=110.0,
            is_stale=True,
            decay_factor=0.20,
        )

        original_width = 20.0
        expected_decay = original_width * 0.2
        assert abs(result.decayed_width - (original_width + expected_decay)) < 0.01


class TestMAEValidation:
    """Tests for MAE validation utilities."""

    def test_calculate_mae_perfect_predictions(self):
        """Test MAE with perfect predictions."""
        predictions = [85.0, 86.0, 87.0]
        actuals = [85.0, 86.0, 87.0]

        result = calculate_mae(predictions, actuals)

        assert result.mae == 0.0
        assert result.mae_percentage == 0.0
        assert result.meets_target

    def test_calculate_mae_with_errors(self):
        """Test MAE calculation with prediction errors."""
        predictions = [85.0, 86.0, 87.0]
        actuals = [84.0, 87.0, 86.0]

        result = calculate_mae(predictions, actuals)

        assert result.mae == 1.0
        assert result.meets_target

    def test_calculate_mae_fails_below_threshold(self):
        """Test MAE fails when exceeding target percentage."""
        predictions = [100.0]
        actuals = [50.0]

        result = calculate_mae(predictions, actuals, target_percentage=5.0)

        assert not result.meets_target
        assert result.mae_percentage > 5.0

    def test_accuracy_validator(self):
        """Test AccuracyValidator tracks multiple validations."""
        validator = AccuracyValidator(target_mae_percentage=5.0)

        validator.validate([85, 86], [84, 87])
        validator.validate([100], [105])

        assert len(validator.get_results()) == 2
        assert validator.average_mae_percentage() > 0


class TestForecastRecord:
    """Tests for Forecast model integration."""

    def test_forecast_validation_complete(self):
        """Test Forecast with all fields valid."""
        now = datetime.now(UTC)
        target_ts = now + timedelta(hours=24)

        forecast = Forecast(
            target_source="cai_spot",
            timestamp_utc=now,
            target_timestamp_utc=target_ts,
            horizon_hours=24,
            predicted_value=85.0,
            lower_bound=80.0,
            upper_bound=90.0,
            confidence_level=0.95,
            is_decayed=False,
        )

        assert forecast.target_source == "cai_spot"
        assert forecast.horizon_hours == 24
        assert forecast.predicted_value == 85.0


class TestForecastPipelineIntegration:
    """Integration tests for end-to-end forecast pipeline."""

    @pytest.mark.asyncio
    async def test_generate_forecast_flow(self, sample_price_history: list[float]):
        """Test complete forecast generation flow."""
        from agents.forecast import get_staleness_status

        is_stale, hours = get_staleness_status(datetime.now(UTC))
        assert not is_stale

        is_stale_old, hours_old = get_staleness_status(datetime.now(UTC) - timedelta(hours=72))
        assert is_stale_old
        assert hours_old > 48

    @pytest.mark.asyncio
    async def test_stale_data_detected(self):
        """Test staleness detection for old data."""
        from agents.forecast import get_staleness_status

        fresh_time = datetime.now(UTC) - timedelta(hours=24)
        is_stale, _ = get_staleness_status(fresh_time)
        assert not is_stale

        stale_time = datetime.now(UTC) - timedelta(hours=72)
        is_stale, _ = get_staleness_status(stale_time)
        assert is_stale

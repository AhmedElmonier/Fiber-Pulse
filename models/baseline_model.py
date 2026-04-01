"""Baseline XGBoost forecasting model for FiberPulse.

Implements feature extraction using 30-day sliding window and XGBoost quantile
regression for generating price forecasts with confidence intervals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import hashlib
import json
import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


WINDOW_SIZE = 30
MIN_HISTORY_DAYS = 30


@dataclass
class TimeSeriesFeatures:
    """Extracted features from a sliding window of price data."""

    prices: NDArray[np.float64]
    lagged_1: float | None
    lagged_2: float | None
    lagged_3: float | None
    lagged_7: float | None
    rolling_mean_7: float | None
    rolling_std_7: float | None
    rolling_mean_14: float | None
    rolling_std_14: float | None
    rolling_mean_30: float | None
    rolling_std_30: float | None
    price_momentum_7: float | None
    price_momentum_14: float | None


def extract_features_from_window(
    prices: list[float] | NDArray[np.float64],
) -> TimeSeriesFeatures:
    """Extract features from a window of price data.

    Args:
        prices: Array of normalized USD prices (most recent last).

    Returns:
        TimeSeriesFeatures with extracted features.
    """
    prices = np.array(prices)
    n = len(prices)

    if n < 1:
        raise ValueError("At least one price required for feature extraction")

    lagged_1 = float(prices[-1]) if n >= 1 else None
    lagged_2 = float(prices[-2]) if n >= 2 else None
    lagged_3 = float(prices[-3]) if n >= 3 else None
    lagged_7 = float(prices[-7]) if n >= 7 else None

    if n >= 7:
        rolling_mean_7 = float(np.mean(prices[-7:]))
        rolling_std_7 = float(np.std(prices[-7:]))
    elif n >= 1:
        rolling_mean_7 = float(np.mean(prices))
        rolling_std_7 = None
    else:
        rolling_mean_7 = None
        rolling_std_7 = None

    if n >= 14:
        rolling_mean_14 = float(np.mean(prices[-14:]))
        rolling_std_14 = float(np.std(prices[-14:]))
    elif n >= 1:
        rolling_mean_14 = float(np.mean(prices))
        rolling_std_14 = None
    else:
        rolling_mean_14 = None
        rolling_std_14 = None

    if n >= 30:
        rolling_mean_30 = float(np.mean(prices[-30:]))
        rolling_std_30 = float(np.std(prices[-30:]))
    elif n >= 1:
        rolling_mean_30 = float(np.mean(prices))
        rolling_std_30 = None
    else:
        rolling_mean_30 = None
        rolling_std_30 = None

    if n >= 8:
        price_momentum_7 = float((prices[-1] - prices[-8]) / prices[-8]) if prices[-8] != 0 else 0.0
    elif n >= 2:
        price_momentum_7 = float((prices[-1] - prices[0]) / prices[0]) if prices[0] != 0 else 0.0
    else:
        price_momentum_7 = None

    if n >= 15:
        price_momentum_14 = (
            float((prices[-1] - prices[-15]) / prices[-15]) if prices[-15] != 0 else 0.0
        )
    elif n >= 2:
        price_momentum_14 = float((prices[-1] - prices[0]) / prices[0]) if prices[0] != 0 else 0.0
    else:
        price_momentum_14 = None

    return TimeSeriesFeatures(
        prices=prices,
        lagged_1=lagged_1,
        lagged_2=lagged_2,
        lagged_3=lagged_3,
        lagged_7=lagged_7,
        rolling_mean_7=rolling_mean_7,
        rolling_std_7=rolling_std_7,
        rolling_mean_14=rolling_mean_14,
        rolling_std_14=rolling_std_14,
        rolling_mean_30=rolling_mean_30,
        rolling_std_30=rolling_std_30,
        price_momentum_7=price_momentum_7,
        price_momentum_14=price_momentum_14,
    )


def features_to_vector(features: TimeSeriesFeatures) -> NDArray[np.float64]:
    """Convert TimeSeriesFeatures to a feature vector for model input.

    Args:
        features: Extracted time series features.

    Returns:
        NumPy array of feature values.
    """
    vector = np.array(
        [
            features.lagged_1 if features.lagged_1 is not None else 0.0,
            features.lagged_2 if features.lagged_2 is not None else 0.0,
            features.lagged_3 if features.lagged_3 is not None else 0.0,
            features.lagged_7 if features.lagged_7 is not None else 0.0,
            features.rolling_mean_7 if features.rolling_mean_7 is not None else 0.0,
            features.rolling_std_7 if features.rolling_std_7 is not None else 0.0,
            features.rolling_mean_14 if features.rolling_mean_14 is not None else 0.0,
            features.rolling_std_14 if features.rolling_std_14 is not None else 0.0,
            features.rolling_mean_30 if features.rolling_mean_30 is not None else 0.0,
            features.rolling_std_30 if features.rolling_std_30 is not None else 0.0,
            features.price_momentum_7 if features.price_momentum_7 is not None else 0.0,
            features.price_momentum_14 if features.price_momentum_14 is not None else 0.0,
        ]
    )
    return vector


def create_training_dataset(
    prices: list[float] | NDArray[np.float64],
    window_size: int = WINDOW_SIZE,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Create training dataset from price time series.

    Args:
        prices: Historical price time series.
        window_size: Number of days to use for each training sample.

    Returns:
        Tuple of (X, y) arrays for training.
    """
    prices = np.array(prices)
    if len(prices) < window_size + 1:
        raise ValueError(f"Need at least {window_size + 1} prices for training, got {len(prices)}")

    x, y = [], []
    for i in range(len(prices) - window_size):
        window = prices[i : i + window_size]
        target = prices[i + window_size]
        features = extract_features_from_window(window)
        x.append(features_to_vector(features))
        y.append(target)

    return np.array(x), np.array(y)


class BaselineXGBoostModel:
    """XGBoost-based baseline forecasting model with quantile regression.

    Uses three XGBoost models for quantile regression to generate
    confidence intervals.
    """

    QUANTILES = [0.05, 0.5, 0.95]
    MODEL_VERSION = "baseline-1.0.0"

    def __init__(
        self,
        window_size: int = WINDOW_SIZE,
        enable_caching: bool = True,
    ) -> None:
        """Initialize the baseline model.

        Args:
            window_size: Number of days in sliding window.
            enable_caching: Whether to cache trained models.
        """
        self.window_size = window_size
        self._models: dict[float, Any] = {}
        self._is_trained = False
        self._enable_caching = enable_caching
        self._cached_source: str | None = None
        self._cached_data_hash: str | None = None

    @property
    def is_trained(self) -> bool:
        """Check if the model has been trained."""
        return self._is_trained

    def _create_model(self, quantile: float) -> Any:
        """Create an XGBoost model for a specific quantile.

        Args:
            quantile: The quantile value (0-1).

        Returns:
            XGBoost model instance.
        """
        from xgboost import XGBRegressor

        return XGBRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            objective="reg:quantileerror",
            quantile_alpha=quantile,
            random_state=42,
            verbosity=0,
        )

    def train(self, prices: list[float], source_name: str = "default") -> None:
        """Train the quantile regression models.

        Args:
            prices: Historical price time series.
            source_name: Name of the price source.
        """
        if len(prices) < MIN_HISTORY_DAYS:
            raise ValueError(
                f"Insufficient history: need at least {MIN_HISTORY_DAYS} days, got {len(prices)}"
            )

        if self._enable_caching and self._is_trained and self._cached_source == source_name:
            return

        x, y = create_training_dataset(prices, self.window_size)

        self._models = {}
        for quantile in self.QUANTILES:
            model = self._create_model(quantile)
            model.fit(x, y)
            self._models[quantile] = model

        self._is_trained = True
        if self._enable_caching:
            self._cached_source = source_name

    def predict(self, recent_prices: list[float]) -> tuple[float, float, float]:
        """Generate point prediction with confidence intervals.

        Args:
            recent_prices: Recent price values (most recent last).

        Returns:
            Tuple of (lower_bound, predicted_value, upper_bound).
        """
        if not self._is_trained:
            raise RuntimeError("Model must be trained before prediction")

        if len(recent_prices) < self.window_size:
            raise ValueError(
                f"Need at least {self.window_size} recent prices, got {len(recent_prices)}"
            )

        window = recent_prices[-self.window_size :]
        features = extract_features_from_window(window)
        x = features_to_vector(features).reshape(1, -1)

        predictions = {}
        for quantile, model in self._models.items():
            predictions[quantile] = float(model.predict(x)[0])

        lower = predictions[0.05]
        median = predictions[0.5]
        upper = predictions[0.95]

        tiny_positive = 1.0
        if median <= 0:
            median = tiny_positive

        if upper < median:
            upper = median * 1.1
        if lower > median:
            lower = median * 0.9
        if lower <= 0:
            lower = median * 0.5
        if upper <= 0:
            upper = median * 1.5

        if upper < lower:
            mid = (upper + lower) / 2
            lower = mid * 0.9
            upper = mid * 1.1

        return (lower, median, upper)

    def get_model_version(self) -> str:
        """Get the model version string."""
        return self.MODEL_VERSION

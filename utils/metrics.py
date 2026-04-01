"""Model evaluation metrics for FiberPulse forecasting.

Provides MAE (Mean Absolute Error) validation utilities to verify
SC-001 accuracy targets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MAEResult:
    """Result of MAE calculation."""

    mae: float
    mae_percentage: float
    sample_count: int
    meets_target: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "mae": self.mae,
            "mae_percentage": self.mae_percentage,
            "sample_count": self.sample_count,
            "meets_target": self.meets_target,
        }


def calculate_mae(
    predictions: list[float],
    actuals: list[float],
    target_percentage: float = 5.0,
) -> MAEResult:
    """Calculate Mean Absolute Error and verify against target percentage.

    Args:
        predictions: List of predicted values.
        actuals: List of actual values.
        target_percentage: Target MAE as percentage of mean actual (default 5.0%).

    Returns:
        MAEResult with MAE, percentage, sample count, and target verification.
    """
    if len(predictions) != len(actuals):
        raise ValueError(
            f"Predictions and actuals must have same length: "
            f"{len(predictions)} vs {len(actuals)}"
        )

    if len(predictions) == 0:
        raise ValueError("At least one prediction is required")

    n = len(predictions)
    total_error = sum(abs(predictions[i] - actuals[i]) for i in range(n))
    mae = total_error / n

    mean_actual = sum(actuals) / n
    if mean_actual > 0:
        mae_percentage = (mae / mean_actual) * 100
    else:
        mae_percentage = float("inf") if mae > 0 else 0.0

    meets_target = mae_percentage <= target_percentage

    return MAEResult(
        mae=mae,
        mae_percentage=mae_percentage,
        sample_count=n,
        meets_target=meets_target,
    )


def calculate_mae_from_forecasts(
    forecasts: list[dict[str, Any]],
    price_records: list[dict[str, Any]],
) -> MAEResult:
    """Calculate MAE by comparing forecasts against actual price records.

    Args:
        forecasts: List of forecast records with predicted_value and target_timestamp_utc.
        price_records: List of price records with normalized_usd and timestamp_utc.

    Returns:
        MAEResult with MAE calculation.
    """
    if not forecasts or not price_records:
        raise ValueError("Both forecasts and price records are required")

    predictions = []
    actuals = []

    for forecast in forecasts:
        forecast_target_ts = forecast.get("target_timestamp_utc")
        predicted_value = forecast.get("predicted_value")

        if not forecast_target_ts or predicted_value is None:
            continue

        matched_records = [
            p for p in price_records
            if p.get("timestamp_utc") == forecast_target_ts
        ]

        if matched_records:
            actual_value = matched_records[0].get("normalized_usd")
            if actual_value is not None:
                predictions.append(predicted_value)
                actuals.append(actual_value)

    if not predictions:
        raise ValueError("No matching forecasts and actuals found")

    return calculate_mae(predictions, actuals)


class AccuracyValidator:
    """Validates model accuracy against specified targets."""

    def __init__(self, target_mae_percentage: float = 5.0) -> None:
        """Initialize validator with target MAE percentage.

        Args:
            target_mae_percentage: Target MAE as percentage (default 5.0%).
        """
        self.target_mae_percentage = target_mae_percentage
        self._results: list[MAEResult] = []

    def validate(
        self,
        predictions: list[float],
        actuals: list[float],
    ) -> MAEResult:
        """Validate predictions against actuals.

        Args:
            predictions: List of predicted values.
            actuals: List of actual values.

        Returns:
            MAEResult with validation outcome.
        """
        result = calculate_mae(predictions, actuals, self.target_mae_percentage)
        self._results.append(result)
        return result

    def get_results(self) -> list[MAEResult]:
        """Get all validation results."""
        return self._results

    def all_meet_target(self) -> bool:
        """Check if all validation results meet the target."""
        if not self._results:
            return False
        return all(r.meets_target for r in self._results)

    def average_mae_percentage(self) -> float:
        """Get average MAE percentage across all validations."""
        if not self._results:
            return 0.0
        return sum(r.mae_percentage for r in self._results) / len(self._results)

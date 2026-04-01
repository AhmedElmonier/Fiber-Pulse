"""Forecast orchestrator for FiberPulse prediction pipeline.

Generates daily price forecasts with confidence intervals using XGBoost
quantile regression. Handles recursive prediction for multi-step horizons
and integrates confidence decay penalty for stale data.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import click

from db.repository import Repository
from models.baseline_model import MIN_HISTORY_DAYS, BaselineXGBoostModel
from models.forecast import Forecast
from utils.confidence_decay import apply_confidence_decay

logger = logging.getLogger(__name__)

DEFAULT_HORIZON_HOURS = 24
STALE_THRESHOLD_HOURS = 48


class ForecastError(Exception):
    """Raised when forecast generation fails."""


class InsufficientDataError(ForecastError):
    """Raised when there's insufficient historical data."""

    pass


def get_staleness_status(
    latest_timestamp: datetime | None,
    reference_time: datetime | None = None,
) -> tuple[bool, float]:
    """Determine if data is stale and calculate staleness duration.

    Args:
        latest_timestamp: Timestamp of most recent data point.
        reference_time: Reference time to calculate staleness from (defaults to now).

    Returns:
        Tuple of (is_stale, hours_since_last_update).
    """
    if reference_time is None:
        reference_time = datetime.now(UTC)

    if latest_timestamp is None:
        return True, float("inf")

    hours_elapsed = (reference_time - latest_timestamp).total_seconds() / 3600
    is_stale = hours_elapsed > STALE_THRESHOLD_HOURS

    return is_stale, hours_elapsed


async def generate_forecast(
    repository: Repository,
    target_source: str,
    horizon_hours: int = DEFAULT_HORIZON_HOURS,
    confidence_level: float = 0.95,
) -> Forecast:
    """Generate a price forecast for the specified target.

    Args:
        repository: Database repository instance.
        target_source: Source name to generate forecast for.
        horizon_hours: Forecast horizon in hours.
        confidence_level: Confidence level for intervals.

    Returns:
        Forecast record with predictions and confidence intervals.

    Raises:
        InsufficientDataError: If insufficient historical data available.
        ForecastError: If forecast generation fails.
    """
    records = await repository.get_price_records(
        source_name=target_source,
        limit=MIN_HISTORY_DAYS + 100,
    )

    if len(records) < MIN_HISTORY_DAYS:
        raise InsufficientDataError(
            f"Insufficient data: need at least {MIN_HISTORY_DAYS} records, got {len(records)}"
        )

    prices = [float(r.normalized_usd) for r in sorted(records, key=lambda x: x.timestamp_utc)]

    model = BaselineXGBoostModel()
    model.train(prices, source_name=target_source)

    recent_prices = prices[-30:]
    lower_bound, predicted_value, upper_bound = model.predict(recent_prices)

    latest_record = max(records, key=lambda x: x.timestamp_utc)
    is_stale, hours_elapsed = get_staleness_status(latest_record.timestamp_utc)

    if is_stale:
        decayed = apply_confidence_decay(
            predicted_value=predicted_value,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            is_stale=True,
        )
        lower_bound = decayed.lower_bound
        upper_bound = decayed.upper_bound
        logger.info(
            f"Applied confidence decay: original width={decayed.original_width:.2f}, "
            f"decayed width={decayed.decayed_width:.2f}"
        )

    now = datetime.now(UTC)
    target_timestamp = now + timedelta(hours=horizon_hours)

    forecast = Forecast(
        target_source=target_source,
        timestamp_utc=now,
        target_timestamp_utc=target_timestamp,
        horizon_hours=horizon_hours,
        predicted_value=round(predicted_value, 4),
        lower_bound=round(lower_bound, 4),
        upper_bound=round(upper_bound, 4),
        confidence_level=confidence_level,
        model_version=model.get_model_version(),
        is_decayed=is_stale,
    )

    await repository.insert_forecast(forecast)
    logger.info(
        f"Generated forecast for {target_source}: "
        f"value={predicted_value:.2f}, CI=[{lower_bound:.2f}, {upper_bound:.2f}], "
        f"is_decayed={is_stale}"
    )

    return forecast


async def get_latest_forecast(
    repository: Repository,
    target_source: str | None = None,
) -> list[Forecast]:
    """Retrieve the most recent forecasts.

    Args:
        repository: Database repository instance.
        target_source: Optional source name filter.

    Returns:
        List of forecast records.
    """
    records = await repository.get_forecasts(
        target_source=target_source,
        limit=10,
    )
    forecasts = []
    for r in records:
        forecasts.append(
            Forecast(
                target_source=r.target_source,
                timestamp_utc=r.timestamp_utc,
                target_timestamp_utc=r.target_timestamp_utc,
                horizon_hours=r.horizon_hours,
                predicted_value=r.predicted_value,
                lower_bound=r.lower_bound,
                upper_bound=r.upper_bound,
                confidence_level=r.confidence_level,
                model_version=r.model_version,
                is_decayed=r.is_decayed,
            )
        )
    return forecasts


@click.command("forecast")
@click.option(
    "--target",
    "target_source",
    required=True,
    help="Target source to forecast (e.g., cai_spot)",
)
@click.option(
    "--horizon",
    "horizon_hours",
    default=DEFAULT_HORIZON_HOURS,
    help="Forecast horizon in hours",
)
@click.option(
    "--confidence",
    "confidence_level",
    default=0.95,
    help="Confidence level for intervals (e.g., 0.95)",
)
def forecast_cli(
    target_source: str,
    horizon_hours: int,
    confidence_level: float,
) -> None:
    """Generate a price forecast for the specified target source."""
    from config import get_config

    config = get_config()

    async def run():
        repository = Repository(config.database_url)

        try:
            forecast = await generate_forecast(
                repository,
                target_source,
                horizon_hours,
                confidence_level,
            )
            click.echo(
                f"Forecast generated for {forecast.target_source}:\n"
                f"  Predicted value: {forecast.predicted_value:.4f}\n"
                f"  Confidence interval: [{forecast.lower_bound:.4f}, {forecast.upper_bound:.4f}]\n"
                f"  Confidence level: {forecast.confidence_level * 100}%\n"
                f"  Is decayed: {forecast.is_decayed}\n"
                f"  Model version: {forecast.model_version}"
            )
        except InsufficientDataError as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()
        except ForecastError as e:
            click.echo(f"Forecast error: {e}", err=True)
            raise click.Abort()
        finally:
            await repository.close()

    import asyncio

    asyncio.run(run())


@click.command("latest-forecast")
@click.option(
    "--target",
    "target_source",
    default=None,
    help="Target source to filter (e.g., cai_spot)",
)
def latest_forecast_cli(target_source: str | None) -> None:
    """Get the most recent forecast results."""
    from config import get_config

    config = get_config()

    async def run():
        repository = Repository(config.database_url)

        try:
            forecasts = await get_latest_forecast(repository, target_source)
            if not forecasts:
                click.echo("No forecasts found")
                return

            for forecast in forecasts:
                click.echo(
                    f"{forecast.target_source} @ {forecast.timestamp_utc}:\n"
                    f"  Predicted value: {forecast.predicted_value:.4f}\n"
                    f"  CI: [{forecast.lower_bound:.4f}, {forecast.upper_bound:.4f}]\n"
                    f"  Decayed: {forecast.is_decayed}"
                )
        finally:
            await repository.close()

    import asyncio

    asyncio.run(run())

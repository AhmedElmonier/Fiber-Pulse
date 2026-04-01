"""Alert trigger logic for high volatility price movements.

Compares the latest price against the previous day and triggers
alerts when the delta exceeds the configured threshold (default 3%).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from src.utils.alert_suppressor import get_suppressor

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD_PCT = 3.0
ALERT_TRIGGER_REASON = "3pct_volatility"


@dataclass
class PriceAlert:
    """Represents a triggered price alert.

    Attributes:
        instrument_name: Name of the instrument (e.g., 'cai_cotton').
        current_price: Latest normalized USD price.
        previous_price: Previous day normalized USD price.
        change_pct: Percentage change from previous day.
        trigger_reason: Reason for the alert.
    """

    instrument_name: str
    current_price: float
    previous_price: float
    change_pct: float
    trigger_reason: str = ALERT_TRIGGER_REASON

    def format_message(self) -> str:
        """Format the alert as a human-readable message."""
        direction = "up" if self.change_pct > 0 else "down"
        return (
            f"VOLATILITY ALERT: {self.instrument_name}\n"
            f"Price moved {direction} {abs(self.change_pct):.2f}%\n"
            f"Previous: ${self.previous_price:.2f}\n"
            f"Current: ${self.current_price:.2f}"
        )

    def to_payload(self) -> dict[str, Any]:
        """Convert to a dict suitable for alert_log message_payload."""
        return {
            "instrument_name": self.instrument_name,
            "current_price": self.current_price,
            "previous_price": self.previous_price,
            "change_pct": self.change_pct,
            "trigger_reason": self.trigger_reason,
        }


def compute_price_change_pct(current: float, previous: float) -> float:
    """Compute percentage change between two prices.

    Args:
        current: Latest price value.
        previous: Previous price value.

    Returns:
        Signed percentage change.
    """
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100.0


def check_volatility(
    current_price: float,
    previous_price: float,
    instrument_name: str,
    threshold_pct: float = DEFAULT_THRESHOLD_PCT,
) -> PriceAlert | None:
    """Check if a price movement exceeds the volatility threshold.

    Args:
        current_price: Latest normalized USD price.
        previous_price: Previous day normalized USD price.
        instrument_name: Name of the instrument.
        threshold_pct: Percentage threshold for triggering an alert.

    Returns:
        A PriceAlert if threshold exceeded, None otherwise.
    """
    if previous_price <= 0:
        logger.warning(f"Invalid previous price for {instrument_name}: {previous_price}")
        return None

    change_pct = compute_price_change_pct(current_price, previous_price)

    if abs(change_pct) >= threshold_pct:
        alert = PriceAlert(
            instrument_name=instrument_name,
            current_price=current_price,
            previous_price=previous_price,
            change_pct=change_pct,
        )
        logger.info(
            f"Volatility alert triggered for {instrument_name}: "
            f"{change_pct:.2f}% (threshold: {threshold_pct}%)"
        )
        return alert

    return None


def check_volatility_with_suppression(
    current_price: float,
    previous_price: float,
    instrument_name: str,
    threshold_pct: float = DEFAULT_THRESHOLD_PCT,
) -> PriceAlert | None:
    """Check volatility with alert suppression applied.

    Args:
        current_price: Latest normalized USD price.
        previous_price: Previous day normalized USD price.
        instrument_name: Name of the instrument.
        threshold_pct: Percentage threshold for triggering an alert.

    Returns:
        A PriceAlert if threshold exceeded and not suppressed, None otherwise.
    """
    alert = check_volatility(current_price, previous_price, instrument_name, threshold_pct)
    if alert is None:
        return None

    suppressor = get_suppressor()
    if not suppressor.should_send_alert(instrument_name, ALERT_TRIGGER_REASON):
        logger.info(f"Alert suppressed for {instrument_name} (within suppression window)")
        return None

    return alert


async def scan_and_trigger_alerts(
    repository: Any,
    instrument_names: list[str] | None = None,
    threshold_pct: float = DEFAULT_THRESHOLD_PCT,
) -> list[PriceAlert]:
    """Scan price history for volatility and return triggered alerts.

    Queries the repository for the two most recent price records per
    instrument and checks if the delta exceeds the threshold.

    Args:
        repository: Database repository instance.
        instrument_names: Optional list of instruments to scan. If None, scans all.
        threshold_pct: Percentage threshold for triggering an alert.

    Returns:
        List of triggered PriceAlert objects (not yet suppressed).
    """
    alerts: list[PriceAlert] = []

    instruments = instrument_names or []
    if not instruments:
        records = await repository.get_price_records(limit=50)
        instruments = list({r.source_name for r in records})

    for instrument in instruments:
        records = await repository.get_price_records(source_name=instrument, limit=2)
        if len(records) < 2:
            logger.debug(f"Insufficient price data for {instrument} to check volatility")
            continue

        latest = records[0]
        previous = records[1]

        current_price = float(latest.normalized_usd)
        previous_price = float(previous.normalized_usd)

        alert = check_volatility(current_price, previous_price, instrument, threshold_pct)
        if alert is not None:
            alerts.append(alert)

    return alerts

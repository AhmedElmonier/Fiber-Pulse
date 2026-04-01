"""Scheduler for automated market report delivery.

Configures APScheduler to send market pulse reports 4x daily
at 09:00, 12:00, 15:00, and 18:00 Cairo time (Africa/Cairo).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone as pytz_timezone

logger = logging.getLogger(__name__)

CAIRO_TZ = "Africa/Cairo"

REPORT_HOURS = [9, 12, 15, 18]


def get_cairo_timezone() -> Any:
    """Get the Cairo timezone object.

    Returns:
        A pytz timezone for Africa/Cairo.
    """
    return pytz_timezone(CAIRO_TZ)


def create_report_scheduler(
    report_callback: Any,
) -> AsyncIOScheduler:
    """Create and configure the APScheduler with Cairo-time triggers.

    Args:
        report_callback: Async callable invoked at each scheduled slot.
            Must accept no positional arguments.

    Returns:
        A configured (but not yet started) AsyncIOScheduler.
    """
    scheduler = AsyncIOScheduler(timezone=get_cairo_timezone())

    for hour in REPORT_HOURS:
        scheduler.add_job(
            report_callback,
            trigger=CronTrigger(hour=hour, minute=0, timezone=get_cairo_timezone()),
            id=f"market_report_{hour:02d}",
            name=f"Market Report {hour:02d}:00 Cairo",
            replace_existing=True,
        )

    return scheduler


def get_next_report_time() -> datetime:
    """Compute the next scheduled report time in Cairo timezone.

    Returns:
        The next datetime (Cairo-aware) when a report will fire.
    """
    cairo_tz = get_cairo_timezone()
    now = datetime.now(cairo_tz)

    for hour in REPORT_HOURS:
        candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if candidate > now:
            return candidate

    # All today's slots have passed; tomorrow's first slot
    tomorrow = now + timedelta(days=1)
    return tomorrow.replace(hour=REPORT_HOURS[0], minute=0, second=0, microsecond=0)


def compose_market_report(
    price_records: list[Any],
    freight_records: list[Any],
    sentiment_records: list[Any],
) -> str:
    """Compose a market report message from price, freight, and sentiment data.

    Args:
        price_records: Recent price history records (latest first).
        freight_records: Recent freight rate records (latest first).
        sentiment_records: Recent sentiment event records (latest first).

    Returns:
        A formatted multi-section report string.
    """
    sections: list[str] = []
    sections.append("DAILY MARKET PULSE\n" + "=" * 30)

    # --- Price Section ---
    sections.append("\nPRICE UPDATE")
    if price_records:
        latest = price_records[0]
        price = getattr(latest, "normalized_usd", None) or getattr(latest, "raw_price", 0)
        source = getattr(latest, "source_name", "Unknown")
        timestamp = getattr(latest, "timestamp_utc", None)
        ts_str = timestamp.strftime("%Y-%m-%d %H:%M UTC") if timestamp else "N/A"
        sections.append(f"  {source}: ${float(price):.2f}  ({ts_str})")

        if len(price_records) >= 2:
            prev = price_records[1]
            prev_price = getattr(prev, "normalized_usd", None) or getattr(prev, "raw_price", 0)
            change = _pct_change(float(price), float(prev_price))
            direction = "up" if change >= 0 else "down"
            sections.append(f"  Change: {direction} {abs(change):.2f}%")
    else:
        sections.append("  No price data available.")

    # --- Freight Section ---
    sections.append("\nFREIGHT RATES")
    if freight_records:
        seen_routes: set[str] = set()
        for rec in freight_records[:4]:
            route = getattr(rec, "route", None) or getattr(rec, "source_name", "Unknown")
            if route in seen_routes:
                continue
            seen_routes.add(route)
            price = getattr(rec, "normalized_usd", None) or getattr(rec, "raw_price", 0)
            sections.append(f"  {route}: ${float(price):.2f}")
    else:
        sections.append("  No freight data available.")

    # --- Sentiment Section ---
    sections.append("\nMARKET SENTIMENT")
    if sentiment_records:
        for event in sentiment_records[:3]:
            label = getattr(event, "sentiment_score", None)
            if label is not None and hasattr(label, "value"):
                label_str = label.value.upper()
            else:
                label_str = str(label) if label is not None else "UNKNOWN"
            headline = getattr(event, "headline", "")
            confidence = getattr(event, "confidence", 0)
            sections.append(f"  [{label_str}] {headline} (conf: {confidence:.0%})")
    else:
        sections.append("  No sentiment data available.")

    sections.append("\n" + "=" * 30)
    return "\n".join(sections)


def _pct_change(current: float, previous: float) -> float:
    """Compute signed percentage change."""
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100.0

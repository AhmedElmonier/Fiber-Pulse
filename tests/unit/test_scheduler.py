"""Unit tests for scheduler configuration and Cairo-timezone offset.

Tests the APScheduler setup, cron triggers, timezone handling,
and market report composition logic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytz import timezone as pytz_timezone


class TestSchedulerConfiguration:
    """Tests for APScheduler Cairo-timezone configuration."""

    def test_report_hours_constant(self):
        """Verify the 4 daily report hours are correct."""
        from src.bot.scheduler import REPORT_HOURS

        assert REPORT_HOURS == [9, 12, 15, 18]

    def test_cairo_timezone_loads(self):
        """Verify Cairo timezone resolves correctly."""
        from src.bot.scheduler import get_cairo_timezone

        tz = get_cairo_timezone()
        assert tz.zone == "Africa/Cairo"

    def test_create_scheduler_registers_four_jobs(self):
        """Verify 4 cron jobs are added for the 4 report slots."""
        from src.bot.scheduler import create_report_scheduler

        callback = AsyncMock()
        scheduler = create_report_scheduler(callback)

        jobs = scheduler.get_jobs()
        assert len(jobs) == 4

        job_ids = {j.id for j in jobs}
        assert job_ids == {
            "market_report_09",
            "market_report_12",
            "market_report_15",
            "market_report_18",
        }

    def test_scheduler_uses_cairo_timezone(self):
        """Verify scheduler jobs target Cairo timezone."""
        from src.bot.scheduler import create_report_scheduler

        callback = AsyncMock()
        scheduler = create_report_scheduler(callback)

        for job in scheduler.get_jobs():
            trigger_tz = job.trigger.timezone
            # zoneinfo.ZoneInfo uses .key; pytz uses .zone
            tz_name = getattr(trigger_tz, "key", None) or getattr(trigger_tz, "zone", None)
            assert tz_name == "Africa/Cairo"

    def test_scheduler_jobs_run_at_correct_hours(self):
        """Verify each cron trigger fires at the expected hour."""
        from src.bot.scheduler import create_report_scheduler

        callback = AsyncMock()
        scheduler = create_report_scheduler(callback)

        expected_hours = {9, 12, 15, 18}
        actual_hours: set[int] = set()

        for job in scheduler.get_jobs():
            # fields[5] is the hour field in APScheduler CronTrigger
            hour_field = job.trigger.fields[5]
            hour_str = str(hour_field)
            if hour_str.isdigit():
                actual_hours.add(int(hour_str))

        assert actual_hours == expected_hours


class TestCairoTimezoneOffset:
    """Tests for correct UTC offset handling for Cairo time."""

    def test_cairo_is_utc_plus_two_in_winter(self):
        """Cairo is UTC+2 during winter (EET)."""
        cairo_tz = pytz_timezone("Africa/Cairo")
        winter = cairo_tz.localize(datetime(2026, 1, 15, 12, 0, 0))
        offset = winter.utcoffset().total_seconds() / 3600
        assert offset == 2.0

    def test_cairo_is_utc_plus_three_in_summer(self):
        """Cairo is UTC+3 during summer (EEST) when DST applies."""
        cairo_tz = pytz_timezone("Africa/Cairo")
        summer = cairo_tz.localize(datetime(2026, 7, 15, 12, 0, 0))
        offset = summer.utcoffset().total_seconds() / 3600
        assert offset == 3.0

    def test_get_next_report_time_returns_future(self):
        """Next report time must always be in the future relative to now."""
        from src.bot.scheduler import get_next_report_time

        cairo_tz = pytz_timezone("Africa/Cairo")
        now = datetime.now(cairo_tz)
        next_report = get_next_report_time()

        assert next_report > now

    def test_get_next_report_time_is_cairo_aware(self):
        """Next report time must carry Cairo timezone info."""
        from src.bot.scheduler import get_next_report_time

        next_report = get_next_report_time()
        assert next_report.tzinfo is not None
        assert next_report.tzinfo.zone == "Africa/Cairo"

    def test_get_next_report_time_minute_is_zero(self):
        """Next report time must land on the hour (minute=0)."""
        from src.bot.scheduler import get_next_report_time

        next_report = get_next_report_time()
        assert next_report.minute == 0
        assert next_report.second == 0


class TestComposeMarketReport:
    """Tests for market report composition logic."""

    def _make_price_record(self, source: str, price: float, ts: datetime):
        rec = MagicMock()
        rec.source_name = source
        rec.normalized_usd = price
        rec.timestamp_utc = ts
        return rec

    def _make_freight_record(self, route: str, price: float):
        rec = MagicMock()
        rec.route = route
        rec.normalized_usd = price
        return rec

    def _make_sentiment_event(self, label: str, headline: str, confidence: float):
        rec = MagicMock()
        rec.sentiment_score = MagicMock()
        rec.sentiment_score.value = label
        rec.headline = headline
        rec.confidence = confidence
        return rec

    def test_report_contains_all_sections(self):
        """Report must include Price, Freight, and Sentiment sections."""
        from src.bot.scheduler import compose_market_report

        now = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
        prices = [self._make_price_record("cai_cotton", 85.50, now)]
        freight = [self._make_freight_record("Med", 1150.0)]
        sentiment = [self._make_sentiment_event("bullish", "Cotton demand rises", 0.82)]

        report = compose_market_report(prices, freight, sentiment)

        assert "PRICE UPDATE" in report
        assert "FREIGHT RATES" in report
        assert "MARKET SENTIMENT" in report

    def test_report_shows_price_and_change(self):
        """Report shows current price and percentage change vs previous."""
        from src.bot.scheduler import compose_market_report

        now = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
        prices = [
            self._make_price_record("cai_cotton", 104.0, now),
            self._make_price_record("cai_cotton", 100.0, now),
        ]

        report = compose_market_report(prices, [], [])

        assert "$104.00" in report
        assert "4.00%" in report
        assert "up" in report

    def test_report_shows_freight_rates(self):
        """Report lists available freight routes."""
        from src.bot.scheduler import compose_market_report

        freight = [
            self._make_freight_record("Mediterranean", 1150.0),
            self._make_freight_record("Shanghai-Rotterdam", 3500.0),
        ]

        report = compose_market_report([], freight, [])

        assert "Mediterranean" in report
        assert "Shanghai-Rotterdam" in report

    def test_report_shows_sentiment(self):
        """Report includes sentiment headlines."""
        from src.bot.scheduler import compose_market_report

        sentiment = [self._make_sentiment_event("bullish", "Cotton demand rises", 0.82)]

        report = compose_market_report([], [], sentiment)

        assert "BULLISH" in report
        assert "Cotton demand rises" in report

    def test_report_handles_empty_data(self):
        """Report gracefully handles all-empty inputs."""
        from src.bot.scheduler import compose_market_report

        report = compose_market_report([], [], [])

        assert "No price data available" in report
        assert "No freight data available" in report
        assert "No sentiment data available" in report

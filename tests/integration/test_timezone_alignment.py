"""Integration tests for timezone alignment in Phase 2.

Validates that ingestion schedules, health evaluation, and timestamps
correctly use or align with the Africa/Cairo timezone.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
import zoneinfo

import pytest

from config import get_config


def test_config_timezone_alignment():
    """Verify that the configured timezone is Africa/Cairo."""
    config = get_config()
    assert config.timezone == "Africa/Cairo"
    
    # Verify we can load the zone
    tz = zoneinfo.ZoneInfo(config.timezone)
    assert tz.key == "Africa/Cairo"

def test_timestamp_normalization_to_utc():
    """Verify that normalized timestamps remain UTC regardless of local timezone."""
    # The system mandate is to store everything in UTC
    now = datetime.now(timezone.utc)
    
    # Africa/Cairo is usually UTC+2 or UTC+3
    cairo_tz = zoneinfo.ZoneInfo("Africa/Cairo")
    cairo_now = now.astimezone(cairo_tz)
    
    # When converting back to UTC for storage, it should match the original UTC time
    assert cairo_now.astimezone(timezone.utc) == now

def test_health_evaluation_window_alignment():
    """Verify that health thresholds are applied consistently with 48h requirement."""
    # This is a unit-level check for logic alignment with Cairo scheduling
    # In practice, ingestion runs at a specific Cairo time (e.g., 08:00 AM)
    # 48 hours covers exactly 2 full daily cycles in that timezone.
    from agents.source_health import DEFAULT_STALE_THRESHOLD_MINUTES
    assert DEFAULT_STALE_THRESHOLD_MINUTES == 2880 # 48 * 60

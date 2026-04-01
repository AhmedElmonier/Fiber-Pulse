"""Integration tests for price alert trigger and suppression.

Tests the volatility alerting pipeline including trigger detection,
suppression logic, and alert broadcasting.
"""

from __future__ import annotations

import pytest


class TestPriceAlertTrigger:
    """Tests for the volatility alert trigger logic."""

    def test_alert_triggered_above_threshold(self):
        """Test alert is triggered when price moves >3%."""
        from src.utils.alert_trigger import check_volatility

        alert = check_volatility(
            current_price=104.0,
            previous_price=100.0,
            instrument_name="cai_cotton",
        )

        assert alert is not None
        assert alert.instrument_name == "cai_cotton"
        assert alert.change_pct == pytest.approx(4.0, abs=0.01)
        assert alert.current_price == 104.0
        assert alert.previous_price == 100.0

    def test_alert_triggered_below_negative_threshold(self):
        """Test alert is triggered when price drops >3%."""
        from src.utils.alert_trigger import check_volatility

        alert = check_volatility(
            current_price=96.0,
            previous_price=100.0,
            instrument_name="cai_cotton",
        )

        assert alert is not None
        assert alert.change_pct == pytest.approx(-4.0, abs=0.01)

    def test_no_alert_below_threshold(self):
        """Test no alert when price move is <3%."""
        from src.utils.alert_trigger import check_volatility

        alert = check_volatility(
            current_price=102.0,
            previous_price=100.0,
            instrument_name="cai_cotton",
        )

        assert alert is None

    def test_alert_at_exact_threshold(self):
        """Test alert is triggered at exactly 3%."""
        from src.utils.alert_trigger import check_volatility

        alert = check_volatility(
            current_price=103.0,
            previous_price=100.0,
            instrument_name="cai_cotton",
        )

        assert alert is not None
        assert alert.change_pct == pytest.approx(3.0, abs=0.01)

    def test_no_alert_with_zero_previous_price(self):
        """Test no alert when previous price is zero (invalid data)."""
        from src.utils.alert_trigger import check_volatility

        alert = check_volatility(
            current_price=100.0,
            previous_price=0.0,
            instrument_name="cai_cotton",
        )

        assert alert is None

    def test_custom_threshold(self):
        """Test alert with a custom threshold of 5%."""
        from src.utils.alert_trigger import check_volatility

        alert = check_volatility(
            current_price=104.0,
            previous_price=100.0,
            instrument_name="cai_cotton",
            threshold_pct=5.0,
        )

        assert alert is None

    def test_compute_price_change_pct(self):
        """Test percentage change calculation."""
        from src.utils.alert_trigger import compute_price_change_pct

        assert compute_price_change_pct(104.0, 100.0) == pytest.approx(4.0)
        assert compute_price_change_pct(96.0, 100.0) == pytest.approx(-4.0)
        assert compute_price_change_pct(100.0, 100.0) == pytest.approx(0.0)
        assert compute_price_change_pct(100.0, 0.0) == pytest.approx(0.0)


class TestAlertFormatting:
    """Tests for alert message formatting."""

    def test_format_message_direction_up(self):
        """Test message shows 'up' for positive change."""
        from src.utils.alert_trigger import PriceAlert

        alert = PriceAlert(
            instrument_name="cai_cotton",
            current_price=104.0,
            previous_price=100.0,
            change_pct=4.0,
        )

        msg = alert.format_message()
        assert "up" in msg
        assert "4.00%" in msg
        assert "cai_cotton" in msg

    def test_format_message_direction_down(self):
        """Test message shows 'down' for negative change."""
        from src.utils.alert_trigger import PriceAlert

        alert = PriceAlert(
            instrument_name="cai_cotton",
            current_price=96.0,
            previous_price=100.0,
            change_pct=-4.0,
        )

        msg = alert.format_message()
        assert "down" in msg

    def test_to_payload(self):
        """Test payload serialization."""
        from src.utils.alert_trigger import PriceAlert

        alert = PriceAlert(
            instrument_name="cai_cotton",
            current_price=104.0,
            previous_price=100.0,
            change_pct=4.0,
        )

        payload = alert.to_payload()
        assert payload["instrument_name"] == "cai_cotton"
        assert payload["current_price"] == 104.0
        assert payload["previous_price"] == 100.0
        assert payload["change_pct"] == 4.0
        assert payload["trigger_reason"] == "3pct_volatility"


class TestAlertSuppression:
    """Tests for alert suppression integration."""

    def test_suppression_prevents_duplicate_alerts(self):
        """Test that suppressor blocks repeated alerts within the window."""
        from src.utils.alert_suppressor import AlertSuppressor
        from src.utils.alert_trigger import (
            ALERT_TRIGGER_REASON,
            check_volatility_with_suppression,
        )

        suppressor = AlertSuppressor(suppression_window_hours=1)

        # Monkey-patch the global suppressor
        import src.utils.alert_suppressor as sup_module

        old = sup_module._suppressor_instance
        sup_module._suppressor_instance = suppressor

        try:
            # First alert should pass
            alert = check_volatility_with_suppression(
                current_price=104.0,
                previous_price=100.0,
                instrument_name="cai_cotton",
            )
            assert alert is not None

            # Record it
            suppressor.record_alert_sent("cai_cotton", ALERT_TRIGGER_REASON)

            # Second alert should be suppressed
            alert2 = check_volatility_with_suppression(
                current_price=105.0,
                previous_price=100.0,
                instrument_name="cai_cotton",
            )
            assert alert2 is None
        finally:
            sup_module._suppressor_instance = old

    def test_suppression_allows_different_instruments(self):
        """Test that suppression is per-instrument."""
        from src.utils.alert_suppressor import AlertSuppressor
        from src.utils.alert_trigger import (
            ALERT_TRIGGER_REASON,
            check_volatility_with_suppression,
        )

        suppressor = AlertSuppressor(suppression_window_hours=1)

        import src.utils.alert_suppressor as sup_module

        old = sup_module._suppressor_instance
        sup_module._suppressor_instance = suppressor

        try:
            # Alert for cai_cotton
            alert1 = check_volatility_with_suppression(
                current_price=104.0,
                previous_price=100.0,
                instrument_name="cai_cotton",
            )
            assert alert1 is not None
            suppressor.record_alert_sent("cai_cotton", ALERT_TRIGGER_REASON)

            # Alert for a different instrument should still pass
            alert2 = check_volatility_with_suppression(
                current_price=52.0,
                previous_price=50.0,
                instrument_name="wci_freight",
            )
            assert alert2 is not None
        finally:
            sup_module._suppressor_instance = old

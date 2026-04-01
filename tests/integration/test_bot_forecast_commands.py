"""Integration tests for bot forecast commands.

Tests /buy and /outlook handler integration.
"""

from __future__ import annotations

import io

import pytest


class TestBotForecastCommands:
    """Tests for forecast command handlers."""

    def test_chart_generation_returns_bytes(self):
        """Test chart generation produces valid image bytes."""
        from src.charts.fan_chart import generate_fan_chart

        dates = ["2025-01-01", "2025-01-02", "2025-01-03"]
        predicted = [85.0, 86.0, 87.0]
        lower = [80.0, 81.0, 82.0]
        upper = [90.0, 91.0, 92.0]

        result = generate_fan_chart(dates, predicted, lower, upper)

        assert isinstance(result, io.BytesIO)
        result.seek(0)
        data = result.read()
        assert len(data) > 0

    def test_forecast_message_format(self):
        """Test forecast message is properly formatted."""
        from src.charts.fan_chart import generate_simple_forecast_message

        msg = generate_simple_forecast_message(
            "cai_spot", 85.50, 80.00, 91.00, 24
        )

        assert "cai_spot" in msg
        assert "85.50" in msg
        assert "80.00" in msg
        assert "91.00" in msg
        assert "24h" in msg

    def test_buy_signal_message_buy(self):
        """Test BUY signal message format."""
        from src.charts.fan_chart import generate_buy_signal_message

        msg = generate_buy_signal_message(
            "cai_spot", "BUY", 0.85, 85.50, 80.00, 91.00
        )

        assert "BUY" in msg
        assert "85.50" in msg
        assert "80.00" in msg
        assert "91.00" in msg

    def test_buy_signal_message_sell(self):
        """Test SELL signal message format."""
        from src.charts.fan_chart import generate_buy_signal_message

        msg = generate_buy_signal_message(
            "cai_spot", "SELL", 0.75, 85.50, 80.00, 91.00
        )

        assert "SELL" in msg

    def test_buy_signal_message_hold(self):
        """Test HOLD signal message format."""
        from src.charts.fan_chart import generate_buy_signal_message

        msg = generate_buy_signal_message(
            "cai_spot", "HOLD", 0.55, 85.50, 80.00, 91.00
        )

        assert "HOLD" in msg


class TestFanChartIntegration:
    """Integration tests for fan chart with supply/demand intervals."""

    def test_multiple_day_chart(self):
        """Test chart with multiple days."""
        from src.charts.fan_chart import generate_fan_chart

        dates = [f"2025-01-{i:02d}" for i in range(1, 6)]
        predicted = [80 + i for i in range(5)]
        lower = [75 + i for i in range(5)]
        upper = [85 + i for i in range(5)]

        result = generate_fan_chart(dates, predicted, lower, upper)

        result.seek(0)
        assert len(result.read()) > 0

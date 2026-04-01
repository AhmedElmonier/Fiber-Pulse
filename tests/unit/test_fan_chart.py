"""Unit tests for fan chart generation."""

from __future__ import annotations

import io

import pytest


class TestFanChart:
    """Tests for fan chart generation."""

    def test_generate_fan_chart_empty_raises(self):
        """Test that empty data raises ValueError."""
        from src.charts.fan_chart import generate_fan_chart

        with pytest.raises(ValueError, match="empty"):
            generate_fan_chart([], [], [], [])

    def test_generate_fan_chart_basic(self):
        """Test basic fan chart generation."""
        from src.charts.fan_chart import generate_fan_chart

        dates = ["2025-01-01", "2025-01-02", "2025-01-03"]
        predicted = [85.0, 86.0, 87.0]
        lower = [80.0, 81.0, 82.0]
        upper = [90.0, 91.0, 92.0]

        result = generate_fan_chart(dates, predicted, lower, upper)

        assert isinstance(result, io.BytesIO)
        result.seek(0)
        assert len(result.read()) > 0

    def test_generate_fan_chart_mismatched_lengths(self):
        """Test mismatched array lengths raise error."""
        from src.charts.fan_chart import generate_fan_chart

        dates = ["2025-01-01", "2025-01-02"]
        predicted = [85.0, 86.0, 87.0]
        lower = [80.0]
        upper = [90.0]

        with pytest.raises(ValueError):
            generate_fan_chart(dates, predicted, lower, upper)

    def test_generate_simple_forecast_message(self):
        """Test forecast message generation."""
        from src.charts.fan_chart import generate_simple_forecast_message

        msg = generate_simple_forecast_message(
            "cai_spot",
            85.50,
            80.00,
            91.00,
            24,
        )

        assert "cai_spot" in msg
        assert "85.50" in msg
        assert "80.00" in msg
        assert "91.00" in msg

    def test_generate_buy_signal_message_buy(self):
        """Test BUY signal message."""
        from src.charts.fan_chart import generate_buy_signal_message

        msg = generate_buy_signal_message(
            "cai_spot",
            "BUY",
            0.85,
            85.50,
            80.00,
            91.00,
        )

        assert "🟢" in msg
        assert "BUY" in msg
        assert "85%" in msg

    def test_generate_buy_signal_message_sell(self):
        """Test SELL signal message."""
        from src.charts.fan_chart import generate_buy_signal_message

        msg = generate_buy_signal_message(
            "cai_spot",
            "SELL",
            0.75,
            85.50,
            80.00,
            91.00,
        )

        assert "🔴" in msg
        assert "SELL" in msg

    def test_generate_buy_signal_message_hold(self):
        """Test HOLD signal message."""
        from src.charts.fan_chart import generate_buy_signal_message

        msg = generate_buy_signal_message(
            "cai_spot",
            "HOLD",
            0.55,
            85.50,
            80.00,
            91.00,
        )

        assert "🟡" in msg
        assert "HOLD" in msg

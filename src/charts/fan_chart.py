"""Fan chart generation using Matplotlib.

Creates visualization for price forecast confidence intervals.
"""

from __future__ import annotations

import io


def generate_fan_chart(
    dates: list[str],
    predicted_values: list[float],
    lower_bounds: list[float],
    upper_bounds: list[float],
    title: str = "Price Forecast with Confidence Intervals",
    xlabel: str = "Date",
    ylabel: str = "Price (USD)",
) -> io.BytesIO:
    """Generate a fan chart visualization.

    Args:
        dates: List of date labels.
        predicted_values: Point predictions.
        lower_bounds: Lower confidence bounds.
        upper_bounds: Upper confidence bounds.
        title: Chart title.
        xlabel: X-axis label.
        ylabel: Y-axis label.

    Returns:
        BytesIO image buffer.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required for chart generation")

    if not dates or not predicted_values:
        raise ValueError("dates and predicted_values cannot be empty")

    if len(lower_bounds) != len(upper_bounds):
        raise ValueError("lower_bounds and upper_bounds must have the same length")
    if len(lower_bounds) != len(dates) or len(lower_bounds) != len(predicted_values):
        raise ValueError(
            "lower_bounds, upper_bounds, dates, and predicted_values must all have the same length"
        )

    fig, ax = plt.subplots(figsize=(10, 6))

    x = range(len(dates))

    ax.fill_between(
        x,
        lower_bounds,
        upper_bounds,
        alpha=0.3,
        color="blue",
        label="Confidence Interval (95%)",
    )

    ax.plot(x, predicted_values, "b-", linewidth=2, label="Predicted Price")
    ax.plot(x, upper_bounds, "b--", alpha=0.5, linewidth=1)
    ax.plot(x, lower_bounds, "b--", alpha=0.5, linewidth=1)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    step = max(1, len(x) // 5)
    tick_indices = list(range(0, len(dates), step))
    ax.set_xticks([x[i] for i in tick_indices])
    ax.set_xticklabels([dates[i] for i in tick_indices], rotation=45)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=100)
    buffer.seek(0)
    plt.close(fig)

    return buffer


def generate_simple_forecast_message(
    source: str,
    predicted_value: float,
    lower_bound: float,
    upper_bound: float,
    horizon_hours: int = 24,
) -> str:
    """Generate a formatted forecast message for Telegram.

    Args:
        source: Source name (e.g., 'cai_spot').
        predicted_value: Point forecast.
        lower_bound: Lower confidence bound.
        upper_bound: Upper confidence bound.
        horizon_hours: Forecast horizon.

    Returns:
        Formatted message string.
    """
    return (
        f"📊 *Market Outlook - {source}*\n\n"
        f"Prediction: ${predicted_value:.2f}\n"
        f"95% CI: [${lower_bound:.2f} - ${upper_bound:.2f}]\n"
        f"Horizon: {horizon_hours}h\n\n"
        f"_Confidence intervals widen for longer horizons._"
    )


def generate_buy_signal_message(
    source: str,
    signal: str,
    confidence: float,
    predicted_value: float,
    lower_bound: float,
    upper_bound: float,
) -> str:
    """Generate a buy signal message for Telegram.

    Args:
        source: Source name.
        signal: 'BUY', 'SELL', or 'HOLD'.
        confidence: Signal confidence (0-1).
        predicted_value: Predicted price.
        lower_bound: Lower bound.
        upper_bound: Upper bound.

    Returns:
        Formatted message string.
    """
    emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(signal, "⚪")

    return (
        f"{emoji} *{signal} Signal - {source}*\n\n"
        f"Confidence: {confidence:.0%}\n"
        f"Price: ${predicted_value:.2f} [${lower_bound:.2f} - ${upper_bound:.2f}]\n\n"
        f"_This is automated advice. Trade at your own risk._"
    )

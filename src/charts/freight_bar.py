"""Freight bar chart generation using Matplotlib.

Creates a bar chart comparing freight rates across routes,
with optional week-over-week comparison.
"""

from __future__ import annotations

import io


def generate_freight_bar_chart(
    route_labels: list[str],
    current_rates: list[float],
    previous_rates: list[float] | None = None,
    title: str = "Freight Rates by Route",
    ylabel: str = "Rate (USD)",
) -> io.BytesIO:
    """Generate a grouped bar chart for freight rate comparison.

    Args:
        route_labels: Route names for x-axis labels.
        current_rates: Current rate values per route.
        previous_rates: Optional previous-week rates for comparison.
        title: Chart title.
        ylabel: Y-axis label.

    Returns:
        BytesIO image buffer containing the PNG chart.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required for chart generation")

    if not route_labels or not current_rates:
        raise ValueError("route_labels and current_rates cannot be empty")

    fig, ax = plt.subplots(figsize=(10, 6))

    x_positions = list(range(len(route_labels)))
    bar_width = 0.35

    if previous_rates and len(previous_rates) == len(route_labels):
        bars_prev = ax.bar(
            [p - bar_width / 2 for p in x_positions],
            previous_rates,
            bar_width,
            label="Previous Week",
            color="#93c5fd",
            edgecolor="#3b82f6",
            linewidth=0.8,
        )
        bars_curr = ax.bar(
            [p + bar_width / 2 for p in x_positions],
            current_rates,
            bar_width,
            label="Current",
            color="#3b82f6",
            edgecolor="#1d4ed8",
            linewidth=0.8,
        )
        ax.legend(loc="best")
    else:
        bars_curr = ax.bar(
            x_positions,
            current_rates,
            0.6,
            color="#3b82f6",
            edgecolor="#1d4ed8",
            linewidth=0.8,
        )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(route_labels, rotation=30, ha="right", fontsize=9)
    ax.grid(axis="y", alpha=0.3)

    for bar in bars_curr:
        height = bar.get_height()
        ax.annotate(
            f"${height:,.0f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=100)
    buffer.seek(0)
    plt.close(fig)

    return buffer


def format_freight_message(
    route_data: list[dict],
) -> str:
    """Format freight rates as a text message for Telegram.

    Args:
        route_data: List of dicts with keys: route, current_rate,
            and optionally previous_rate and change_pct.

    Returns:
        Formatted multi-line message string.
    """
    lines = ["FREIGHT RATES", "=" * 28]

    for entry in route_data:
        route = entry.get("route", "Unknown")
        rate = entry.get("current_rate", 0.0)
        line = f"  {route}: ${rate:,.2f}"

        prev = entry.get("previous_rate")
        if prev is not None and prev > 0:
            change = entry.get("change_pct")
            if change is None:
                change = ((rate - prev) / prev) * 100
            direction = "up" if change >= 0 else "down"
            line += f"  ({direction} {abs(change):.1f}%)"

        lines.append(line)

    if not route_data:
        lines.append("  No freight data available.")

    lines.append("=" * 28)
    return "\n".join(lines)

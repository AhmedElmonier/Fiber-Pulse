"""Price trend chart generation using Matplotlib.

Creates a sparkline-style line chart for historical price visualization.
"""

from __future__ import annotations

import io


def generate_trend_chart(
    dates: list[str],
    prices: list[float],
    title: str = "Price History (30 Days)",
    xlabel: str = "Date",
    ylabel: str = "Price (USD)",
) -> io.BytesIO:
    """Generate a sparkline-style price trend chart.

    Args:
        dates: List of date labels (oldest first).
        prices: Corresponding price values.
        title: Chart title.
        xlabel: X-axis label.
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

    if not dates or not prices:
        raise ValueError("dates and prices cannot be empty")

    fig, ax = plt.subplots(figsize=(10, 4))

    x = range(len(dates))

    ax.plot(x, prices, color="#3b82f6", linewidth=1.8, marker="", zorder=3)
    ax.fill_between(x, prices, min(prices) * 0.98, alpha=0.12, color="#3b82f6")

    if len(prices) >= 2:
        first = prices[0]
        last = prices[-1]
        color = "#16a34a" if last >= first else "#dc2626"
        ax.plot(
            len(prices) - 1,
            last,
            marker="o",
            markersize=7,
            color=color,
            zorder=4,
        )

    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)

    step = max(1, len(x) // 6)
    tick_indices = list(range(0, len(dates), step))
    ax.set_xticks([x[i] for i in tick_indices])
    ax.set_xticklabels([dates[i] for i in tick_indices], rotation=40, ha="right", fontsize=8)
    ax.grid(True, alpha=0.25, linewidth=0.5)

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=100)
    buffer.seek(0)
    plt.close(fig)

    return buffer


def format_history_table(
    dates: list[str],
    prices: list[float],
) -> str:
    """Format price history as a compact text table for Telegram.

    Args:
        dates: Date labels (oldest first).
        prices: Corresponding prices.

    Returns:
        Formatted table string with Date | Price | % Change columns.
    """
    lines = ["PRICE HISTORY (30 DAYS)", "=" * 34]
    lines.append(f"  {'Date':<12} {'Price':>10} {'Change':>8}")
    lines.append("  " + "-" * 32)

    for i, (date, price) in enumerate(zip(dates, prices)):
        if i == 0:
            change_str = "  ---"
        else:
            prev = prices[i - 1]
            if prev > 0:
                pct = ((price - prev) / prev) * 100
                sign = "+" if pct >= 0 else ""
                change_str = f"{sign}{pct:.1f}%"
            else:
                change_str = "  ---"

        short_date = date[-5:] if len(date) >= 5 else date
        lines.append(f"  {short_date:<12} ${price:>9.2f} {change_str:>8}")

    lines.append("=" * 34)
    return "\n".join(lines)

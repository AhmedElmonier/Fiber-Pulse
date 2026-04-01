"""Confidence interval decay logic for FiberPulse forecasts.

Implements the 20% uncertainty widening rule (SC-003) when data feeds are stale.
"""

from __future__ import annotations

from dataclasses import dataclass

# The proportion by which confidence intervals are widened for stale data.
DEFAULT_DECAY_FACTOR = 0.20


@dataclass
class DecayedInterval:
    """Result of applying confidence decay to a forecast interval.

    Attributes:
        lower_bound: Widened lower bound.
        upper_bound: Widened upper bound.
        is_decayed: Whether decay was applied.
        original_width: Width of the original interval.
        decayed_width: Width of the decayed interval.
    """

    lower_bound: float
    upper_bound: float
    is_decayed: bool
    original_width: float
    decayed_width: float


def apply_confidence_decay(
    predicted_value: float,
    lower_bound: float,
    upper_bound: float,
    is_stale: bool,
    decay_factor: float = DEFAULT_DECAY_FACTOR,
) -> DecayedInterval:
    """Widen confidence interval by the decay factor if data is stale.

    Applies the SC-003 rule: automatically widen the confidence interval
    by 20% when underlying data feeds are stale.

    Args:
        predicted_value: Point estimate for the forecast.
        lower_bound: Original lower confidence bound.
        upper_bound: Original upper confidence bound.
        is_stale: Whether the underlying data feeds are stale.
        decay_factor: Proportion to widen (default 0.20 = 20%).

    Returns:
        DecayedInterval with widened bounds if stale, original otherwise.
    """
    original_width = upper_bound - lower_bound

    if not is_stale:
        return DecayedInterval(
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            is_decayed=False,
            original_width=original_width,
            decayed_width=original_width,
        )

    half_widen = (original_width * decay_factor) / 2.0
    decayed_lower = lower_bound - half_widen
    decayed_upper = upper_bound + half_widen
    decayed_width = decayed_upper - decayed_lower

    return DecayedInterval(
        lower_bound=round(decayed_lower, 6),
        upper_bound=round(decayed_upper, 6),
        is_decayed=True,
        original_width=original_width,
        decayed_width=round(decayed_width, 6),
    )

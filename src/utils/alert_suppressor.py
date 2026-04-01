"""Alert suppression utility for the Telegram bot.

Provides logic to suppress duplicate alerts within a time window.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Any


class AlertSuppressor:
    """Utility to check and suppress duplicate alerts.

    Uses a simple in-memory store for demonstration. For production,
    use database-backed suppression with the alert_log table.
    """

    def __init__(self, suppression_window_hours: int = 1) -> None:
        """Initialize the suppressor.

        Args:
            suppression_window_hours: Hours to suppress duplicate alerts.
        """
        self.suppression_window_hours = suppression_window_hours
        self._sent_alerts: dict[str, datetime] = {}
        self._lock = threading.Lock()

    def should_send_alert(
        self,
        instrument_name: str,
        trigger_reason: str,
    ) -> bool:
        """Check if an alert should be sent."""
        with self._lock:
            key = self._make_key(instrument_name, trigger_reason)
            last_sent = self._sent_alerts.get(key)

            if last_sent is None:
                return True

            window = timedelta(hours=self.suppression_window_hours)
            if datetime.now(timezone.utc) - last_sent > window:
                return True

            return False

    def record_alert_sent(self, instrument_name: str, trigger_reason: str) -> None:
        """Record that an alert was sent."""
        with self._lock:
            key = self._make_key(instrument_name, trigger_reason)
            self._sent_alerts[key] = datetime.now(timezone.utc)

    def clear_suppression_cache(self, instrument_name: str | None = None) -> None:
        """Clear the suppression cache."""
        with self._lock:
            if instrument_name is None:
                self._sent_alerts.clear()
                return

            keys_to_remove = [
                k for k in self._sent_alerts.keys()
                if k.startswith(f"{instrument_name}:")
            ]
            for key in keys_to_remove:
                del self._sent_alerts[key]

    @staticmethod
    def _make_key(instrument_name: str, trigger_reason: str) -> str:
        """Create a cache key for an alert."""
        return f"{instrument_name}:{trigger_reason}"


_suppressor_instance: AlertSuppressor | None = None
_suppressor_lock = threading.Lock()


def get_suppressor() -> AlertSuppressor:
    """Get the global alert suppressor instance."""
    global _suppressor_instance
    if _suppressor_instance is None:
        with _suppressor_lock:
            if _suppressor_instance is None:
                _suppressor_instance = AlertSuppressor()
    return _suppressor_instance

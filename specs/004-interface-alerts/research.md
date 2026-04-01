# Research: Phase 4 — Interface & Alerts

## Decision: Telegram Bot Framework
- **Chosen**: `python-telegram-bot` (v20+)
- **Rationale**: It is the most robust, actively maintained, and feature-rich asynchronous library for Telegram in Python. It supports the latest Bot API features and fits perfectly with the project's async nature.
- **Alternatives considered**: `aiogram` (excellent but `python-telegram-bot` has a larger community and more documentation for the specific reporting use case).

## Decision: Chart Generation
- **Chosen**: `Matplotlib`
- **Rationale**: For Telegram, static images are preferred over interactive charts. Matplotlib is highly customizable for "fan charts" (using `fill_between` for confidence intervals) and bar charts. It can render to a buffer (BytesIO) and be sent directly via the Bot API without saving to disk.
- **Alternatives considered**: `Plotly` (generates HTML/interactive, harder to convert to static images reliably on headless servers), `Seaborn` (good but Matplotlib is sufficient and more flexible for custom fan charts).

## Decision: Scheduling
- **Chosen**: `APScheduler` (AsyncIOScheduler)
- **Rationale**: It integrates seamlessly with `asyncio` and `python-telegram-bot`. It supports Cron-style triggers and can handle the Africa/Cairo timezone using `zoneinfo`.
- **Alternatives considered**: `Celery Beat` (too heavy for this scope), `Cron` (external to the app, harder to manage dynamic whitelists or internal state).

## Decision: Alert Suppression Logic
- **Chosen**: Database-backed suppression using `alert_log`
- **Rationale**: Since we already have PostgreSQL, checking the `alert_log` table for a record of the same instrument within the last 60 minutes is the most reliable and persistent way to handle suppression without adding Redis as a dependency.
- **Alternatives considered**: In-memory cache (lost on restart), Redis (adds operational complexity).

## Decision: Timezone Handling
- **Chosen**: `zoneinfo` (Python 3.9+)
- **Rationale**: Standard library approach for IANA timezones. Consistent with Python 3.12 requirement.
- **Alternatives considered**: `pytz` (older third-party library, superseded by the standard library approach).

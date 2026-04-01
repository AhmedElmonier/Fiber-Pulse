# Data Model: Phase 4 — Interface & Alerts

## New Tables

### Alert Log (`alert_log`)
Captures all notifications (alerts and scheduled reports) sent to users.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `BIGSERIAL PRIMARY KEY` | Primary key |
| `timestamp` | `TIMESTAMPTZ DEFAULT NOW()` | When the alert was sent |
| `instrument_name` | `TEXT NOT NULL` | Name of the instrument (e.g., 'cai_cotton', 'wci_freight') |
| `trigger_reason` | `TEXT NOT NULL` | Reason for alert (e.g., '3pct_volatility', 'scheduled_report') |
| `target_chat_id` | `BIGINT NOT NULL` | Telegram Chat/User ID recipient |
| `message_payload` | `JSONB` | Full content of the message sent (for audit) |
| `status` | `TEXT NOT NULL` | 'success' or 'failed' |

### Bot Command Log (`bot_command_log`)
Tracks user interactions for performance monitoring and audit.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `BIGSERIAL PRIMARY KEY` | Primary key |
| `user_id` | `BIGINT NOT NULL` | Telegram User ID of the caller |
| `command_name` | `TEXT NOT NULL` | Command invoked (e.g., '/buy', '/outlook') |
| `arguments` | `TEXT` | Optional arguments provided to the command |
| `timestamp` | `TIMESTAMPTZ DEFAULT NOW()` | When the command was received |
| `response_time_ms` | `INTEGER` | Time taken to respond (for SC-001) |

## Relationships
- `alert_log.instrument_name` should implicitly map to instrument identifiers used in `price_history` and `freight_rates`.
- `bot_command_log.user_id` must be present in the authorized `TELEGRAM_WHITELIST` (stored in `.env` or a small `authorized_users` table if dynamic management is required).

## Indexes
- `idx_alert_log_suppression`: `(instrument_name, timestamp DESC)` to optimize per-instrument per-hour suppression checks.
- `idx_bot_command_user`: `(user_id, timestamp DESC)` for auditing user activity.

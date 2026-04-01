"""Migration script for Phase 4 (Interface & Alerts) tables.

Creates alert_log and bot_command_log tables for Telegram bot integration.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, inspect

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def run_migration() -> None:
    """Execute the migration to create Phase 4 tables."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)

    from db.schema import Base

    print("Connecting to database...")
    engine = create_engine(database_url)

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    print(f"Existing tables: {', '.join(existing_tables)}")

    target_tables = ["alert_log", "bot_command_log"]

    print("Provisioning Phase 4 tables (alert_log, bot_command_log)...")
    Base.metadata.create_all(engine)

    new_inspector = inspect(engine)
    updated_tables = new_inspector.get_table_names()

    for table in target_tables:
        if table in updated_tables:
            print(f"Success: Table '{table}' is present.")
        else:
            print(f"Warning: Table '{table}' was not found after migration.")

    print("Migration completed successfully.")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    run_migration()

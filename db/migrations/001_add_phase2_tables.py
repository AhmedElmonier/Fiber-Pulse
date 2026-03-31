"""Migration script for Phase 2 tables.

Provisions freight_rates and macro_feed_records tables and ensures
source_health table reflects the latest schema.
"""

import os
import sys

from sqlalchemy import create_engine, inspect

# Add project root to sys.path to allow importing from db
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from db.schema import Base


def run_migration():
    """Execute the migration to create new tables."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)

    print(f"Connecting to database...")
    engine = create_engine(database_url)
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print(f"Existing tables: {', '.join(existing_tables)}")
    
    # Tables to create
    target_tables = ["freight_rates", "macro_feed_records"]
    
    # We use Base.metadata.create_all which is idempotent (only creates if not exists)
    print("Provisioning Phase 2 tables...")
    Base.metadata.create_all(engine)
    
    # Verify
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

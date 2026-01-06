#!/usr/bin/env python3
"""Database migration script to add dependency context fields to chat_sessions table.

This script adds:
- selected_dependency_ids: JSON field for storing focused dependency IDs
- context_injected: Boolean flag to track if full context was injected
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text  # noqa: E402

from database.db import get_db_manager  # noqa: E402


def migrate():
    """Add dependency context fields to chat_sessions table."""
    print("Dependency Context Migration")
    print("=" * 50)

    # Get database manager and engine
    db_manager = get_db_manager()
    engine = db_manager.engine

    # Check if columns already exist
    with engine.connect() as conn:
        # Check table schema
        result = conn.execute(text("PRAGMA table_info(chat_sessions)"))
        columns = [row[1] for row in result]

        columns_to_add = []

        if "selected_dependency_ids" not in columns:
            columns_to_add.append("selected_dependency_ids")

        if "context_injected" not in columns:
            columns_to_add.append("context_injected")

        if not columns_to_add:
            print("\n✓ All columns already exist. No migration needed.")
            return

        print(f"\nAdding columns: {', '.join(columns_to_add)}")

        # Add columns (SQLite doesn't support adding multiple columns in one statement)
        if "selected_dependency_ids" in columns_to_add:
            conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN selected_dependency_ids TEXT"))
            conn.commit()
            print("✓ Added selected_dependency_ids column")

        if "context_injected" in columns_to_add:
            conn.execute(
                text(
                    "ALTER TABLE chat_sessions ADD COLUMN context_injected INTEGER NOT NULL DEFAULT 0"
                )
            )
            conn.commit()
            print("✓ Added context_injected column")

    print("\nMigration complete!")
    print("\nNew fields in chat_sessions:")
    print("  - selected_dependency_ids: JSON list of dependency IDs for focused chat")
    print("  - context_injected: Boolean flag (0/1) tracking if full context was injected")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

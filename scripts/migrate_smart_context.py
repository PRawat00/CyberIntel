#!/usr/bin/env python3
"""Database migration script for smart context injection (Phase 6).

This script adds fields for intelligent context management:

ChatSession table:
- dependency_context_hash: SHA256 hash for change detection
- last_context_used_at: Timestamp when context was last injected
- context_usage_count: Counter for analytics

ChatMessage table:
- context_injected: Boolean flag if dependency context was injected
- context_dependency_count: Number of dependencies in context
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text  # noqa: E402

from database.db import get_db_manager  # noqa: E402


def migrate():
    """Add smart context tracking fields to chat_sessions and chat_messages tables."""
    print("Smart Context Injection Migration (Phase 6)")
    print("=" * 60)

    # Get database manager and engine
    db_manager = get_db_manager()
    engine = db_manager.engine

    with engine.connect() as conn:
        # Migrate chat_sessions table
        print("\n[1/2] Migrating chat_sessions table...")
        result = conn.execute(text("PRAGMA table_info(chat_sessions)"))
        session_columns = [row[1] for row in result]

        session_columns_to_add = []

        if "dependency_context_hash" not in session_columns:
            session_columns_to_add.append("dependency_context_hash")

        if "last_context_used_at" not in session_columns:
            session_columns_to_add.append("last_context_used_at")

        if "context_usage_count" not in session_columns:
            session_columns_to_add.append("context_usage_count")

        if session_columns_to_add:
            print(f"  Adding columns: {', '.join(session_columns_to_add)}")

            if "dependency_context_hash" in session_columns_to_add:
                conn.execute(
                    text("ALTER TABLE chat_sessions ADD COLUMN dependency_context_hash VARCHAR(64)")
                )
                conn.commit()
                print("  ✓ Added dependency_context_hash column")

            if "last_context_used_at" in session_columns_to_add:
                conn.execute(
                    text("ALTER TABLE chat_sessions ADD COLUMN last_context_used_at DATETIME")
                )
                conn.commit()
                print("  ✓ Added last_context_used_at column")

            if "context_usage_count" in session_columns_to_add:
                conn.execute(
                    text(
                        "ALTER TABLE chat_sessions ADD COLUMN context_usage_count INTEGER NOT NULL DEFAULT 0"
                    )
                )
                conn.commit()
                print("  ✓ Added context_usage_count column")
        else:
            print("  ✓ All chat_sessions columns already exist")

        # Migrate chat_messages table
        print("\n[2/2] Migrating chat_messages table...")
        result = conn.execute(text("PRAGMA table_info(chat_messages)"))
        message_columns = [row[1] for row in result]

        message_columns_to_add = []

        if "context_injected" not in message_columns:
            message_columns_to_add.append("context_injected")

        if "context_dependency_count" not in message_columns:
            message_columns_to_add.append("context_dependency_count")

        if message_columns_to_add:
            print(f"  Adding columns: {', '.join(message_columns_to_add)}")

            if "context_injected" in message_columns_to_add:
                conn.execute(
                    text(
                        "ALTER TABLE chat_messages ADD COLUMN context_injected INTEGER NOT NULL DEFAULT 0"
                    )
                )
                conn.commit()
                print("  ✓ Added context_injected column")

            if "context_dependency_count" in message_columns_to_add:
                conn.execute(
                    text("ALTER TABLE chat_messages ADD COLUMN context_dependency_count INTEGER")
                )
                conn.commit()
                print("  ✓ Added context_dependency_count column")
        else:
            print("  ✓ All chat_messages columns already exist")

    print("\n" + "=" * 60)
    print("Migration complete!")
    print("\nNew fields in chat_sessions:")
    print("  - dependency_context_hash: SHA256 hash of selected dependency IDs")
    print("  - last_context_used_at: Timestamp when context was last injected")
    print("  - context_usage_count: Counter for analytics")
    print("\nNew fields in chat_messages:")
    print("  - context_injected: Boolean flag (0/1) if dependency context was injected")
    print("  - context_dependency_count: Number of dependencies in context")
    print("\nSmart context injection is now active!")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

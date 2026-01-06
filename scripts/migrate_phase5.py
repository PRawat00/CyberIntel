#!/usr/bin/env python3
"""Database migration script for Phase 5 chat tables.

This script adds the chat_sessions and chat_messages tables to the database.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db import get_db_manager  # noqa: E402
from database.models import ChatMessage, ChatSession  # noqa: E402


def migrate():
    """Create Phase 5 chat tables."""
    print("Phase 5 Database Migration")
    print("=" * 50)

    print("\nCreating chat tables...")

    # Get database manager and engine
    db_manager = get_db_manager()
    engine = db_manager.engine

    # Create only the new tables
    ChatSession.__table__.create(engine, checkfirst=True)
    ChatMessage.__table__.create(engine, checkfirst=True)

    print("✓ chat_sessions table created")
    print("✓ chat_messages table created")

    print("\nMigration complete!")
    print("\nNew tables:")
    print("  - chat_sessions: Store chat sessions")
    print("  - chat_messages: Store individual messages")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

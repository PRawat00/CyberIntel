"""
Migration script to add user_id columns to existing SQLite database.
Prepares local database for authentication integration.
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path to import database config
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock user ID for existing test data
MOCK_USER_ID = "00000000-0000-0000-0000-000000000001"


def get_db_path():
    """Get the database path from config or use default."""
    try:
        import yaml

        config_path = Path(__file__).parent.parent / "configs" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
            db_path_str = config.get("database", {}).get("sqlite", {}).get("path", "cyberintel.db")
            return Path(__file__).parent.parent / db_path_str
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
        # Default path
        return Path(__file__).parent.parent / "cyberintel.db"


def migrate():
    """Add user_id columns to scans and chat_sessions tables."""

    db_path = get_db_path()

    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        print("   Make sure you've run a scan first to create the database.")
        return False

    print(f"📁 Migrating database at: {db_path}")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(scans)")
        scans_columns = [col[1] for col in cursor.fetchall()]

        cursor.execute("PRAGMA table_info(chat_sessions)")
        sessions_columns = [col[1] for col in cursor.fetchall()]

        changes_made = False

        # Add user_id to scans table
        if "user_id" not in scans_columns:
            print("\n📊 Adding user_id to scans table...")
            cursor.execute("ALTER TABLE scans ADD COLUMN user_id TEXT")
            cursor.execute(
                f"UPDATE scans SET user_id = '{MOCK_USER_ID}' WHERE user_id IS NULL"  # noqa: S608
            )
            conn.commit()
            print("   ✓ Added user_id column (set to mock ID for existing scans)")
            changes_made = True
        else:
            print("\n✓ scans.user_id already exists")

        # Add user_id to chat_sessions table
        if "user_id" not in sessions_columns:
            print("\n💬 Adding user_id to chat_sessions table...")
            cursor.execute("ALTER TABLE chat_sessions ADD COLUMN user_id TEXT")
            cursor.execute(
                f"UPDATE chat_sessions SET user_id = '{MOCK_USER_ID}' WHERE user_id IS NULL"  # noqa: S608
            )
            conn.commit()
            print("   ✓ Added user_id column (set to mock ID for existing sessions)")
            changes_made = True
        else:
            print("\n✓ chat_sessions.user_id already exists")

        # Verify the changes
        print("\n🔍 Verifying migration...")
        cursor.execute("SELECT COUNT(*) FROM scans WHERE user_id IS NOT NULL")
        scans_count = cursor.fetchone()[0]
        print(f"   ✓ {scans_count} scans have user_id")

        cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE user_id IS NOT NULL")
        sessions_count = cursor.fetchone()[0]
        print(f"   ✓ {sessions_count} chat sessions have user_id")

        conn.close()

        if changes_made:
            print("\n✅ Migration completed successfully!")
            print(f"\n📝 Note: Existing data assigned to mock user: {MOCK_USER_ID}")
            print("   This allows testing auth with existing scans.")
        else:
            print("\n✅ Database already up-to-date (no changes needed)")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SQLite User ID Migration Script")
    print("=" * 60)

    success = migrate()

    if success:
        print("\n" + "=" * 60)
        print("Next steps:")
        print("1. Backend auth integration (Supabase middleware)")
        print("2. Frontend auth pages (login/signup)")
        print("3. Test locally with new auth")
        print("=" * 60)
        sys.exit(0)
    else:
        sys.exit(1)

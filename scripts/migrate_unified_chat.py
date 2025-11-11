"""
Database migration for unified chat architecture.

Adds new columns to support dynamic context management and feature toggles.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging  # noqa: E402

from sqlalchemy import text  # noqa: E402

from database.db import get_db_session  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """
    Run migration to add unified chat columns.

    Adds:
    - context_stack: JSON column for context history
    - enabled_features: JSON column for session-specific feature flags

    Note: Keeps old columns for backward compatibility.
    """
    logger.info("Starting unified chat migration...")

    with get_db_session() as session:
        try:
            # Check if columns already exist
            result = session.execute(text("PRAGMA table_info(chat_sessions)")).fetchall()

            existing_columns = {row[1] for row in result}
            logger.info(f"Existing columns: {existing_columns}")

            # Add context_stack column
            if "context_stack" not in existing_columns:
                logger.info("Adding context_stack column...")
                session.execute(text("ALTER TABLE chat_sessions ADD COLUMN context_stack TEXT"))
                session.commit()
                logger.info("✓ Added context_stack column")
            else:
                logger.info("context_stack column already exists")

            # Add enabled_features column
            if "enabled_features" not in existing_columns:
                logger.info("Adding enabled_features column...")
                session.execute(text("ALTER TABLE chat_sessions ADD COLUMN enabled_features TEXT"))
                session.commit()
                logger.info("✓ Added enabled_features column")
            else:
                logger.info("enabled_features column already exists")

            logger.info("Migration completed successfully!")

            # Show final schema
            logger.info("\nFinal schema:")
            result = session.execute(text("PRAGMA table_info(chat_sessions)")).fetchall()

            for row in result:
                logger.info(f"  {row[1]}: {row[2]} (nullable={row[3] == 0})")

        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            session.rollback()
            raise


if __name__ == "__main__":
    migrate()

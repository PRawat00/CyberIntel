#!/usr/bin/env python3
"""
Database migration script for adding GitHub integration support.

This migration adds:
1. GitHub integration table for storing encrypted tokens
2. Additional columns to scans table for GitHub metadata
"""

import sys
from pathlib import Path

# Add parent directory to path to import database modules
sys.path.append(str(Path(__file__).parent.parent))

import logging

from sqlalchemy import (
    inspect,
    text,
)

from database.db import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_github_integration():
    """Add GitHub integration support to the database."""

    # Create database manager
    db_manager = DatabaseManager()
    logger.info("Connecting to database...")

    # Get engine from database manager
    engine = db_manager.engine

    # Get inspector to check existing tables/columns
    inspector = inspect(engine)

    try:
        # Check if github_integrations table exists
        if "github_integrations" not in inspector.get_table_names():
            logger.info("Creating github_integrations table...")

            # Create the table using raw SQL for better control
            with engine.begin() as conn:
                conn.execute(
                    text(
                        """
                    CREATE TABLE github_integrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id VARCHAR(36),
                        github_token TEXT,
                        github_username VARCHAR(100),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                    )
                )

                # Create index on user_id
                conn.execute(
                    text(
                        """
                    CREATE INDEX idx_github_integrations_user_id
                    ON github_integrations(user_id)
                """
                    )
                )

            logger.info("✓ Created github_integrations table")
        else:
            logger.info("github_integrations table already exists")

        # Check and add columns to scans table
        existing_columns = [col["name"] for col in inspector.get_columns("scans")]

        columns_to_add = {
            "source": "VARCHAR(20) DEFAULT 'upload'",
            "github_repo": "VARCHAR(255)",
            "github_path": "VARCHAR(500)",
            "github_branch": "VARCHAR(100)",
            "github_commit_sha": "VARCHAR(40)",
        }

        with engine.begin() as conn:
            for column_name, column_type in columns_to_add.items():
                if column_name not in existing_columns:
                    logger.info(f"Adding column '{column_name}' to scans table...")
                    conn.execute(text(f"ALTER TABLE scans ADD COLUMN {column_name} {column_type}"))
                    logger.info(f"✓ Added column '{column_name}'")
                else:
                    logger.info(f"Column '{column_name}' already exists in scans table")

        # Create index on source column for faster filtering
        with engine.begin() as conn:
            # Check if index exists
            indexes = inspector.get_indexes("scans")
            index_names = [idx["name"] for idx in indexes if idx["name"]]

            if "idx_scans_source" not in index_names:
                logger.info("Creating index on scans.source...")
                conn.execute(text("CREATE INDEX idx_scans_source ON scans(source)"))
                logger.info("✓ Created index on scans.source")
            else:
                logger.info("Index on scans.source already exists")

        logger.info("\n✅ GitHub integration migration completed successfully!")

        # Show summary
        logger.info("\n📊 Migration Summary:")
        logger.info("- github_integrations table: ready")
        logger.info("- scans table: extended with GitHub metadata columns")
        logger.info("- Indexes: created for performance")
        logger.info("\n🔐 Note: GitHub tokens will be encrypted at the application level")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    logger.info("Starting GitHub integration migration...")
    logger.info("=" * 50)

    try:
        migrate_github_integration()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

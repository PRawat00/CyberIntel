"""Database connection and session management."""

import hashlib
import json
import os
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import yaml
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, selectinload, sessionmaker
from sqlalchemy.pool import StaticPool

from database.models import Base


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, config_path: str = "configs/config.yaml"):
        """Initialize database manager.

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine based on configuration."""
        db_config = self.config.get("database", {})
        db_type = db_config.get("type", "sqlite")

        # Check for DATABASE_URL environment variable first
        database_url = os.getenv("DATABASE_URL")

        if database_url:
            # Use environment variable if set
            engine = create_engine(database_url)
        elif db_type == "sqlite":
            # SQLite configuration
            db_path = db_config.get("sqlite", {}).get("path", "cyberintel.db")
            database_url = f"sqlite:///{db_path}"
            # Use StaticPool for SQLite to avoid threading issues
            engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        elif db_type == "postgresql":
            # PostgreSQL configuration
            pg_config = db_config.get("postgresql", {})
            host = pg_config.get("host", "localhost")
            port = pg_config.get("port", 5432)
            database = pg_config.get("database", "cyberintel")
            user = pg_config.get("user", "postgres")
            password = pg_config.get("password", "")

            database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            engine = create_engine(database_url)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        return engine

    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """Drop all tables in the database (use with caution)."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session.

        Returns:
            SQLAlchemy Session object
        """
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope for database operations.

        Yields:
            SQLAlchemy Session object

        Example:
            with db_manager.session_scope() as session:
                cve = session.query(CVE).filter_by(cve_id="CVE-2025-1234").first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_db_manager(config_path: str = "configs/config.yaml") -> DatabaseManager:
    """Get or create the global database manager instance.

    Args:
        config_path: Path to configuration file

    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(config_path)
    return _db_manager


@contextmanager
def get_db_session(config_path: str = "configs/config.yaml") -> Generator[Session, None, None]:
    """Get a database session (convenience function).

    Args:
        config_path: Path to configuration file

    Yields:
        SQLAlchemy Session object

    Example:
        with get_db_session() as session:
            cves = session.query(CVE).filter(CVE.severity == "Critical").all()
    """
    db_manager = get_db_manager(config_path)
    with db_manager.session_scope() as session:
        yield session


# Chat Session Context Management Helpers


def _compute_dependency_hash(dependency_ids: list[int] | None) -> str | None:
    """
    Compute SHA256 hash of dependency IDs for change detection.

    Args:
        dependency_ids: List of dependency IDs (can be None or empty)

    Returns:
        Hash string or None if no dependencies
    """
    if not dependency_ids:
        return None

    # Sort IDs for consistent hashing
    sorted_ids = sorted(dependency_ids)
    # Convert to JSON string for stable representation
    ids_json = json.dumps(sorted_ids)
    # Compute SHA256 hash
    hash_obj = hashlib.sha256(ids_json.encode("utf-8"))
    return hash_obj.hexdigest()


def update_session_context(session_id: int, dependency_ids: list[int] | None = None) -> bool:
    """Update the selected dependency context for a chat session.

    Uses hash-based change detection to only reset context when dependencies actually change.

    Args:
        session_id: ID of the chat session
        dependency_ids: List of dependency IDs to focus on (None to clear context)

    Returns:
        True if update successful, False if session not found
    """
    from database.models import ChatSession

    with get_db_session() as session:
        chat_session = session.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session:
            return False

        # Compute new hash
        new_hash = _compute_dependency_hash(dependency_ids)

        # Check if context actually changed
        context_changed = new_hash != chat_session.dependency_context_hash

        # Update dependency IDs and hash
        chat_session.selected_dependency_ids = dependency_ids
        chat_session.dependency_context_hash = new_hash

        # Only reset context_injected if context actually changed
        if context_changed:
            chat_session.context_injected = 0

        session.commit()
        return True


def mark_context_injected(session_id: int) -> bool:
    """Mark that full dependency context has been injected for this session.

    Also updates usage tracking fields for analytics.

    Args:
        session_id: ID of the chat session

    Returns:
        True if update successful, False if session not found
    """
    from database.models import ChatSession

    with get_db_session() as session:
        chat_session = session.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session:
            return False

        chat_session.context_injected = 1
        chat_session.last_context_used_at = datetime.utcnow()
        chat_session.context_usage_count = (chat_session.context_usage_count or 0) + 1
        session.commit()
        return True


def get_session_dependencies(session_id: int) -> list | None:
    """Get the selected dependencies for a chat session.

    Args:
        session_id: ID of the chat session

    Returns:
        List of Dependency objects if session has selection, None otherwise
    """
    from database.models import ChatSession, Dependency

    with get_db_session() as session:
        chat_session = session.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session or not chat_session.selected_dependency_ids:
            return None

        # Fetch the actual dependency objects with eager-loaded CVE relationships
        # This prevents "not bound to a Session" errors when accessing dep.cves later
        dependencies = (
            session.query(Dependency)
            .options(selectinload(Dependency.cves))
            .filter(Dependency.id.in_(chat_session.selected_dependency_ids))
            .all()
        )

        # Expunge objects from session to make them fully detached
        # This ensures all attributes are loaded and accessible without the session
        for dep in dependencies:
            # Also expunge related CVE objects to prevent lazy loading issues
            for cve in dep.cves:
                session.expunge(cve)
            session.expunge(dep)

        return dependencies if dependencies else None


def clear_session_context(session_id: int) -> bool:
    """Clear the dependency context for a chat session.

    Args:
        session_id: ID of the chat session

    Returns:
        True if clear successful, False if session not found
    """
    return update_session_context(session_id, None)


def record_message_context_usage(
    message_id: int, context_injected: bool, dependency_count: int = 0
) -> bool:
    """Record whether dependency context was injected for a specific message.

    Args:
        message_id: ID of the chat message
        context_injected: Whether dependency context was injected
        dependency_count: Number of dependencies in context

    Returns:
        True if update successful, False if message not found
    """
    from database.models import ChatMessage

    with get_db_session() as session:
        message = session.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            return False

        message.context_injected = 1 if context_injected else 0
        message.context_dependency_count = dependency_count if context_injected else None
        session.commit()
        return True

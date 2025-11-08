"""Database connection and session management."""

import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import yaml
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
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

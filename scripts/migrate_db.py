"""Database migration script to add Phase 2 tables.

Adds the following tables:
- scans: Store dependency scan metadata
- dependencies: Store parsed dependency information
- scan_cves: Junction table linking scans to CVEs

Usage:
    python -m scripts.migrate_db
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console

from database.models import CVE, Base, Dependency, Scan

console = Console()


def migrate_database(db_path: str = "cyberintel.db"):
    """Run database migration to add Phase 2 tables.

    Args:
        db_path: Path to SQLite database file
    """
    console.print("[cyan]Starting database migration...[/cyan]")

    try:
        # Create engine directly without using DatabaseManager config
        from sqlalchemy import create_engine

        engine = create_engine(f"sqlite:///{db_path}")

        # Create all tables (will skip existing ones)
        # This uses SQLAlchemy's create_all which is idempotent
        Base.metadata.create_all(engine)

        console.print("[green]Migration completed successfully![/green]")
        console.print()
        console.print("Added tables:")
        console.print("  - scans (dependency scan metadata)")
        console.print("  - dependencies (parsed dependency information)")
        console.print("  - scan_cves (scan-CVE relationships)")
        console.print()

        # Verify tables exist
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            # Check if we can query the new tables
            scan_count = session.query(Scan).count()
            dep_count = session.query(Dependency).count()
            cve_count = session.query(CVE).count()

            console.print("[cyan]Database status:[/cyan]")
            console.print(f"  - CVEs: {cve_count}")
            console.print(f"  - Scans: {scan_count}")
            console.print(f"  - Dependencies: {dep_count}")
            console.print()
            console.print("[green]Database is ready for Phase 2 scanning![/green]")

        finally:
            session.close()

    except Exception as e:
        console.print(f"[red]Migration failed:[/red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate database for Phase 2")
    parser.add_argument(
        "--db",
        default="cyberintel.db",
        help="Path to database file (default: cyberintel.db)",
    )

    args = parser.parse_args()

    migrate_database(args.db)


if __name__ == "__main__":
    main()

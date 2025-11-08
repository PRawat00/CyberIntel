"""Initialize database tables."""

import logging
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel

from database.db import get_db_manager

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database."""
    console.print(
        Panel.fit(
            "[bold cyan]CyberIntel Summarizer - Database Initialization[/bold cyan]",
            border_style="cyan",
        )
    )

    try:
        # Get database manager
        console.print("\n[yellow]Loading configuration...[/yellow]")
        db_manager = get_db_manager()

        # Create tables
        console.print("[yellow]Creating database tables...[/yellow]")
        db_manager.create_tables()

        console.print("\n[bold green]✓ Database initialized successfully![/bold green]")
        console.print(f"[dim]Database location: {db_manager.engine.url}[/dim]\n")

    except Exception as e:
        console.print(f"\n[bold red]✗ Error initializing database: {e}[/bold red]\n")
        logger.exception("Database initialization failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

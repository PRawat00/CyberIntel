"""Script to clear CVE data from the database."""

import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import get_db_manager
from database.models import CVE, ChatMessage, ChatSession, Dependency, Scan, scan_cves

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/clear_database.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def get_database_stats(db_manager):
    """Get current database statistics.

    Args:
        db_manager: DatabaseManager instance

    Returns:
        Dict with counts of each table
    """
    stats = {}

    with db_manager.session_scope() as session:
        stats["cves"] = session.query(CVE).count()
        stats["scans"] = session.query(Scan).count()
        stats["dependencies"] = session.query(Dependency).count()
        stats["chat_sessions"] = session.query(ChatSession).count()
        stats["chat_messages"] = session.query(ChatMessage).count()

        # Get scan_cves count
        from sqlalchemy import func, select

        stats["scan_cves"] = session.execute(select(func.count()).select_from(scan_cves)).scalar()

    return stats


def backup_database(db_path: Path):
    """Create a backup of the database.

    Args:
        db_path: Path to database file

    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}_backup_{timestamp}{db_path.suffix}"

    console.print("\n[yellow]Creating backup...[/yellow]")
    console.print(f"Source: {db_path}")
    console.print(f"Backup: {backup_path}")

    shutil.copy2(db_path, backup_path)
    backup_size_mb = backup_path.stat().st_size / (1024 * 1024)

    console.print(f"[green]✓ Backup created ({backup_size_mb:.1f} MB)[/green]\n")

    return backup_path


def clear_cves_only(db_manager):
    """Clear only CVE data, keep scans and dependencies.

    Args:
        db_manager: DatabaseManager instance

    Returns:
        Number of CVEs deleted
    """
    with db_manager.session_scope() as session:
        # First clear the association table
        session.execute(scan_cves.delete())

        # Then delete CVEs
        count = session.query(CVE).delete()

    return count


def clear_all_data(db_manager):
    """Clear all data from database (CVEs, scans, dependencies, chats).

    Args:
        db_manager: DatabaseManager instance

    Returns:
        Dict with counts of deleted records
    """
    counts = {}

    with db_manager.session_scope() as session:
        # Delete in order to respect foreign key constraints
        counts["chat_messages"] = session.query(ChatMessage).delete()
        counts["chat_sessions"] = session.query(ChatSession).delete()
        counts["dependencies"] = session.query(Dependency).delete()
        counts["scans"] = session.query(Scan).delete()

        # Clear association table
        session.execute(scan_cves.delete())

        # Delete CVEs
        counts["cves"] = session.query(CVE).delete()

    return counts


@click.command()
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Clear all data (CVEs, scans, dependencies, chat sessions). Default: only CVEs",
)
@click.option(
    "--backup",
    "-b",
    is_flag=True,
    help="Create a backup before clearing",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt (USE WITH CAUTION)",
)
def main(all: bool, backup: bool, yes: bool):
    """Clear CVE data from the database to start fresh."""
    console.print(
        Panel.fit(
            "[bold red]Database Clear Utility[/bold red]\n"
            "[yellow]⚠️  WARNING: This will permanently delete data[/yellow]",
            border_style="red",
        )
    )

    try:
        # Initialize database manager
        console.print("\n[yellow]Connecting to database...[/yellow]")
        db_manager = get_db_manager()

        # Get current stats
        console.print("[yellow]Analyzing database...[/yellow]\n")
        stats_before = get_database_stats(db_manager)

        # Display current stats
        stats_table = Table(
            title="Current Database Contents", show_header=True, header_style="bold cyan"
        )
        stats_table.add_column("Table", style="cyan")
        stats_table.add_column("Records", justify="right", style="yellow")

        stats_table.add_row("CVEs", str(stats_before["cves"]))
        stats_table.add_row("Scans", str(stats_before["scans"]))
        stats_table.add_row("Dependencies", str(stats_before["dependencies"]))
        stats_table.add_row("Scan-CVE Links", str(stats_before["scan_cves"]))
        stats_table.add_row("Chat Sessions", str(stats_before["chat_sessions"]))
        stats_table.add_row("Chat Messages", str(stats_before["chat_messages"]))

        console.print(stats_table)
        console.print()

        # Check if database is empty
        if stats_before["cves"] == 0 and stats_before["scans"] == 0:
            console.print("[green]Database is already empty. Nothing to clear.[/green]\n")
            return

        # Show what will be deleted
        if all:
            console.print("[bold red]Will delete:[/bold red]")
            console.print(f"  • {stats_before['cves']:,} CVEs")
            console.print(f"  • {stats_before['scans']:,} Scans")
            console.print(f"  • {stats_before['dependencies']:,} Dependencies")
            console.print(f"  • {stats_before['chat_sessions']:,} Chat Sessions")
            console.print(f"  • {stats_before['chat_messages']:,} Chat Messages")
        else:
            console.print("[bold yellow]Will delete:[/bold yellow]")
            console.print(f"  • {stats_before['cves']:,} CVEs")
            console.print(f"  • {stats_before['scan_cves']:,} Scan-CVE Links")
            console.print(
                "\n[dim]Note: Scans and dependencies will be kept (use --all to clear everything)[/dim]"
            )

        console.print()

        # Confirmation
        if not yes:
            response = input("Are you sure you want to proceed? Type 'yes' to confirm: ").lower()
            if response != "yes":
                console.print("\n[yellow]Operation cancelled.[/yellow]\n")
                return

            # Double confirmation for --all
            if all:
                response2 = input("This will delete ALL data. Type 'DELETE ALL' to confirm: ")
                if response2 != "DELETE ALL":
                    console.print("\n[yellow]Operation cancelled.[/yellow]\n")
                    return

        # Backup if requested
        if backup:
            # Load config to get database path
            config_path = Path(__file__).parent.parent / "configs" / "config.yaml"
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            db_path = Path(
                config.get("database", {}).get("sqlite", {}).get("path", "cyberintel.db")
            )
            backup_path = backup_database(db_path)
            console.print(f"[green]Backup saved to: {backup_path}[/green]\n")

        # Clear database
        console.print("[bold red]Clearing database...[/bold red]\n")

        if all:
            counts = clear_all_data(db_manager)
            console.print("[green]✓ All data cleared successfully![/green]\n")

            # Show what was deleted
            result_table = Table(
                title="Deleted Records", show_header=True, header_style="bold green"
            )
            result_table.add_column("Table", style="cyan")
            result_table.add_column("Deleted", justify="right", style="green")

            result_table.add_row("CVEs", str(counts["cves"]))
            result_table.add_row("Scans", str(counts["scans"]))
            result_table.add_row("Dependencies", str(counts["dependencies"]))
            result_table.add_row("Chat Sessions", str(counts["chat_sessions"]))
            result_table.add_row("Chat Messages", str(counts["chat_messages"]))

            console.print(result_table)
        else:
            count = clear_cves_only(db_manager)
            console.print(f"[green]✓ Cleared {count:,} CVEs successfully![/green]\n")

        # Verify database is cleared
        stats_after = get_database_stats(db_manager)

        if all:
            if stats_after["cves"] == 0 and stats_after["scans"] == 0:
                console.print(
                    "[bold green]✓ Database is now empty and ready for fresh data.[/bold green]\n"
                )
            else:
                console.print("[yellow]⚠️  Warning: Some data may remain in database.[/yellow]\n")
        else:
            if stats_after["cves"] == 0:
                console.print(
                    "[bold green]✓ CVE data cleared. Scans and dependencies preserved.[/bold green]\n"
                )
            else:
                console.print("[yellow]⚠️  Warning: Some CVEs may remain in database.[/yellow]\n")

        # Next steps
        console.print("[bold cyan]Next steps:[/bold cyan]")
        console.print("1. Run a fresh CVE fetch:")
        console.print("   [dim]python -m scripts.fetch_nvd --sync-smart --days 4380[/dim]")
        console.print("\n2. The new batch commit system will save progress incrementally")
        console.print("   [dim]You can safely interrupt (Ctrl+C) without losing data[/dim]\n")

    except FileNotFoundError as e:
        console.print(f"\n[bold red]✗ Configuration file not found: {e}[/bold red]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]✗ Error: {e}[/bold red]\n")
        logger.exception("Clear operation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

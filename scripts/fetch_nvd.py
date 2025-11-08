"""CLI tool to fetch CVEs from NVD and store in database."""

import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from sqlalchemy.exc import IntegrityError

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_ingestion.nvd_fetcher import NVDFetcher
from database.db import get_db_manager
from database.models import CVE

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/fetch_nvd.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def store_cves_in_db(cves, db_manager):
    """Store CVEs in database.

    Args:
        cves: List of CVEData objects
        db_manager: DatabaseManager instance

    Returns:
        Tuple of (new_count, updated_count, skipped_count)
    """
    new_count = 0
    updated_count = 0
    skipped_count = 0

    with db_manager.session_scope() as session:
        for cve_data in cves:
            try:
                # Check if CVE already exists
                existing_cve = session.query(CVE).filter_by(cve_id=cve_data.cve_id).first()

                if existing_cve:
                    # Update if last_modified date is newer
                    if cve_data.last_modified > existing_cve.last_modified:
                        # Update fields
                        existing_cve.description = cve_data.description
                        existing_cve.last_modified = cve_data.last_modified
                        existing_cve.severity = cve_data.severity
                        existing_cve.cvss_score = cve_data.cvss_score
                        existing_cve.cvss_vector = cve_data.cvss_vector
                        existing_cve.attack_vector = cve_data.attack_vector
                        existing_cve.attack_complexity = cve_data.attack_complexity
                        existing_cve.privileges_required = cve_data.privileges_required
                        existing_cve.user_interaction = cve_data.user_interaction
                        existing_cve.vendor = cve_data.vendor
                        existing_cve.product = cve_data.product
                        existing_cve.references = cve_data.references
                        existing_cve.cwe_ids = cve_data.cwe_ids
                        existing_cve.raw_data = cve_data.raw_data

                        updated_count += 1
                        logger.debug(f"Updated CVE: {cve_data.cve_id}")
                    else:
                        skipped_count += 1
                        logger.debug(f"Skipped (no changes): {cve_data.cve_id}")
                else:
                    # Insert new CVE
                    new_cve = CVE(
                        cve_id=cve_data.cve_id,
                        description=cve_data.description,
                        published_date=cve_data.published_date,
                        last_modified=cve_data.last_modified,
                        severity=cve_data.severity,
                        cvss_score=cve_data.cvss_score,
                        cvss_vector=cve_data.cvss_vector,
                        attack_vector=cve_data.attack_vector,
                        attack_complexity=cve_data.attack_complexity,
                        privileges_required=cve_data.privileges_required,
                        user_interaction=cve_data.user_interaction,
                        vendor=cve_data.vendor,
                        product=cve_data.product,
                        references=cve_data.references,
                        cwe_ids=cve_data.cwe_ids,
                        source="NVD",
                        raw_data=cve_data.raw_data,
                    )
                    session.add(new_cve)
                    new_count += 1
                    logger.debug(f"Inserted new CVE: {cve_data.cve_id}")

            except IntegrityError as e:
                logger.error(f"Database integrity error for {cve_data.cve_id}: {e}")
                session.rollback()
                skipped_count += 1
            except Exception as e:
                logger.error(f"Error storing {cve_data.cve_id}: {e}")
                skipped_count += 1

    return new_count, updated_count, skipped_count


@click.command()
@click.option(
    "--days",
    "-d",
    default=7,
    type=int,
    help="Number of days to look back (default: 7)",
)
@click.option(
    "--limit",
    "-l",
    default=None,
    type=int,
    help="Maximum number of CVEs to fetch (default: unlimited)",
)
@click.option(
    "--cve-id",
    "-c",
    default=None,
    type=str,
    help="Fetch a specific CVE by ID (e.g., CVE-2025-1234)",
)
@click.option(
    "--results-per-page",
    "-r",
    default=100,
    type=int,
    help="Results per API request (default: 100)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(days: int, limit: int | None, cve_id: str | None, results_per_page: int, verbose: bool):
    """Fetch CVEs from NVD and store in database."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    console.print(
        Panel.fit(
            "[bold cyan]CyberIntel Summarizer - NVD CVE Fetcher[/bold cyan]", border_style="cyan"
        )
    )

    try:
        # Initialize database manager
        console.print("\n[yellow]Initializing database...[/yellow]")
        db_manager = get_db_manager()
        db_manager.create_tables()  # Ensure tables exist

        # Initialize NVD fetcher
        console.print("[yellow]Initializing NVD fetcher...[/yellow]")
        fetcher = NVDFetcher()

        # Fetch CVEs
        cves = []

        if cve_id:
            # Fetch specific CVE
            console.print(f"\n[cyan]Fetching CVE: {cve_id}[/cyan]\n")
            cve_data = fetcher.fetch_cve_by_id(cve_id)
            if cve_data:
                cves = [cve_data]
        else:
            # Fetch recent CVEs
            console.print(f"\n[cyan]Fetching CVEs from last {days} days...[/cyan]\n")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Fetching CVEs...", total=None)
                cves = fetcher.fetch_recent_cves(
                    days=days,
                    results_per_page=results_per_page,
                    max_results=limit,
                )
                progress.update(task, completed=True)

        if not cves:
            console.print("\n[yellow]No CVEs found.[/yellow]\n")
            return

        console.print(f"\n[green]✓ Fetched {len(cves)} CVEs from NVD[/green]\n")

        # Store in database
        console.print("[yellow]Storing CVEs in database...[/yellow]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Storing CVEs...", total=None)
            new_count, updated_count, skipped_count = store_cves_in_db(cves, db_manager)
            progress.update(task, completed=True)

        # Display summary
        console.print("\n[bold green]✓ Operation completed![/bold green]\n")

        summary_table = Table(title="Summary", show_header=True, header_style="bold magenta")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", justify="right", style="green")

        summary_table.add_row("Total Fetched", str(len(cves)))
        summary_table.add_row("New CVEs", str(new_count))
        summary_table.add_row("Updated CVEs", str(updated_count))
        summary_table.add_row("Skipped CVEs", str(skipped_count))

        console.print(summary_table)
        console.print()

        # Display sample CVEs
        if cves:
            console.print("[bold]Sample CVEs:[/bold]\n")
            cve_table = Table(show_header=True, header_style="bold blue")
            cve_table.add_column("CVE ID", style="cyan", width=16)
            cve_table.add_column("Severity", style="yellow", width=10)
            cve_table.add_column("CVSS", justify="right", width=6)
            cve_table.add_column("Published", style="dim", width=12)
            cve_table.add_column("Description", style="white", width=60)

            for cve in cves[:10]:  # Show first 10
                severity_color = {
                    "CRITICAL": "bold red",
                    "HIGH": "red",
                    "MEDIUM": "yellow",
                    "LOW": "green",
                }.get(cve.severity or "NONE", "white")

                cve_table.add_row(
                    cve.cve_id,
                    f"[{severity_color}]{cve.severity or 'N/A'}[/{severity_color}]",
                    f"{cve.cvss_score:.1f}" if cve.cvss_score else "N/A",
                    cve.published_date.strftime("%Y-%m-%d"),
                    cve.description[:60] + "..." if len(cve.description) > 60 else cve.description,
                )

            console.print(cve_table)
            console.print()

    except FileNotFoundError as e:
        console.print(f"\n[bold red]✗ Configuration file not found: {e}[/bold red]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]✗ Error: {e}[/bold red]\n")
        logger.exception("Fetch operation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

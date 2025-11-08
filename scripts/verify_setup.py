"""Verify that the CyberIntel Summarizer setup is complete and working."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from database.db import get_db_manager
from database.models import CVE

console = Console()


def main():
    """Verify the setup."""
    console.print(
        Panel.fit(
            "[bold cyan]CyberIntel Summarizer - Setup Verification[/bold cyan]", border_style="cyan"
        )
    )

    all_checks_passed = True

    # Check 1: Configuration file
    console.print("\n[yellow]Checking configuration...[/yellow]")
    config_path = Path("configs/config.yaml")
    if config_path.exists():
        console.print("[green]✓ Configuration file found[/green]")
    else:
        console.print("[red]✗ Configuration file not found[/red]")
        all_checks_passed = False

    # Check 2: Database connection
    console.print("[yellow]Checking database connection...[/yellow]")
    try:
        db_manager = get_db_manager()
        console.print("[green]✓ Database connection successful[/green]")
        console.print(f"[dim]  Location: {db_manager.engine.url}[/dim]")
    except Exception as e:
        console.print(f"[red]✗ Database connection failed: {e}[/red]")
        all_checks_passed = False
        return

    # Check 3: Database tables
    console.print("[yellow]Checking database tables...[/yellow]")
    try:
        with db_manager.session_scope() as session:
            # Try to query CVE table
            count = session.query(CVE).count()
            console.print(f"[green]✓ CVE table exists ({count} records)[/green]")
    except Exception as e:
        console.print(f"[red]✗ Database tables not found: {e}[/red]")
        console.print("[yellow]  Run: python -m scripts.init_db[/yellow]")
        all_checks_passed = False
        return

    # Check 4: CVE data statistics
    console.print("\n[yellow]Analyzing stored CVEs...[/yellow]")
    try:
        with db_manager.session_scope() as session:
            total = session.query(CVE).count()

            if total == 0:
                console.print("[yellow]⚠ No CVEs in database yet[/yellow]")
                console.print("[dim]  Run: python -m scripts.fetch_nvd --days 7[/dim]")
            else:
                # Get severity counts
                critical = session.query(CVE).filter(CVE.severity == "CRITICAL").count()
                high = session.query(CVE).filter(CVE.severity == "HIGH").count()
                medium = session.query(CVE).filter(CVE.severity == "MEDIUM").count()
                low = session.query(CVE).filter(CVE.severity == "LOW").count()
                none_severity = session.query(CVE).filter(CVE.severity.is_(None)).count()

                # Create statistics table
                stats_table = Table(
                    title="CVE Statistics", show_header=True, header_style="bold magenta"
                )
                stats_table.add_column("Severity", style="cyan")
                stats_table.add_column("Count", justify="right", style="green")
                stats_table.add_column("Percentage", justify="right", style="yellow")

                stats = [
                    ("Critical", critical, "bold red"),
                    ("High", high, "red"),
                    ("Medium", medium, "yellow"),
                    ("Low", low, "green"),
                    ("Unknown", none_severity, "dim"),
                ]

                for severity, count, color in stats:
                    percentage = (count / total * 100) if total > 0 else 0
                    stats_table.add_row(
                        f"[{color}]{severity}[/{color}]", str(count), f"{percentage:.1f}%"
                    )

                stats_table.add_row("──────", "───", "──────", end_section=True)
                stats_table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]", "100.0%")

                console.print()
                console.print(stats_table)

                # Get source distribution
                nvd_count = session.query(CVE).filter(CVE.source == "NVD").count()
                console.print(f"\n[dim]Source distribution: NVD: {nvd_count}[/dim]")

    except Exception as e:
        console.print(f"[red]✗ Error analyzing CVE data: {e}[/red]")
        all_checks_passed = False

    # Check 5: NVD Fetcher
    console.print("\n[yellow]Checking NVD fetcher...[/yellow]")
    try:
        from data_ingestion.nvd_fetcher import NVDFetcher

        fetcher = NVDFetcher()
        console.print("[green]✓ NVD fetcher initialized successfully[/green]")
        console.print(f"[dim]  API URL: {fetcher.base_url}[/dim]")
        if fetcher.api_key:
            console.print("[dim]  API Key: Configured (rate limit: 50 req/30s)[/dim]")
        else:
            console.print("[dim]  API Key: Not configured (rate limit: 5 req/30s)[/dim]")
    except Exception as e:
        console.print(f"[red]✗ NVD fetcher initialization failed: {e}[/red]")
        all_checks_passed = False

    # Final summary
    console.print()
    if all_checks_passed:
        console.print(
            Panel.fit(
                "[bold green]✓ All checks passed! Phase 1 is complete.[/bold green]\n\n"
                "Next steps:\n"
                "  • Run: [cyan]python -m scripts.fetch_nvd --days 7[/cyan] to fetch CVEs\n"
                "  • Proceed to Phase 2: LLM Summarization",
                title="Setup Verification Complete",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel.fit(
                "[bold red]✗ Some checks failed. Please fix the issues above.[/bold red]",
                title="Setup Verification Failed",
                border_style="red",
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

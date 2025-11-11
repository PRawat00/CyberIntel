#!/usr/bin/env python3
"""Initialize RAG system by generating embeddings for all CVEs in database.

This script:
1. Reads all CVEs from the database
2. Generates embeddings for each CVE description
3. Stores embeddings in ChromaDB vector store

Run this once after populating CVE database or when adding new CVEs.

Usage:
    python -m scripts.init_embeddings
    python -m scripts.init_embeddings --batch-size 64 --reset
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse  # noqa: E402
import logging  # noqa: E402

from rich.console import Console  # noqa: E402
from rich.progress import (  # noqa: E402
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from database.db import get_db_session  # noqa: E402
from database.models import CVE  # noqa: E402
from llm_engine.embedder import CVEEmbedder  # noqa: E402
from llm_engine.vector_store import CVEVectorStore  # noqa: E402

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

console = Console()


def init_embeddings(batch_size: int = 32, reset: bool = False, limit: int | None = None):
    """Initialize embeddings for all CVEs in database.

    Args:
        batch_size: Batch size for embedding generation (default: 32)
        reset: Whether to reset vector store before adding (default: False)
        limit: Maximum number of CVEs to process (None = all)
    """
    console.print("\n[bold cyan]CVE Embeddings Initialization[/bold cyan]\n")

    # Initialize components
    console.print("[yellow]Loading models...[/yellow]")
    embedder = CVEEmbedder()
    vector_store = CVEVectorStore()

    console.print(f"✓ Embedder loaded: {embedder.model_name}")
    console.print(f"✓ Vector store initialized: {vector_store.count()} CVEs\n")

    # Reset vector store if requested
    if reset:
        console.print("[red]Resetting vector store...[/red]")
        vector_store.reset()
        console.print("✓ Vector store reset complete\n")

    # Fetch CVEs from database
    console.print("[yellow]Fetching CVEs from database...[/yellow]")
    with get_db_session() as session:
        query = session.query(CVE).order_by(CVE.published_date.desc())

        if limit:
            query = query.limit(limit)

        cves = query.all()
        total = len(cves)

        # Extract CVE data while still in session
        cve_data = []
        for cve in cves:
            cve_data.append(
                {
                    "cve_id": cve.cve_id,
                    "description": cve.description or "No description available",
                    "severity": cve.severity or "UNKNOWN",
                    "cvss_score": cve.cvss_score or 0.0,
                    "vendor": cve.vendor or "unknown",
                    "product": cve.product or "unknown",
                    "published_date": cve.published_date,
                }
            )

    if total == 0:
        console.print("[red]No CVEs found in database![/red]")
        console.print("Run: python -m scripts.fetch_nvd --days 365")
        return

    console.print(f"✓ Found {total} CVEs\n")

    # Check which CVEs already have embeddings
    console.print("[yellow]Checking existing embeddings...[/yellow]")
    existing_cve_ids = set()
    for cve in cve_data:
        if vector_store.get_cve(cve["cve_id"]):
            existing_cve_ids.add(cve["cve_id"])

    new_cves = [cve for cve in cve_data if cve["cve_id"] not in existing_cve_ids]

    if existing_cve_ids:
        console.print(f"✓ Found {len(existing_cve_ids)} existing embeddings")
        console.print(f"✓ {len(new_cves)} new CVEs to process\n")
    else:
        console.print("✓ No existing embeddings found\n")
        new_cves = cve_data  # Use dict data, not CVE objects

    if not new_cves:
        console.print("[green]All CVEs already have embeddings![/green]")
        console.print(f"Total in vector store: {vector_store.count()}")
        return

    # Generate embeddings with progress bar
    console.print("[yellow]Generating embeddings...[/yellow]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing CVEs", total=len(new_cves))

        # Process in batches
        for i in range(0, len(new_cves), batch_size):
            batch = new_cves[i : i + batch_size]

            # Prepare batch data
            cve_ids = []
            descriptions = []
            severities = []
            cvss_scores = []
            vendors = []
            products = []
            published_dates = []

            for cve in batch:
                cve_ids.append(cve["cve_id"])
                descriptions.append(cve["description"])
                severities.append(cve["severity"])
                cvss_scores.append(cve["cvss_score"])
                vendors.append(cve["vendor"])
                products.append(cve["product"])
                published_dates.append(cve["published_date"])

            # Generate embeddings for batch
            embeddings = embedder.embed_cves_batch(
                descriptions, batch_size=batch_size, max_length=512
            )

            # Add to vector store
            _ = vector_store.add_cves_batch(
                cve_ids=cve_ids,
                embeddings=embeddings,
                descriptions=descriptions,
                severities=severities,
                cvss_scores=cvss_scores,
                vendors=vendors,
                products=products,
                published_dates=published_dates,
                batch_size=batch_size,
            )

            progress.update(task, advance=len(batch))

    # Final stats
    final_count = vector_store.count()
    console.print("\n[green]✓ Initialization complete![/green]")
    console.print(f"[green]✓ Total CVEs in vector store: {final_count}[/green]\n")

    # Show some example searches
    console.print("[cyan]Example searches you can try:[/cyan]")
    console.print('  - "SQL injection vulnerabilities"')
    console.print('  - "Remote code execution in authentication"')
    console.print('  - "Critical Apache vulnerabilities"')
    console.print('  - "Cross-site scripting in web applications"\n')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Initialize CVE embeddings")
    parser.add_argument(
        "--batch-size", type=int, default=32, help="Batch size for processing (default: 32)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset vector store before adding (deletes existing embeddings)",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit number of CVEs to process (for testing)"
    )

    args = parser.parse_args()

    try:
        init_embeddings(batch_size=args.batch_size, reset=args.reset, limit=args.limit)
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.exception("Failed to initialize embeddings")
        sys.exit(1)


if __name__ == "__main__":
    main()

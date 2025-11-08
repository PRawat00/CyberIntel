"""CLI tool for scanning dependency files for vulnerabilities.

Usage:
    python -m scripts.scan_dependencies --file package.json
    python -m scripts.scan_dependencies --file requirements.txt --verbose
    python -m scripts.scan_dependencies --file package.json --output json
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Dependency, Scan, scan_cves
from matching import CpeMatcher
from parsers import NpmParser, PipParser

console = Console()


class DependencyScanner:
    """Main scanner class for dependency vulnerability scanning."""

    def __init__(self, db_path: str = "cyberintel.db"):
        """Initialize the scanner.

        Args:
            db_path: Path to the SQLite database
        """
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine)
        self.parsers = {
            "npm": NpmParser(),
            "pip": PipParser(),
        }

    def detect_file_type(self, file_path: Path) -> str:
        """Detect the type of dependency file.

        Args:
            file_path: Path to the file

        Returns:
            File type string (npm, pip, etc.)

        Raises:
            ValueError: If file type cannot be detected
        """
        file_name = file_path.name.lower()

        for file_type, parser in self.parsers.items():
            if parser.supports_file(file_name):
                return file_type

        raise ValueError(
            f"Unsupported file type: {file_name}. "
            f"Supported files: package.json, requirements.txt"
        )

    def scan_file(self, file_path: Path, verbose: bool = False) -> dict[str, Any]:
        """Scan a dependency file for vulnerabilities.

        Args:
            file_path: Path to the dependency file
            verbose: Whether to print verbose output

        Returns:
            Dictionary containing scan results

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if verbose:
            console.print(f"[cyan]Scanning file:[/cyan] {file_path}")

        # Detect file type
        file_type = self.detect_file_type(file_path)
        parser = self.parsers[file_type]

        if verbose:
            console.print(f"[cyan]Detected file type:[/cyan] {file_type}")

        # Parse dependencies
        if verbose:
            console.print("[cyan]Parsing dependencies...[/cyan]")

        dependencies = parser.parse_file(file_path)

        if verbose:
            console.print(f"[green]Found {len(dependencies)} dependencies[/green]")

        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)

        # Create database session
        session = self.Session()

        try:
            # Create scan record
            scan = Scan(
                file_name=file_path.name,
                file_type=file_type,
                file_hash=file_hash,
                scan_date=datetime.now(),
                total_dependencies=len(dependencies),
            )
            session.add(scan)
            session.flush()  # Get scan ID

            # Initialize CPE matcher
            cpe_matcher = CpeMatcher(session)

            # Match dependencies to CVEs
            if verbose:
                console.print("[cyan]Matching dependencies to CVEs...[/cyan]")

            vulnerable_count = 0
            total_cves = 0
            severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}

            scan_results = []

            for dep in dependencies:
                if verbose:
                    console.print(f"  Checking {dep.package_name}@{dep.version}...", end="")

                # Find CVEs for this dependency
                cve_matches = cpe_matcher.find_cves_for_package(
                    dep.package_name, dep.version, dep.ecosystem
                )

                is_vulnerable = len(cve_matches) > 0
                if is_vulnerable:
                    vulnerable_count += 1
                    total_cves += len(cve_matches)

                # Determine highest severity
                highest_severity = None
                if cve_matches:
                    severity_order = ["Critical", "High", "Medium", "Low", "Unknown"]
                    for severity in severity_order:
                        if any(cve.severity == severity for cve in cve_matches):
                            highest_severity = severity
                            if severity in severity_counts:
                                severity_counts[severity] += 1
                            break

                # Create dependency record
                dep_record = Dependency(
                    scan_id=scan.id,
                    package_name=dep.package_name,
                    version=dep.version,
                    version_constraint=dep.version_constraint,
                    ecosystem=dep.ecosystem,
                    is_vulnerable=1 if is_vulnerable else 0,
                    cve_count=len(cve_matches),
                    highest_severity=highest_severity,
                    package_metadata=dep.metadata,
                )
                session.add(dep_record)
                session.flush()  # Get dependency ID

                # Link CVEs to scan
                for cve_match in cve_matches:
                    session.execute(
                        scan_cves.insert().values(
                            scan_id=scan.id,
                            cve_id=cve_match.cve_id,
                            dependency_id=dep_record.id,
                        )
                    )

                scan_results.append(
                    {
                        "package": dep.package_name,
                        "version": dep.version,
                        "vulnerable": is_vulnerable,
                        "cve_count": len(cve_matches),
                        "cves": cve_matches,
                        "highest_severity": highest_severity,
                    }
                )

                if verbose:
                    if is_vulnerable:
                        console.print(f" [red]VULNERABLE[/red] ({len(cve_matches)} CVEs)")
                    else:
                        console.print(" [green]OK[/green]")

            # Update scan summary
            scan.vulnerable_dependencies = vulnerable_count
            scan.total_cves = total_cves
            scan.critical_count = severity_counts["Critical"]
            scan.high_count = severity_counts["High"]
            scan.medium_count = severity_counts["Medium"]
            scan.low_count = severity_counts["Low"]

            # Commit to database
            session.commit()

            return {
                "scan_id": scan.id,
                "file_name": file_path.name,
                "file_type": file_type,
                "scan_date": scan.scan_date.isoformat(),
                "total_dependencies": len(dependencies),
                "vulnerable_dependencies": vulnerable_count,
                "total_cves": total_cves,
                "severity_counts": severity_counts,
                "results": scan_results,
            }

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content.

        Args:
            file_path: Path to file

        Returns:
            SHA-256 hash string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


def print_scan_report(results: dict[str, Any], format: str = "text"):
    """Print scan results in specified format.

    Args:
        results: Scan results dictionary
        format: Output format (text, json)
    """
    if format == "json":
        # Convert CveMatch objects to dicts for JSON serialization
        json_results = results.copy()
        for result in json_results["results"]:
            result["cves"] = [
                {
                    "cve_id": cve.cve_id,
                    "severity": cve.severity,
                    "cvss_score": cve.cvss_score,
                    "description": cve.description[:100] + "...",  # Truncate
                }
                for cve in result["cves"]
            ]
        print(json.dumps(json_results, indent=2))
        return

    # Text format with Rich
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]Dependency Scan Report[/bold cyan]\n"
            f"File: {results['file_name']}\n"
            f"Type: {results['file_type']}\n"
            f"Scan ID: {results['scan_id']}",
            box=box.DOUBLE,
        )
    )
    console.print()

    # Summary statistics
    summary_table = Table(title="Scan Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white", justify="right")

    summary_table.add_row("Total Dependencies", str(results["total_dependencies"]))
    summary_table.add_row(
        "Vulnerable Dependencies",
        (
            f"[red]{results['vulnerable_dependencies']}[/red]"
            if results["vulnerable_dependencies"] > 0
            else "[green]0[/green]"
        ),
    )
    summary_table.add_row("Total CVEs", str(results["total_cves"]))

    console.print(summary_table)
    console.print()

    # Severity breakdown
    if results["total_cves"] > 0:
        severity_table = Table(title="Severity Breakdown", box=box.ROUNDED)
        severity_table.add_column("Severity", style="cyan")
        severity_table.add_column("Count", justify="right")

        counts = results["severity_counts"]
        if counts["Critical"] > 0:
            severity_table.add_row("Critical", f"[red bold]{counts['Critical']}[/red bold]")
        if counts["High"] > 0:
            severity_table.add_row("High", f"[red]{counts['High']}[/red]")
        if counts["Medium"] > 0:
            severity_table.add_row("Medium", f"[yellow]{counts['Medium']}[/yellow]")
        if counts["Low"] > 0:
            severity_table.add_row("Low", f"[blue]{counts['Low']}[/blue]")

        console.print(severity_table)
        console.print()

    # Vulnerable dependencies detail
    vulnerable = [r for r in results["results"] if r["vulnerable"]]

    if vulnerable:
        console.print("[bold red]Vulnerable Dependencies:[/bold red]")
        console.print()

        for i, result in enumerate(vulnerable[:10], 1):  # Show top 10
            severity_color = {
                "Critical": "red bold",
                "High": "red",
                "Medium": "yellow",
                "Low": "blue",
            }.get(result["highest_severity"], "white")

            console.print(
                f"[bold]{i}. {result['package']}@{result['version']}[/bold] - "
                f"[{severity_color}]{result['highest_severity']}[/{severity_color}]"
            )

            for cve in result["cves"][:3]:  # Show top 3 CVEs per package
                console.print(f"   └─ {cve.cve_id} (CVSS: {cve.cvss_score or 'N/A'})")

            if len(result["cves"]) > 3:
                console.print(f"   └─ ... and {len(result['cves']) - 3} more CVEs")
            console.print()

        if len(vulnerable) > 10:
            console.print(f"... and {len(vulnerable) - 10} more vulnerable packages")
            console.print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Scan dependency files for known vulnerabilities")
    parser.add_argument(
        "--file",
        "-f",
        required=True,
        type=Path,
        help="Path to dependency file (package.json, requirements.txt, etc.)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--db",
        default="cyberintel.db",
        help="Path to database file (default: cyberintel.db)",
    )

    args = parser.parse_args()

    try:
        scanner = DependencyScanner(db_path=args.db)
        results = scanner.scan_file(args.file, verbose=args.verbose)
        print_scan_report(results, format=args.output)

        # Exit with error code if vulnerabilities found
        if results["vulnerable_dependencies"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(2)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(2)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()

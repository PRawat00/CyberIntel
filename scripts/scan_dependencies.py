"""CLI tool for scanning dependency files for vulnerabilities.

Usage:
    python -m scripts.scan_dependencies --file package.json
    python -m scripts.scan_dependencies --file requirements.txt --verbose
    python -m scripts.scan_dependencies --file package.json --output json
    python -m scripts.scan_dependencies --file package.json --output html --output-file report.html
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
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

    def __init__(self, db_path: str = "cyberintel.db", session_factory=None):
        """Initialize the scanner.

        Args:
            db_path: Path to the SQLite database (used if session_factory is None)
            session_factory: Optional SQLAlchemy session factory to use instead of creating one
        """
        import logging

        logger = logging.getLogger(__name__)

        if session_factory is not None:
            # Use provided session factory (from API)
            self.Session = session_factory
            self.engine = None  # Not needed when using external session
            logger.info("Scanner initialized with external session factory (API mode)")
        else:
            # Create own session factory (for CLI usage)
            self.engine = create_engine(f"sqlite:///{db_path}")
            self.Session = sessionmaker(bind=self.engine)
            logger.info(f"Scanner initialized with SQLite database: {db_path}")

        self.parsers = {
            "npm": NpmParser(),
            "pip": PipParser(),
        }

    def detect_file_type(self, file_path: Path) -> str:
        """Detect the type of dependency file using content analysis.

        Uses intelligent detection: checks filename, extension, and file content.
        This allows users to upload files with ANY name.

        Args:
            file_path: Path to the file

        Returns:
            File type string (npm, pip, etc.)

        Raises:
            ValueError: If file type cannot be detected
        """
        file_name = file_path.name

        # Read file content for intelligent detection
        content = None
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Binary file, fall back to name-only detection
            content = None
        except Exception:
            # File read error, fall back to name-only detection
            content = None

        # Try each parser with content-aware detection
        for file_type, parser in self.parsers.items():
            if parser.supports_file(file_name, content=content):
                return file_type

        # Build helpful error message
        raise ValueError(
            f"Could not detect file type for: {file_name}\n\n"
            f"Supported formats:\n"
            f"  - npm: .json files with package.json structure\n"
            f"    (must contain 'dependencies', 'devDependencies', or 'lockfileVersion')\n"
            f"  - pip: .txt files with requirements format\n"
            f"    (lines like: package==version, package>=version)\n\n"
            f"Tip: Ensure your file has the correct structure and extension."
        )

    # Security constants
    MAX_FILE_SIZE_MB = 1
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = {
        ".json",
        ".txt",
        ".lock",
        ".in",
        ".toml",
        ".xml",
        ".gradle",
        ".mod",
        ".sum",
    }

    def scan_file(
        self, file_path: Path, verbose: bool = False, user_id: str | None = None, session=None
    ) -> dict[str, Any]:
        """Scan a dependency file for vulnerabilities.

        Args:
            file_path: Path to the dependency file
            verbose: Whether to print verbose output
            user_id: Optional user ID for multi-tenant support
            session: Optional database session to use (if None, creates a new one)

        Returns:
            Dictionary containing scan results

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported or file is too large
            SecurityError: If file path is unsafe
        """
        # Security: Check file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Security: Validate file path (prevent path traversal)
        try:
            resolved_path = file_path.resolve(strict=True)
            if not str(resolved_path).startswith(str(Path.cwd().resolve())):
                # Allow absolute paths but warn if outside current directory
                if verbose:
                    console.print(
                        f"[yellow]Warning: Scanning file outside current directory: {resolved_path}[/yellow]"
                    )
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid file path: {e}")  # noqa: B904

        # Security: Check file size
        file_size = resolved_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"File too large: {file_size / 1024 / 1024:.2f}MB "
                f"(maximum allowed: {self.MAX_FILE_SIZE_MB}MB). "
                f"Please use a lock file or dependency manifest only."
            )

        # Security: Validate file extension
        if resolved_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            if verbose:
                console.print(
                    f"[yellow]Warning: Unusual file extension '{resolved_path.suffix}'. "
                    f"Supported: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}[/yellow]"
                )

        file_path = resolved_path  # Use resolved path for rest of processing

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

        # Create database session or use provided one
        import logging

        logger = logging.getLogger(__name__)

        if session is None:
            # Create own session (for CLI usage)
            session = self.Session()
            owns_session = True
            logger.info("Creating new database session for scan")
        else:
            # Use provided session (from API)
            owns_session = False
            logger.info("Using provided database session for scan")

        try:
            # Create scan record
            scan = Scan(
                file_name=file_path.name,
                file_type=file_type,
                file_hash=file_hash,
                scan_date=datetime.now(),
                total_dependencies=len(dependencies),
                user_id=user_id,  # Set owner (None for legacy scans)
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

            # Commit to database only if we own the session
            if owns_session:
                session.commit()
            else:
                # For external sessions, just flush to ensure data is written
                session.flush()

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
            if owns_session:
                session.rollback()
            raise e
        finally:
            if owns_session:
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


def apply_filters(
    results: dict[str, Any],
    severity_min: str | None = None,
    vulnerable_only: bool = False,
) -> dict[str, Any]:
    """Apply filters to scan results.

    Args:
        results: Scan results dictionary
        severity_min: Minimum severity level (Low, Medium, High, Critical)
        vulnerable_only: Show only vulnerable dependencies

    Returns:
        Filtered results dictionary
    """
    # Severity hierarchy for filtering
    severity_levels = {
        "Low": 1,
        "Medium": 2,
        "High": 3,
        "Critical": 4,
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
    }

    filtered_results = results.copy()
    filtered_items = []

    for item in results["results"]:
        # Filter vulnerable_only
        if vulnerable_only and not item["vulnerable"]:
            continue

        # Filter by severity
        if severity_min and item["vulnerable"]:
            # Get minimum severity threshold
            min_level = severity_levels.get(severity_min, 0)

            # Filter CVEs by severity
            filtered_cves = [
                cve for cve in item["cves"] if severity_levels.get(cve.severity, 0) >= min_level
            ]

            # If no CVEs pass the filter, skip this dependency (unless showing all)
            if not filtered_cves:
                continue

            # Update item with filtered CVEs
            item = item.copy()
            item["cves"] = filtered_cves
            item["cve_count"] = len(filtered_cves)

            # Recalculate highest severity
            if filtered_cves:
                severities = [severity_levels.get(cve.severity, 0) for cve in filtered_cves]
                max_severity = max(severities)
                severity_names = {v: k for k, v in severity_levels.items() if k == k.title()}
                item["highest_severity"] = severity_names.get(max_severity, "Unknown")

        filtered_items.append(item)

    # Update results
    filtered_results["results"] = filtered_items
    filtered_results["total_dependencies"] = len(filtered_items)
    filtered_results["vulnerable_dependencies"] = sum(1 for r in filtered_items if r["vulnerable"])

    # Recalculate severity counts and total CVEs
    severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    total_cves = 0

    for item in filtered_items:
        if item["vulnerable"]:
            for cve in item["cves"]:
                severity = cve.severity
                # Normalize severity
                if severity in ["CRITICAL", "Critical"]:
                    severity_counts["Critical"] += 1
                elif severity in ["HIGH", "High"]:
                    severity_counts["High"] += 1
                elif severity in ["MEDIUM", "Medium"]:
                    severity_counts["Medium"] += 1
                elif severity in ["LOW", "Low"]:
                    severity_counts["Low"] += 1
                total_cves += 1

    filtered_results["severity_counts"] = severity_counts
    filtered_results["total_cves"] = total_cves

    return filtered_results


def print_scan_report(
    results: dict[str, Any], format: str = "text", output_file: str | None = None
):
    """Print scan results in specified format.

    Args:
        results: Scan results dictionary
        format: Output format (text, json, html)
        output_file: Optional output file path (required for HTML format)
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

    if format == "html":
        # Generate HTML report using Jinja2
        if not output_file:
            console.print("[red]Error:[/red] --output-file is required for HTML format")
            sys.exit(2)

        # Load Jinja2 template
        template_dir = Path(__file__).parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))  # noqa: S701
        template = env.get_template("scan_report.html")

        # Prepare data for template
        vulnerable_results = [r for r in results["results"] if r["vulnerable"]]

        # Convert CveMatch objects to dicts for template
        for result in vulnerable_results:
            result["cves"] = [
                {
                    "cve_id": cve.cve_id,
                    "severity": cve.severity,
                    "cvss_score": cve.cvss_score,
                    "description": cve.description,
                }
                for cve in result["cves"]
            ]

        # Render template
        html_content = template.render(
            file_name=results["file_name"],
            file_type=results["file_type"],
            scan_id=results["scan_id"],
            total_dependencies=results["total_dependencies"],
            vulnerable_dependencies=results["vulnerable_dependencies"],
            total_cves=results["total_cves"],
            severity_counts=results["severity_counts"],
            vulnerable_results=vulnerable_results,
            scan_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        # Write to file
        output_path = Path(output_file)
        output_path.write_text(html_content, encoding="utf-8")
        console.print(f"[green]HTML report generated:[/green] {output_path.absolute()}")
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
        choices=["text", "json", "html"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Output file path (required for HTML format)",
    )
    parser.add_argument(
        "--severity-min",
        choices=["Low", "Medium", "High", "Critical"],
        help="Minimum severity level to report (filters out lower severity CVEs)",
    )
    parser.add_argument(
        "--vulnerable-only",
        action="store_true",
        help="Show only vulnerable dependencies (hide safe ones)",
    )
    parser.add_argument(
        "--include-dev",
        action="store_true",
        default=True,
        help="Include dev dependencies in scan (default: True)",
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

        # Apply filters
        results = apply_filters(
            results,
            severity_min=args.severity_min,
            vulnerable_only=args.vulnerable_only,
        )

        print_scan_report(results, format=args.output, output_file=args.output_file)

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

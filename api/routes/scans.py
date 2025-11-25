"""
Scan-related API endpoints.
"""

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import joinedload

from api.middleware.auth import RequireAuth, User
from api.models import (
    CveResponse,
    DependencyResponse,
    ScanDetail,
    ScanListResponse,
    ScanSummary,
    SeverityCount,
    StatsResponse,
)
from database.db import get_db_session
from database.models import Dependency, Scan
from scripts.scan_dependencies import DependencyScanner

router = APIRouter()

# File upload constraints
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB
ALLOWED_EXTENSIONS = {".json", ".txt", ".lock", ".in", ".toml", ".mod", ".sum"}


@router.post("/scans", response_model=ScanDetail, status_code=201)
async def create_scan(user: User = RequireAuth, file: UploadFile = File(...)):
    """
    Upload and scan a dependency file.

    Accepts: package.json, requirements.txt, Pipfile, package-lock.json, etc.
    Returns: Scan results with vulnerabilities

    Requires authentication.

    Note: Parameter order matters! Auth dependencies must come before File/Form parameters
    to avoid FastAPI route resolution issues with multipart/form-data.
    """
    # Validate file extension

    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")  # noqa: B904

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB",
        )

    # Save to temporary file for processing
    # Use original filename so parsers can detect file type
    tmp_dir = None
    tmp_path = None

    try:
        tmp_dir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, file.filename)
        with open(tmp_path, "wb") as f:
            f.write(content)

        # Use the same database session for scanning and fetching results
        with get_db_session() as session:
            # Get the global database manager (uses same config as session)
            from database.db import get_db_manager

            db_manager = get_db_manager()

            # Log which database we're using
            import logging

            logger = logging.getLogger(__name__)
            logger.info(f"Using database engine: {db_manager.engine.url}")

            # Initialize scanner with the session factory from global manager
            scanner = DependencyScanner(session_factory=db_manager.SessionLocal)

            # Scan the file using the provided session
            result = scanner.scan_file(Path(tmp_path), user_id=user.id, session=session)
            scan_id = result["scan_id"]

            logger.info(f"Scan completed successfully with scan_id: {scan_id}")

            # Commit the transaction to ensure data is persisted
            session.commit()

    except Exception as e:
        # Log the error details for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Scan failed: {type(e).__name__}: {str(e)}", exc_info=True)

        # Clean up temp file and directory if they exist
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:  # noqa: S110
                pass
        if tmp_dir and os.path.exists(tmp_dir):
            try:
                os.rmdir(tmp_dir)
            except Exception:  # noqa: S110
                pass

        # Provide more specific error messages based on exception type
        if "database" in str(e).lower() or "connection" in str(e).lower():
            detail = f"Database error during scan: {str(e)}"
        elif "permission" in str(e).lower():
            detail = f"Permission error during scan: {str(e)}"
        else:
            detail = f"Scan failed: {str(e)}"

        raise HTTPException(status_code=500, detail=detail)  # noqa: B904
    finally:
        # Always clean up temp files
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:  # noqa: S110
                pass
        if tmp_dir and os.path.exists(tmp_dir):
            try:
                os.rmdir(tmp_dir)
            except Exception:  # noqa: S110
                pass

    # Fetch scan results from database using the same session management
    with get_db_session() as session:
        scan = (
            session.query(Scan)
            .options(joinedload(Scan.dependencies).joinedload(Dependency.cves))
            .filter(Scan.id == scan_id)
            .first()
        )

        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        # Build response
        return _build_scan_detail(scan)


@router.get("/scans", response_model=ScanListResponse)
async def list_scans(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    file_type: str | None = Query(None, description="Filter by file type (npm, pip, etc.)"),
    user: User = RequireAuth,
):
    """
    List all scans with pagination (filtered by current user).

    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    - file_type: Filter by ecosystem (npm, pip, go, etc.)

    Requires authentication. Only returns scans owned by the authenticated user.
    """
    with get_db_session() as session:
        # Base query - filter by user
        query = session.query(Scan).filter(Scan.user_id == user.id)

        # Apply additional filters
        if file_type:
            query = query.filter(Scan.file_type == file_type)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        scans = query.order_by(desc(Scan.scan_date)).offset(offset).limit(per_page).all()

        # Calculate pages
        pages = (total + per_page - 1) // per_page

        return ScanListResponse(
            scans=[_build_scan_summary(scan) for scan in scans],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )


@router.get("/scans/{scan_id}", response_model=ScanDetail)
async def get_scan(scan_id: int, user: User = RequireAuth):
    """
    Get detailed scan results by ID.

    Returns full scan information including all dependencies and CVEs.
    Requires authentication and validates ownership.
    """
    with get_db_session() as session:
        scan = (
            session.query(Scan)
            .options(joinedload(Scan.dependencies).joinedload(Dependency.cves))
            .filter(Scan.id == scan_id)
            .first()
        )

        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        # Validate ownership
        if scan.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied: You don't own this scan")

        return _build_scan_detail(scan)


@router.get("/scans/{scan_id}/dependencies", response_model=list[DependencyResponse])
async def get_scan_dependencies(
    scan_id: int,
    vulnerable_only: bool = Query(False, description="Show only vulnerable dependencies"),
    severity_min: str | None = Query(
        None, description="Minimum severity (Low, Medium, High, Critical)"
    ),
    user: User = RequireAuth,
):
    """
    Get dependencies for a specific scan with optional filtering.

    Query parameters:
    - vulnerable_only: Show only vulnerable packages
    - severity_min: Filter by minimum severity level

    Requires authentication and validates scan ownership.
    """
    with get_db_session() as session:
        # Check if scan exists
        scan = session.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        # Validate ownership
        if scan.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied: You don't own this scan")

        # Query dependencies
        query = (
            session.query(Dependency)
            .options(joinedload(Dependency.cves))
            .filter(Dependency.scan_id == scan_id)
        )

        # Apply filters
        if vulnerable_only:
            query = query.filter(Dependency.is_vulnerable == True)  # noqa: E712

        if severity_min:
            severity_order = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
            if severity_min not in severity_order:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid severity. Use: Low, Medium, High, Critical",
                )
            # This is a simplified filter - you may want to improve this
            query = query.filter(Dependency.highest_severity == severity_min)

        dependencies = query.all()

        return [_build_dependency_response(dep) for dep in dependencies]


@router.get("/scans/{scan_id}/export")
async def export_scan(
    scan_id: int,
    format: str = Query("json", description="Export format (json, csv, html)"),
    user: User = RequireAuth,
):
    """
    Export scan results in various formats.

    Supported formats:
    - json: Machine-readable JSON
    - csv: Comma-separated values
    - html: HTML report

    Requires authentication and validates scan ownership.
    """
    with get_db_session() as session:
        scan = (
            session.query(Scan)
            .options(joinedload(Scan.dependencies).joinedload(Dependency.cves))
            .filter(Scan.id == scan_id)
            .first()
        )

        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        # Validate ownership
        if scan.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied: You don't own this scan")

        if format == "json":
            # Return JSON response
            scan_detail = _build_scan_detail(scan)
            return JSONResponse(content=scan_detail.model_dump())

        elif format == "csv":
            # Generate CSV
            csv_content = _generate_csv(scan)
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}.csv"},
            )

        elif format == "html":
            # Generate HTML report (reuse existing template)
            html_content = _generate_html_report(scan)
            return Response(
                content=html_content,
                media_type="text/html",
                headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}.html"},
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid format. Supported: json, csv, html",
            )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(user: User = RequireAuth):
    """
    Get dashboard statistics for the current user.

    Returns user-specific statistics and recent scans.
    Requires authentication.
    """
    with get_db_session() as session:
        # Total scans (user-scoped)
        total_scans = session.query(Scan).filter(Scan.user_id == user.id).count()

        # Total dependencies scanned (user-scoped)
        total_deps = (
            session.query(func.sum(Scan.total_dependencies))
            .filter(Scan.user_id == user.id)
            .scalar()
            or 0
        )

        # Total vulnerabilities (user-scoped)
        total_vulns = (
            session.query(func.sum(Scan.total_cves)).filter(Scan.user_id == user.id).scalar() or 0
        )

        # Critical vulnerabilities (user-scoped)
        critical_vulns = (
            session.query(func.sum(Scan.critical_count)).filter(Scan.user_id == user.id).scalar()
            or 0
        )

        # Recent scans (last 10, user-scoped)
        recent_scans = (
            session.query(Scan)
            .filter(Scan.user_id == user.id)
            .order_by(desc(Scan.scan_date))
            .limit(10)
            .all()
        )

        return StatsResponse(
            total_scans=total_scans,
            total_dependencies_scanned=int(total_deps),
            total_vulnerabilities_found=int(total_vulns),
            critical_vulnerabilities=int(critical_vulns),
            recent_scans=[_build_scan_summary(scan) for scan in recent_scans],
        )


@router.delete("/scans/{scan_id}", status_code=204)
async def delete_scan(scan_id: int, user: User = RequireAuth):
    """
    Delete a scan and all associated data.

    Requires authentication and validates scan ownership.
    """
    with get_db_session() as session:
        scan = session.query(Scan).filter(Scan.id == scan_id).first()

        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        # Validate ownership
        if scan.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied: You don't own this scan")

        session.delete(scan)
        session.commit()

        return Response(status_code=204)


@router.get("/samples/{filename}")
async def get_sample_file(filename: str):
    """
    Serve sample files for demo purposes.

    Available files:
    - vulnerable-requirements.txt
    - package-lock.json
    - Pipfile

    No authentication required for demo files.
    """
    # Whitelist of allowed sample files
    ALLOWED_SAMPLES = {
        "vulnerable-requirements.txt",
        "package-lock.json",
        "Pipfile",
    }

    if filename not in ALLOWED_SAMPLES:
        raise HTTPException(
            status_code=404,
            detail=f"Sample file not found. Available: {', '.join(ALLOWED_SAMPLES)}",
        )

    # Build path to sample file
    samples_dir = Path(__file__).parent.parent.parent / "test_samples"
    file_path = samples_dir / filename

    # Check if file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Sample file '{filename}' not found on server")

    # Return file
    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")


# Helper functions


def _build_scan_summary(scan: Scan) -> ScanSummary:
    """Build ScanSummary from database model."""
    return ScanSummary(
        id=scan.id,
        file_name=scan.file_name,
        file_type=scan.file_type,
        scan_date=scan.scan_date,
        total_dependencies=scan.total_dependencies,
        vulnerable_dependencies=scan.vulnerable_dependencies,
        total_cves=scan.total_cves,
        severity_counts=SeverityCount(
            critical=scan.critical_count or 0,
            high=scan.high_count or 0,
            medium=scan.medium_count or 0,
            low=scan.low_count or 0,
        ),
        source=scan.source or "upload",
        github_repo=scan.github_repo,
        github_path=scan.github_path,
    )


def _build_scan_detail(scan: Scan) -> ScanDetail:
    """Build ScanDetail with dependencies from database model."""
    summary = _build_scan_summary(scan)

    dependencies = [_build_dependency_response(dep) for dep in scan.dependencies]

    return ScanDetail(
        **summary.model_dump(),
        dependencies=dependencies,
    )


def _build_dependency_response(dep: Dependency) -> DependencyResponse:
    """Build DependencyResponse from database model."""
    cves = [
        CveResponse(
            cve_id=cve.cve_id,
            severity=cve.severity or "UNKNOWN",
            cvss_score=cve.cvss_score,
            description=cve.description or "",
            published_date=cve.published_date.isoformat() if cve.published_date else None,
            vendor=cve.vendor,
            product=cve.product,
            affected_version=cve.version,
        )
        for cve in dep.cves
    ]

    return DependencyResponse(
        id=dep.id,
        package_name=dep.package_name,
        version=dep.version,
        ecosystem=dep.ecosystem,
        is_vulnerable=dep.is_vulnerable,
        cve_count=dep.cve_count or 0,
        highest_severity=dep.highest_severity,
        cves=cves,
    )


def _generate_csv(scan: Scan) -> str:
    """Generate CSV export of scan results."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        [
            "Package",
            "Version",
            "Ecosystem",
            "Vulnerable",
            "CVE Count",
            "Highest Severity",
            "CVE IDs",
        ]
    )

    # Write dependencies
    for dep in scan.dependencies:
        cve_ids = ", ".join([cve.cve_id for cve in dep.cves])
        writer.writerow(
            [
                dep.package_name,
                dep.version,
                dep.ecosystem,
                "Yes" if dep.is_vulnerable else "No",
                dep.cve_count,
                dep.highest_severity or "N/A",
                cve_ids or "None",
            ]
        )

    return output.getvalue()


def _generate_html_report(scan: Scan) -> str:
    """Generate HTML report using existing template."""
    from pathlib import Path

    from jinja2 import Environment, FileSystemLoader

    # Load template
    template_dir = Path(__file__).parent.parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))  # noqa: S701
    template = env.get_template("scan_report.html")

    # Prepare data
    scan_data = _build_scan_detail(scan)

    # Render template
    html = template.render(
        scan_id=scan.id,
        file_name=scan.file_name,
        scan_date=scan.scan_date.strftime("%Y-%m-%d %H:%M:%S"),
        total_dependencies=scan.total_dependencies,
        vulnerable_dependencies=scan.vulnerable_dependencies,
        total_cves=scan.total_cves,
        severity_counts=scan_data.severity_counts.model_dump(),
        dependencies=scan_data.dependencies,
    )

    return html

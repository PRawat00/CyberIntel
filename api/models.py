"""
Pydantic models for API request/response validation.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CveResponse(BaseModel):
    """CVE information in API responses."""

    cve_id: str
    severity: str
    cvss_score: float | None = None
    description: str
    published_date: str | None = None
    vendor: str | None = None
    product: str | None = None
    affected_version: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DependencyResponse(BaseModel):
    """Dependency information in scan results."""

    id: int
    package_name: str
    version: str
    ecosystem: str
    is_vulnerable: bool
    cve_count: int
    highest_severity: str | None = None
    cves: list[CveResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SeverityCount(BaseModel):
    """Severity breakdown."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class ScanSummary(BaseModel):
    """Scan summary information."""

    id: int
    file_name: str
    file_type: str
    scan_date: datetime
    total_dependencies: int
    vulnerable_dependencies: int
    total_cves: int
    severity_counts: SeverityCount

    model_config = ConfigDict(from_attributes=True)


class ScanDetail(ScanSummary):
    """Detailed scan results with dependencies."""

    dependencies: list[DependencyResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ScanListResponse(BaseModel):
    """Paginated list of scans."""

    scans: list[ScanSummary]
    total: int
    page: int
    per_page: int
    pages: int


class StatsResponse(BaseModel):
    """Dashboard statistics."""

    total_scans: int
    total_dependencies_scanned: int
    total_vulnerabilities_found: int
    critical_vulnerabilities: int
    recent_scans: list[ScanSummary]


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    message: str
    details: dict[str, Any] | None = None

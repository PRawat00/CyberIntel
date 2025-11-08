"""NVD (National Vulnerability Database) API fetcher."""

import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests
import yaml
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class CVSSMetrics(BaseModel):
    """CVSS (Common Vulnerability Scoring System) metrics."""

    version: str | None = None
    vector_string: str | None = None
    base_score: float | None = None
    base_severity: str | None = None
    attack_vector: str | None = None
    attack_complexity: str | None = None
    privileges_required: str | None = None
    user_interaction: str | None = None


class CVEData(BaseModel):
    """Pydantic model for validated CVE data."""

    cve_id: str = Field(..., description="CVE ID (e.g., CVE-2025-1234)")
    description: str = Field(..., description="CVE description")
    published_date: datetime = Field(..., description="Publication date")
    last_modified: datetime = Field(..., description="Last modification date")
    severity: str | None = Field(None, description="Severity level")
    cvss_score: float | None = Field(None, description="CVSS base score")
    cvss_vector: str | None = Field(None, description="CVSS vector string")
    attack_vector: str | None = Field(None, description="Attack vector")
    attack_complexity: str | None = Field(None, description="Attack complexity")
    privileges_required: str | None = Field(None, description="Privileges required")
    user_interaction: str | None = Field(None, description="User interaction")
    vendor: str | None = Field(None, description="Affected vendor")
    product: str | None = Field(None, description="Affected product")
    references: list[str] | None = Field(default_factory=list, description="Reference URLs")
    cwe_ids: list[str] | None = Field(default_factory=list, description="CWE IDs")
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Raw JSON data")


class NVDFetcher:
    """Fetches CVE data from the NVD API with rate limiting."""

    def __init__(self, config_path: str = "configs/config.yaml"):
        """Initialize NVD fetcher.

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.nvd_config = self.config.get("nvd", {})
        self.base_url = self.nvd_config.get("base_url")
        self.api_key = os.getenv("NVD_API_KEY") or self.nvd_config.get("api_key")

        # Rate limiting
        rate_limit_config = self.nvd_config.get("rate_limit", {})
        self.requests_per_period = rate_limit_config.get("requests_per_period", 5)
        self.period_seconds = rate_limit_config.get("period_seconds", 30)
        self.request_timestamps: list[float] = []

        # Request configuration
        self.default_results_per_page = self.nvd_config.get("default_results_per_page", 100)
        self.max_results_per_page = self.nvd_config.get("max_results_per_page", 2000)

        # Retry configuration
        ingestion_config = self.config.get("ingestion", {})
        self.retry_attempts = ingestion_config.get("retry_attempts", 3)
        self.retry_delay = ingestion_config.get("retry_delay_seconds", 5)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file) as f:
            return yaml.safe_load(f)

    def _rate_limit(self):
        """Implement rate limiting based on configuration."""
        now = time.time()

        # Remove timestamps older than the rate limit period
        self.request_timestamps = [
            ts for ts in self.request_timestamps if now - ts < self.period_seconds
        ]

        # If we've hit the rate limit, wait
        if len(self.request_timestamps) >= self.requests_per_period:
            oldest_timestamp = self.request_timestamps[0]
            wait_time = self.period_seconds - (now - oldest_timestamp)
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                # Clean up old timestamps after waiting
                now = time.time()
                self.request_timestamps = [
                    ts for ts in self.request_timestamps if now - ts < self.period_seconds
                ]

        # Record this request
        self.request_timestamps.append(time.time())

    def _make_request(self, params: dict[str, Any]) -> dict[str, Any]:
        """Make HTTP request to NVD API with retry logic.

        Args:
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.RequestException: If request fails after retries
        """
        headers = {}
        if self.api_key:
            headers["apiKey"] = self.api_key

        for attempt in range(self.retry_attempts):
            try:
                self._rate_limit()
                response = requests.get(self.base_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"All retry attempts failed for request: {params}")
                    raise

        return {}

    def _parse_cve_item(self, cve_item: dict[str, Any]) -> CVEData | None:
        """Parse a single CVE item from NVD API response.

        Args:
            cve_item: CVE item from API response

        Returns:
            CVEData object or None if parsing fails
        """
        try:
            cve = cve_item.get("cve", {})
            cve_id = cve.get("id")

            # Extract description
            descriptions = cve.get("descriptions", [])
            description = ""
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break

            # Extract dates
            published = cve.get("published")
            last_modified = cve.get("lastModified")

            if not all([cve_id, description, published, last_modified]):
                logger.warning(f"Missing required fields for CVE: {cve_id}")
                return None

            # Extract CVSS metrics (prefer v3.1, fall back to v3.0, then v2.0)
            metrics = cve.get("metrics", {})
            cvss_data = None

            if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
                cvss_data = metrics["cvssMetricV31"][0].get("cvssData", {})
            elif "cvssMetricV30" in metrics and metrics["cvssMetricV30"]:
                cvss_data = metrics["cvssMetricV30"][0].get("cvssData", {})
            elif "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
                cvss_data = metrics["cvssMetricV2"][0].get("cvssData", {})

            severity = None
            cvss_score = None
            cvss_vector = None
            attack_vector = None
            attack_complexity = None
            privileges_required = None
            user_interaction = None

            if cvss_data:
                severity = cvss_data.get("baseSeverity")
                cvss_score = cvss_data.get("baseScore")
                cvss_vector = cvss_data.get("vectorString")
                attack_vector = cvss_data.get("attackVector")
                attack_complexity = cvss_data.get("attackComplexity")
                privileges_required = cvss_data.get("privilegesRequired")
                user_interaction = cvss_data.get("userInteraction")

            # Extract affected products (CPE - Common Platform Enumeration)
            configurations = cve.get("configurations", [])
            vendor = None
            product = None

            for config in configurations:
                nodes = config.get("nodes", [])
                for node in nodes:
                    cpe_matches = node.get("cpeMatch", [])
                    if cpe_matches:
                        # Parse first CPE match
                        cpe = cpe_matches[0].get("criteria", "")
                        # CPE format: cpe:2.3:a:vendor:product:version:...
                        cpe_parts = cpe.split(":")
                        if len(cpe_parts) >= 5:
                            vendor = cpe_parts[3]
                            product = cpe_parts[4]
                        break
                if vendor:
                    break

            # Extract references
            references = []
            ref_list = cve.get("references", [])
            for ref in ref_list:
                url = ref.get("url")
                if url:
                    references.append(url)

            # Extract CWE IDs
            cwe_ids = []
            weaknesses = cve.get("weaknesses", [])
            for weakness in weaknesses:
                descriptions = weakness.get("description", [])
                for desc in descriptions:
                    cwe_id = desc.get("value")
                    if cwe_id and cwe_id.startswith("CWE-"):
                        cwe_ids.append(cwe_id)

            # Create CVEData object
            cve_data = CVEData(
                cve_id=cve_id,
                description=description,
                published_date=datetime.fromisoformat(published.replace("Z", "+00:00")),
                last_modified=datetime.fromisoformat(last_modified.replace("Z", "+00:00")),
                severity=severity,
                cvss_score=cvss_score,
                cvss_vector=cvss_vector,
                attack_vector=attack_vector,
                attack_complexity=attack_complexity,
                privileges_required=privileges_required,
                user_interaction=user_interaction,
                vendor=vendor,
                product=product,
                references=references,
                cwe_ids=cwe_ids,
                raw_data=cve_item,
            )

            return cve_data

        except (KeyError, ValueError, ValidationError) as e:
            logger.error(f"Error parsing CVE {cve_item.get('cve', {}).get('id', 'UNKNOWN')}: {e}")
            return None

    def fetch_recent_cves(
        self, days: int = 7, results_per_page: int = 100, max_results: int | None = None
    ) -> list[CVEData]:
        """Fetch CVEs published in the last N days.

        Args:
            days: Number of days to look back
            results_per_page: Results per API request
            max_results: Maximum total results to fetch (None for unlimited)

        Returns:
            List of CVEData objects
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Fetching CVEs from {start_date.date()} to {end_date.date()}")

        return self.fetch_cves_by_date_range(
            start_date=start_date,
            end_date=end_date,
            results_per_page=results_per_page,
            max_results=max_results,
        )

    def fetch_cves_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        results_per_page: int = 100,
        max_results: int | None = None,
    ) -> list[CVEData]:
        """Fetch CVEs within a specific date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            results_per_page: Results per API request
            max_results: Maximum total results to fetch (None for unlimited)

        Returns:
            List of CVEData objects
        """
        all_cves: list[CVEData] = []
        start_index = 0
        total_fetched = 0

        # Format dates for API (ISO 8601)
        pub_start_date = start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        pub_end_date = end_date.strftime("%Y-%m-%dT%H:%M:%S.000")

        while True:
            params = {
                "pubStartDate": pub_start_date,
                "pubEndDate": pub_end_date,
                "resultsPerPage": min(results_per_page, self.max_results_per_page),
                "startIndex": start_index,
            }

            logger.info(f"Fetching CVEs (startIndex={start_index}, limit={results_per_page})...")

            try:
                data = self._make_request(params)
            except Exception as e:
                logger.error(f"Failed to fetch CVEs: {e}")
                break

            # Parse response
            total_results = data.get("totalResults", 0)
            vulnerabilities = data.get("vulnerabilities", [])

            logger.info(
                f"Found {total_results} total results. Processing {len(vulnerabilities)} CVEs..."
            )

            # Parse each CVE
            for vuln in vulnerabilities:
                cve_data = self._parse_cve_item(vuln)
                if cve_data:
                    all_cves.append(cve_data)
                    total_fetched += 1

                    # Check if we've reached max_results
                    if max_results and total_fetched >= max_results:
                        logger.info(f"Reached maximum results limit: {max_results}")
                        return all_cves

            # Check if there are more results to fetch
            start_index += len(vulnerabilities)
            if start_index >= total_results:
                break

        logger.info(f"Successfully fetched {len(all_cves)} CVEs")
        return all_cves

    def fetch_cve_by_id(self, cve_id: str) -> CVEData | None:
        """Fetch a specific CVE by ID.

        Args:
            cve_id: CVE ID (e.g., CVE-2025-1234)

        Returns:
            CVEData object or None if not found
        """
        params = {"cveId": cve_id}

        logger.info(f"Fetching CVE: {cve_id}")

        try:
            data = self._make_request(params)
            vulnerabilities = data.get("vulnerabilities", [])

            if vulnerabilities:
                cve_data = self._parse_cve_item(vulnerabilities[0])
                if cve_data:
                    logger.info(f"Successfully fetched {cve_id}")
                    return cve_data

            logger.warning(f"CVE not found: {cve_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to fetch CVE {cve_id}: {e}")
            return None

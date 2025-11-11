"""NVD (National Vulnerability Database) API fetcher."""

import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

# Load environment variables from .env file
load_dotenv()

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

        # Log API key status (without exposing full key)
        if self.api_key:
            key_prefix = self.api_key[:8] if len(self.api_key) >= 8 else self.api_key[:4]
            logger.info(f"NVD API key loaded: {key_prefix}... (length: {len(self.api_key)})")
        else:
            logger.warning("No NVD API key found. Using public rate limits (5 req/30s)")

        # Rate limiting
        rate_limit_config = self.nvd_config.get("rate_limit", {})
        self.requests_per_period = rate_limit_config.get("requests_per_period", 5)
        self.period_seconds = rate_limit_config.get("period_seconds", 30)
        self.min_delay = rate_limit_config.get("min_delay_between_requests", 0.6)
        self.request_timestamps: list[float] = []

        # Log rate limiting configuration
        logger.info(
            f"Rate limiting: {self.requests_per_period} requests per {self.period_seconds}s "
            f"with {self.min_delay}s minimum delay between requests"
        )

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
        """Implement rate limiting based on configuration.

        NVD API requires requests to be spread over the time window,
        not sent in bursts. This implementation ensures proper spacing.
        """
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

        # Add delay between requests to prevent bursting
        # Use configured min_delay or calculate from rate limit
        min_delay = max(self.min_delay, self.period_seconds / self.requests_per_period)
        if self.request_timestamps:
            time_since_last = now - self.request_timestamps[-1]
            if time_since_last < min_delay:
                sleep_time = min_delay - time_since_last
                time.sleep(sleep_time)

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

    def test_api_key(self) -> bool:
        """Test if the API key is working properly.

        Makes a simple request with 1 result to verify the API key is valid
        and properly authenticated.

        Returns:
            True if API key is working, False otherwise
        """
        if not self.api_key:
            logger.info("No API key configured - skipping API key test")
            return True  # Not an error if no key is configured

        logger.info("Testing NVD API key validity...")

        try:
            # Make a simple request for just 1 CVE
            params = {"resultsPerPage": 1}
            headers = {"apiKey": self.api_key}

            response = requests.get(self.base_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            total_results = data.get("totalResults", 0)

            if total_results > 0:
                logger.info("API key test successful - key is valid and working")
                return True
            else:
                logger.warning("API key test returned no results - this may be a temporary issue")
                return False

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.error(
                    "API key test failed: 403 Forbidden - API key may be invalid or not activated"
                )
                logger.error("Please check that you clicked the activation link in the email")
                return False
            elif e.response.status_code == 429:
                logger.warning(
                    "API key test failed: 429 Too Many Requests - "
                    "API key may need time to propagate (wait 10-30 minutes after activation)"
                )
                return False
            else:
                logger.error(f"API key test failed with HTTP error: {e}")
                return False
        except Exception as e:
            logger.error(f"API key test failed with error: {e}")
            return False

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

    def _get_existing_cve_ids(self, start_date: datetime, end_date: datetime) -> set[str]:
        """Query database for existing CVE IDs within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Set of CVE IDs that already exist in the database
        """
        try:
            from database.db import get_db_session
            from database.models import CVE

            with get_db_session() as session:
                existing_cves = (
                    session.query(CVE.cve_id)
                    .filter(CVE.published_date >= start_date, CVE.published_date <= end_date)
                    .all()
                )

                cve_ids = {cve.cve_id for cve in existing_cves}
                logger.info(
                    f"Found {len(cve_ids)} existing CVEs in database for date range {start_date.date()} to {end_date.date()}"
                )
                return cve_ids

        except Exception as e:
            logger.warning(f"Could not query existing CVEs from database: {e}")
            return set()

    def get_nvd_cve_count(self, start_date: datetime, end_date: datetime) -> int:
        """Query NVD API for total CVE count in date range.

        This makes a minimal API request (resultsPerPage=1) to get only the
        total count, avoiding unnecessary data transfer.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Total number of CVEs in the date range according to NVD
        """
        # Format dates for API (ISO 8601 with UTC timezone marker)
        pub_start_date = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        pub_end_date = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        params = {
            "pubStartDate": pub_start_date,
            "pubEndDate": pub_end_date,
            "resultsPerPage": 1,  # Minimal data transfer - we only need the count
            "startIndex": 0,
        }

        try:
            data = self._make_request(params)
            total_results = data.get("totalResults", 0)
            logger.debug(
                f"NVD reports {total_results} CVEs for {start_date.date()} to {end_date.date()}"
            )
            return total_results
        except Exception as e:
            logger.error(f"Failed to get NVD CVE count: {e}")
            return 0

    def get_db_cve_count(self, start_date: datetime, end_date: datetime) -> int:
        """Query database for CVE count in date range.

        Uses indexed published_date field for fast O(log n) query.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Number of CVEs in database for the date range
        """
        try:
            from sqlalchemy import func

            from database.db import get_db_session
            from database.models import CVE

            with get_db_session() as session:
                count = (
                    session.query(func.count(CVE.cve_id))
                    .filter(
                        CVE.published_date >= start_date,
                        CVE.published_date < end_date,  # Use < for clean boundaries
                    )
                    .scalar()
                )

                count = count or 0
                logger.debug(
                    f"Database has {count} CVEs for {start_date.date()} to {end_date.date()}"
                )
                return count

        except Exception as e:
            logger.warning(f"Could not query database CVE count: {e}")
            return 0

    def get_latest_cve_date(self) -> datetime | None:
        """Get the publication date of the most recent CVE in the database.

        Useful for determining where to start incremental updates.

        Returns:
            Most recent CVE publication date, or None if database is empty
        """
        try:
            from sqlalchemy import func

            from database.db import get_db_session
            from database.models import CVE

            with get_db_session() as session:
                max_date = session.query(func.max(CVE.published_date)).scalar()

                if max_date:
                    logger.info(f"Latest CVE in database published: {max_date.date()}")
                else:
                    logger.info("Database is empty, no CVEs found")

                return max_date

        except Exception as e:
            logger.warning(f"Could not query latest CVE date: {e}")
            return None

    def _create_120_day_chunks(
        self, start_date: datetime, end_date: datetime
    ) -> list[tuple[datetime, datetime]]:
        """Split a date range into 120-day chunks (NVD API limit).

        Args:
            start_date: Start date of full range
            end_date: End date of full range

        Returns:
            List of (chunk_start, chunk_end) tuples, each ≤ 120 days
        """
        chunks = []
        current_start = start_date
        max_chunk_days = 120

        while current_start < end_date:
            current_end = min(current_start + timedelta(days=max_chunk_days), end_date)
            chunks.append((current_start, current_end))
            current_start = current_end

        logger.info(f"Split date range into {len(chunks)} chunks of ≤120 days")
        return chunks

    def find_gap_start(
        self, start_date: datetime, end_date: datetime, min_days_threshold: int = 1
    ) -> datetime | None:
        """Use binary search to find where CVE data gaps begin.

        This method recursively searches a date range to find the exact point
        where missing CVE data starts, using O(log n) binary search.

        IMPORTANT: This method should only be called on ranges ≤ 120 days
        due to NVD API limitations.

        Args:
            start_date: Start of date range to check (inclusive)
            end_date: End of date range to check (inclusive)
            min_days_threshold: Minimum days span to continue searching (default: 1)

        Returns:
            - None if no gap exists (database has all CVEs for this range)
            - datetime of where the gap starts if missing data is found
        """
        # Safety check: enforce 120-day limit for NVD API
        days_span = (end_date - start_date).days
        if days_span > 120:
            logger.error(
                f"Binary search called on range > 120 days ({days_span} days). "
                f"This violates NVD API limits. Use chunk-based sync instead."
            )
            # Return start_date to trigger fetch of entire range
            return start_date

        logger.debug(f"Checking gap in range {start_date.date()} to {end_date.date()}")

        # Query both NVD and database for counts
        nvd_count = self.get_nvd_cve_count(start_date, end_date)
        db_count = self.get_db_cve_count(start_date, end_date)

        # No gap - database has all CVEs
        if nvd_count == db_count:
            logger.debug(f"No gap: both have {nvd_count} CVEs")
            return None

        # Complete gap - database has no CVEs for this range
        if db_count == 0:
            logger.debug(f"Complete gap: missing all {nvd_count} CVEs")
            return start_date

        # Data inconsistency - database has more CVEs than NVD reports
        # This can happen due to CVEs being removed/updated or timezone differences
        # Continue with binary search to find new CVEs - skip-existing will handle duplicates
        if db_count > nvd_count:
            logger.warning(
                f"Count mismatch: DB has {db_count} CVEs but NVD reports {nvd_count}. "
                f"Continuing binary search to find any new CVEs..."
            )
            # Don't return early - continue with binary search below

        # Calculate date range span in days
        days_span = (end_date - start_date).days

        # Base case: if range is at minimum threshold, this is where the gap starts
        if days_span <= min_days_threshold:
            logger.debug(f"Gap found at {start_date.date()} (base case, {days_span} day range)")
            return start_date

        # Binary search: split range in half
        mid_date = start_date + timedelta(days=days_span // 2)

        logger.debug(f"Binary search: splitting at {mid_date.date()}")

        # Check first half for gaps
        nvd_count_first = self.get_nvd_cve_count(start_date, mid_date)
        db_count_first = self.get_db_cve_count(start_date, mid_date)

        if nvd_count_first != db_count_first:
            # Gap exists in first half - recurse there
            logger.debug(f"Gap in first half ({db_count_first}/{nvd_count_first} CVEs)")
            return self.find_gap_start(start_date, mid_date, min_days_threshold)
        else:
            # First half is complete, gap must be in second half - recurse there
            logger.debug("First half complete, checking second half")
            next_start = mid_date + timedelta(days=1)
            return self.find_gap_start(next_start, end_date, min_days_threshold)

    def smart_sync_cves(
        self,
        start_date: datetime,
        end_date: datetime,
        results_per_page: int = 100,
        max_results: int | None = None,
    ) -> dict:
        """Intelligently sync CVEs using 120-day chunking + binary search.

        This method splits large date ranges into 120-day chunks (NVD API limit),
        then uses binary search within each chunk to find exact gaps.

        Strategy:
        - Match: Skip chunk entirely (already have all data)
        - Empty: Fetch whole chunk
        - Mismatch: Binary search within chunk to find exact gap

        Args:
            start_date: Start date for sync range
            end_date: End date for sync range
            results_per_page: Results per API request (default: 100)
            max_results: Maximum total results to fetch (None for unlimited)

        Returns:
            Dictionary with sync statistics
        """
        logger.info(f"Starting smart sync for {start_date.date()} to {end_date.date()}")

        # Track API calls for statistics
        initial_request_count = len(self.request_timestamps)
        total_days = (end_date - start_date).days

        # Split into 120-day chunks to respect NVD API limits
        chunks = self._create_120_day_chunks(start_date, end_date)

        logger.info(f"Checking {len(chunks)} chunks for gaps using smart detection...")

        gaps_to_fetch = []
        chunks_skipped = 0
        chunks_with_gaps = 0

        # Process each chunk
        for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
            logger.info(f"Chunk {i}/{len(chunks)}: {chunk_start.date()} to {chunk_end.date()}")

            # Get counts for this chunk
            nvd_count = self.get_nvd_cve_count(chunk_start, chunk_end)
            db_count = self.get_db_cve_count(chunk_start, chunk_end)

            # Handle edge case: NVD reports 0 but DB has data
            # This usually means the query had issues or CVEs were removed
            if nvd_count == 0 and db_count > 0:
                logger.warning(
                    f"Chunk {i}: NVD reports 0 CVEs but DB has {db_count}. "
                    f"Skipping (data already present or query error)."
                )
                chunks_skipped += 1
                continue

            # Case 1: Perfect match - skip this chunk
            if nvd_count == db_count and nvd_count > 0:
                logger.info(f"Chunk {i}: Match ({nvd_count} CVEs) - Skipping ✓")
                chunks_skipped += 1
                continue

            # Case 2: Empty database for this chunk - fetch entire chunk
            elif db_count == 0 and nvd_count > 0:
                logger.info(f"Chunk {i}: Empty DB, NVD has {nvd_count} CVEs - Fetching all")
                gaps_to_fetch.append((chunk_start, chunk_end))
                chunks_with_gaps += 1

            # Case 3: Count mismatch - use binary search within chunk
            else:
                logger.info(
                    f"Chunk {i}: Mismatch (DB={db_count}, NVD={nvd_count}) - Binary searching..."
                )
                gap_start = self.find_gap_start(chunk_start, chunk_end)
                if gap_start:
                    logger.info(f"Chunk {i}: Gap found starting at {gap_start.date()}")
                    gaps_to_fetch.append((gap_start, chunk_end))
                    chunks_with_gaps += 1
                else:
                    logger.info(f"Chunk {i}: No gap found despite mismatch - Skipping")
                    chunks_skipped += 1

        # Calculate API calls used for gap detection
        detection_calls = len(self.request_timestamps) - initial_request_count

        # Log summary of chunk processing
        logger.info("\nChunk Processing Summary:")
        logger.info(f"  Total chunks: {len(chunks)}")
        logger.info(f"  Chunks skipped (match): {chunks_skipped}")
        logger.info(f"  Chunks with gaps: {chunks_with_gaps}")
        logger.info(f"  Gaps to fetch: {len(gaps_to_fetch)}")

        # No gaps found - database is up to date
        if not gaps_to_fetch:
            logger.info("No data gaps found! Database is completely up to date.")

            stats = {
                "gap_found": False,
                "gap_start_date": None,
                "gap_days": 0,
                "cves_fetched": 0,
                "chunks_total": len(chunks),
                "chunks_skipped": chunks_skipped,
                "chunks_with_gaps": 0,
                "api_calls_for_detection": detection_calls,
                "api_calls_for_fetch": 0,
                "total_api_calls": detection_calls,
                "time_saved_estimate": f"{total_days * 2} seconds ({total_days * 2 / 60:.1f} minutes)",
            }
            return stats

        # Fetch all identified gaps
        logger.info(f"\nFetching {len(gaps_to_fetch)} gap(s)...")
        all_fetched_cves = []
        fetch_start_count = len(self.request_timestamps)

        for gap_start, gap_end in gaps_to_fetch:
            gap_days = (gap_end - gap_start).days
            logger.info(f"Fetching gap: {gap_start.date()} to {gap_end.date()} ({gap_days} days)")

            gap_cves = self.fetch_recent_cves(
                days=gap_days,
                results_per_page=results_per_page,
                max_results=max_results,
            )
            all_fetched_cves.extend(gap_cves)

        fetch_calls = len(self.request_timestamps) - fetch_start_count

        # Calculate statistics
        first_gap_start = gaps_to_fetch[0][0] if gaps_to_fetch else None
        total_gap_days = sum((end - start).days for start, end in gaps_to_fetch)
        days_skipped = total_days - total_gap_days

        stats = {
            "gap_found": True,
            "gap_start_date": first_gap_start,
            "gap_days": total_gap_days,
            "cves_fetched": len(all_fetched_cves),
            "chunks_total": len(chunks),
            "chunks_skipped": chunks_skipped,
            "chunks_with_gaps": chunks_with_gaps,
            "api_calls_for_detection": detection_calls,
            "api_calls_for_fetch": fetch_calls,
            "total_api_calls": detection_calls + fetch_calls,
            "time_saved_estimate": f"{days_skipped * 2} seconds ({days_skipped * 2 / 60:.1f} minutes)",
        }

        logger.info("\nSmart sync complete!")
        logger.info(f"  CVEs fetched: {stats['cves_fetched']}")
        logger.info(f"  API calls (detection): {stats['api_calls_for_detection']}")
        logger.info(f"  API calls (fetch): {stats['api_calls_for_fetch']}")
        logger.info(f"  Total API calls: {stats['total_api_calls']}")
        logger.info(f"  Time saved: {stats['time_saved_estimate']}")

        return stats

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

        # NVD API has a 120-day maximum range limit
        # Split into chunks if needed
        max_chunk_days = 120
        if days <= max_chunk_days:
            return self.fetch_cves_by_date_range(
                start_date=start_date,
                end_date=end_date,
                results_per_page=results_per_page,
                max_results=max_results,
            )

        # Split into chunks
        all_cves: list[CVEData] = []
        current_start = start_date
        total_fetched = 0

        while current_start < end_date:
            current_end = min(current_start + timedelta(days=max_chunk_days), end_date)

            logger.info(f"Fetching chunk: {current_start.date()} to {current_end.date()}")

            chunk_cves = self.fetch_cves_by_date_range(
                start_date=current_start,
                end_date=current_end,
                results_per_page=results_per_page,
                max_results=max_results - total_fetched if max_results else None,
            )

            all_cves.extend(chunk_cves)
            total_fetched += len(chunk_cves)

            # Check if we've reached max_results
            if max_results and total_fetched >= max_results:
                logger.info(f"Reached maximum results limit: {max_results}")
                break

            current_start = current_end

        return all_cves

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
        skipped_count = 0

        # Query database for existing CVE IDs in this date range
        existing_cve_ids = self._get_existing_cve_ids(start_date, end_date)

        # Format dates for API (ISO 8601 with UTC timezone marker)
        pub_start_date = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        pub_end_date = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        # First, check if all CVEs might already exist
        if existing_cve_ids:
            logger.info(
                f"Checking for new CVEs (already have {len(existing_cve_ids)} CVEs in this date range)..."
            )

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
                    # Skip if CVE already exists in database
                    if cve_data.cve_id in existing_cve_ids:
                        skipped_count += 1
                        continue

                    all_cves.append(cve_data)
                    total_fetched += 1

                    # Check if we've reached max_results
                    if max_results and total_fetched >= max_results:
                        logger.info(f"Reached maximum results limit: {max_results}")
                        return all_cves

            # Log progress periodically (every 1000 CVEs processed)
            total_processed = total_fetched + skipped_count
            if total_processed > 0 and total_processed % 1000 == 0:
                logger.info(
                    f"Progress: {total_processed}/{total_results} CVEs processed "
                    f"({total_fetched} new, {skipped_count} skipped)"
                )

            # Check if there are more results to fetch
            start_index += len(vulnerabilities)
            if start_index >= total_results:
                break

        logger.info(
            f"Successfully fetched {len(all_cves)} new CVEs "
            f"(skipped {skipped_count} existing CVEs)"
        )
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

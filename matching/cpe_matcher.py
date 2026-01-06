"""CPE (Common Platform Enumeration) matching engine.

This module provides functionality to match package names from dependency files
to CPE URIs in the NVD database, enabling CVE lookups for dependencies.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from database.models import CVE
from matching.version_comparator import VersionComparator


@dataclass
class CveMatch:
    """Represents a matched CVE for a dependency."""

    cve_id: str
    severity: str
    cvss_score: float | None
    description: str
    published_date: str
    vendor: str | None
    product: str | None
    affected_version: str | None


class CpeMatcher:
    """Engine for matching package names to CVE data via CPE URIs."""

    # Common package name to vendor/product mappings
    # This helps resolve cases where package names differ from NVD product names
    PACKAGE_NAME_MAPPINGS = {
        # Top 50 npm packages (by downloads and security relevance)
        "lodash": ("lodash", "lodash"),
        "axios": ("axios", "axios"),
        "express": ("expressjs", "express"),
        "react": ("facebook", "react"),
        "react-dom": ("facebook", "react-dom"),
        "vue": ("vuejs", "vue"),
        "angular": ("angular", "angular"),
        "jquery": ("jquery", "jquery"),
        "moment": ("momentjs", "moment"),
        "webpack": ("webpack", "webpack"),
        "node": ("nodejs", "node.js"),
        "typescript": ("microsoft", "typescript"),
        "next": ("vercel", "next.js"),
        "eslint": ("eslint", "eslint"),
        "prettier": ("prettier", "prettier"),
        "babel-core": ("babel", "babel"),
        "mocha": ("mochajs", "mocha"),
        "jest": ("facebook", "jest"),
        "chai": ("chaijs", "chai"),
        "commander": ("tj", "commander.js"),
        "dotenv": ("motdotla", "dotenv"),
        "async": ("caolan", "async"),
        "request": ("request", "request"),
        "node-fetch": ("node-fetch", "node-fetch"),
        "body-parser": ("expressjs", "body-parser"),
        "cors": ("expressjs", "cors"),
        "debug": ("debug-js", "debug"),
        "chalk": ("chalk", "chalk"),
        "uuid": ("uuidjs", "uuid"),
        "yargs": ("yargs", "yargs"),
        "jsonwebtoken": ("auth0", "node-jsonwebtoken"),
        "bcrypt": ("kelektiv", "node.bcrypt.js"),
        "socket.io": ("socketio", "socket.io"),
        "redis": ("redis", "node-redis"),
        "mongoose": ("automattic", "mongoose"),
        "sequelize": ("sequelize", "sequelize"),
        "typeorm": ("typeorm", "typeorm"),
        "passport": ("jaredhanson", "passport"),
        "multer": ("expressjs", "multer"),
        "sharp": ("lovell", "sharp"),
        "ws": ("websockets", "ws"),
        "cheerio": ("cheeriojs", "cheerio"),
        "nodemailer": ("nodemailer", "nodemailer"),
        "handlebars": ("handlebars", "handlebars.js"),
        "ejs": ("ejs", "ejs"),
        "pug": ("pugjs", "pug"),
        "marked": ("markedjs", "marked"),
        "cross-env": ("kentcdodds", "cross-env"),
        "validator": ("validatorjs", "validator.js"),
        "minimist": ("minimist", "minimist"),
        # Top 30 Python packages (by usage and security relevance)
        "django": ("djangoproject", "django"),
        "flask": ("palletsprojects", "flask"),
        "requests": ("python-requests", "requests"),
        "numpy": ("numpy", "numpy"),
        "pillow": ("python", "pillow"),
        "pyyaml": ("pyyaml", "pyyaml"),
        "jinja2": ("palletsprojects", "jinja2"),
        "sqlalchemy": ("sqlalchemy", "sqlalchemy"),
        "celery": ("celeryproject", "celery"),
        "tornado": ("tornadoweb", "tornado"),
        "pandas": ("pandas-dev", "pandas"),
        "scipy": ("scipy", "scipy"),
        "matplotlib": ("matplotlib", "matplotlib"),
        "boto3": ("boto", "boto3"),
        "pytest": ("pytest-dev", "pytest"),
        "click": ("pallets", "click"),
        "cryptography": ("pyca", "cryptography"),
        "pycryptodome": ("legrandin", "pycryptodome"),
        "urllib3": ("urllib3", "urllib3"),
        "certifi": ("certifi", "python-certifi"),
        "setuptools": ("pypa", "setuptools"),
        "pip": ("pypa", "pip"),
        "virtualenv": ("pypa", "virtualenv"),
        "scrapy": ("scrapy", "scrapy"),
        "beautifulsoup4": ("crummy", "beautifulsoup"),
        "lxml": ("lxml", "lxml"),
        # "redis": ("redis", "redis-py"),  # Duplicate key - npm redis at line 69 takes precedence
        "psycopg2": ("psycopg", "psycopg2"),
        "pymongo": ("mongodb", "mongo-python-driver"),
        "paramiko": ("paramiko", "paramiko"),
    }

    def __init__(self, db_session: Session):
        """Initialize the CPE matcher.

        Args:
            db_session: SQLAlchemy database session for querying CVEs
        """
        self.db_session = db_session
        self.version_comparator = VersionComparator()

    def find_cves_for_package(
        self,
        package_name: str,
        version: str,
        ecosystem: str,
        version_constraint: str | None = None,
    ) -> list[CveMatch]:
        """Find CVEs that affect a specific package version.

        Args:
            package_name: Name of the package
            version: Version of the package
            ecosystem: Package ecosystem (npm, pip, etc.)
            version_constraint: Optional version constraint

        Returns:
            List of CveMatch objects for matching CVEs
        """
        # Normalize package name
        package_name = package_name.lower().strip()

        # Try to get vendor/product mapping
        vendor, product = self._get_vendor_product(package_name, ecosystem)

        # Query CVEs from database
        cves = self._query_cves_by_product(product, vendor)

        # Filter CVEs by version
        matching_cves = []
        for cve in cves:
            if self._version_matches_cve(version, cve, ecosystem):
                matching_cves.append(
                    CveMatch(
                        cve_id=cve.cve_id,
                        severity=cve.severity or "Unknown",
                        cvss_score=cve.cvss_score,
                        description=cve.description,
                        published_date=(
                            cve.published_date.isoformat() if cve.published_date else "Unknown"
                        ),
                        vendor=cve.vendor,
                        product=cve.product,
                        affected_version=cve.version,
                    )
                )

        return matching_cves

    def _get_vendor_product(self, package_name: str, ecosystem: str) -> tuple[str, str]:
        """Get vendor and product names for a package.

        Args:
            package_name: Name of the package
            ecosystem: Package ecosystem

        Returns:
            Tuple of (vendor, product)
        """
        # Check if we have a mapping
        if package_name in self.PACKAGE_NAME_MAPPINGS:
            return self.PACKAGE_NAME_MAPPINGS[package_name]

        # For npm packages, try common patterns
        if ecosystem == "npm":
            # Handle scoped packages (@org/package)
            if package_name.startswith("@"):
                parts = package_name[1:].split("/")
                if len(parts) == 2:
                    vendor = parts[0]
                    product = parts[1]
                    return (vendor, product)

        # Default: use package name as both vendor and product
        return (package_name, package_name)

    def _query_cves_by_product(self, product: str, vendor: str | None = None) -> list[CVE]:
        """Query CVEs from database by product and optionally vendor.

        Args:
            product: Product name
            vendor: Optional vendor name

        Returns:
            List of CVE objects
        """
        query = self.db_session.query(CVE)

        # Filter by product (case-insensitive partial match)
        query = query.filter(CVE.product.ilike(f"%{product}%"))

        # Optionally filter by vendor
        if vendor:
            query = query.filter(CVE.vendor.ilike(f"%{vendor}%"))

        return query.all()

    def _version_matches_cve(self, package_version: str, cve: CVE, ecosystem: str) -> bool:
        """Check if a package version is affected by a CVE.

        Args:
            package_version: Version to check
            cve: CVE object from database
            ecosystem: Package ecosystem

        Returns:
            True if version is affected by this CVE
        """
        # If CVE doesn't specify a version, we can't determine if it matches
        if not cve.version:
            # Conservative approach: assume it might affect this version
            return True

        cve_version = cve.version.strip()

        # Handle version ranges in CVE data
        # Common patterns:
        # - "* " (all versions before X)
        # - "1.2.3" (exact version)
        # - "< 2.0.0" (versions before 2.0.0)

        # Check for exact version match
        if cve_version == package_version:
            return True

        # Check for version range patterns
        if "<" in cve_version or ">" in cve_version:
            try:
                return self.version_comparator.version_satisfies_constraint(
                    package_version, cve_version, ecosystem
                )
            except Exception:
                # If comparison fails, conservatively assume it matches
                return True

        # Check if CVE version is less than or equal to package version
        # (common pattern: CVE affects all versions up to X)
        comparison = self.version_comparator.compare_versions(package_version, cve_version)
        if comparison is not None:
            # If package version <= CVE version, it's likely affected
            return comparison <= 0

        # If we can't determine, conservatively assume it might be affected
        return True

    def get_cpe_uri(self, package_name: str, version: str, ecosystem: str) -> str | None:
        """Generate a CPE URI for a package.

        CPE format: cpe:2.3:a:vendor:product:version:*:*:*:*:*:*:*

        Args:
            package_name: Name of the package
            version: Version of the package
            ecosystem: Package ecosystem

        Returns:
            CPE URI string or None
        """
        vendor, product = self._get_vendor_product(package_name, ecosystem)

        # Clean version for CPE format
        version = version.replace(" ", "_")

        # Construct CPE 2.3 URI
        cpe_uri = f"cpe:2.3:a:{vendor}:{product}:{version}:*:*:*:*:*:*:*"

        return cpe_uri

    def bulk_match_packages(self, packages: list[dict[str, str]]) -> dict[str, list[CveMatch]]:
        """Match multiple packages to CVEs in a single operation.

        Args:
            packages: List of package dicts with 'name', 'version', 'ecosystem' keys

        Returns:
            Dictionary mapping package names to lists of CveMatch objects
        """
        results = {}

        for pkg in packages:
            package_name = pkg.get("name", "")
            version = pkg.get("version", "")
            ecosystem = pkg.get("ecosystem", "")

            if not package_name or not version:
                continue

            matches = self.find_cves_for_package(package_name, version, ecosystem)
            if matches:
                results[package_name] = matches

        return results

    def get_match_confidence(
        self, package_name: str, cve_product: str, cve_vendor: str | None = None
    ) -> float:
        """Calculate confidence score for a package-to-CVE match.

        Args:
            package_name: Name of the package
            cve_product: Product name from CVE
            cve_vendor: Vendor name from CVE

        Returns:
            Confidence score between 0.0 and 1.0
        """
        package_name = package_name.lower()
        cve_product = cve_product.lower() if cve_product else ""

        # Exact match
        if package_name == cve_product:
            return 1.0

        # Partial match
        if package_name in cve_product or cve_product in package_name:
            return 0.8

        # Check known mappings
        if package_name in self.PACKAGE_NAME_MAPPINGS:
            mapped_vendor, mapped_product = self.PACKAGE_NAME_MAPPINGS[package_name]
            if mapped_product.lower() == cve_product:
                return 0.95
            if cve_vendor and mapped_vendor.lower() == cve_vendor.lower():
                return 0.85

        # Fuzzy match (basic Levenshtein-like logic)
        # Count matching characters
        matches = sum(1 for a, b in zip(package_name, cve_product, strict=False) if a == b)
        max_len = max(len(package_name), len(cve_product))
        if max_len > 0:
            ratio = matches / max_len
            return max(0.5, ratio)  # Minimum 0.5 for fuzzy matches

        return 0.3  # Low confidence for no clear match

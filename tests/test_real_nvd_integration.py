"""Integration tests using real NVD database.

These tests are marked as 'integration' and require a real database with NVD data.
They are slower and optional compared to unit tests with mock data.

Run with: pytest -m integration
Skip with: pytest -m "not integration"
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import CVE
from matching.cpe_matcher import CpeMatcher

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def real_db():
    """Connect to real database if it exists."""
    db_path = "cyberintel.db"

    if not os.path.exists(db_path):
        pytest.skip(f"Real database not found at {db_path}")

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


class TestRealNvdDatabase:
    """Test with real NVD data from the database."""

    def test_database_has_cves(self, real_db):
        """Test that the real database contains CVE data."""
        cve_count = real_db.query(CVE).count()
        assert cve_count > 0, "Real database should contain CVE data"

    def test_database_has_vendor_product_data(self, real_db):
        """Test that some CVEs have vendor/product information."""
        cves_with_products = real_db.query(CVE).filter(CVE.product.isnot(None)).limit(10).all()

        # At least some CVEs should have product info
        assert len(cves_with_products) > 0, "Database should have CVEs with product information"

        for cve in cves_with_products:
            print(f"Found: {cve.cve_id} - {cve.vendor}/{cve.product} {cve.version}")

    def test_severity_distribution(self, real_db):
        """Test severity distribution in real database."""
        severities = {}

        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE", None]:
            count = real_db.query(CVE).filter(CVE.severity == severity).count()
            if count > 0:
                severities[severity or "NULL"] = count

        print(f"\nSeverity distribution: {severities}")
        assert len(severities) > 0, "Database should have CVEs with severity data"


class TestRealCveMatching:
    """Test CVE matching with real NVD data."""

    def test_can_query_database(self, real_db):
        """Test basic database queries work."""
        matcher = CpeMatcher(real_db)

        # Try to find any CVE with common package names
        test_packages = [
            ("linux", "5.0.0"),
            ("android", "11.0"),
            ("windows", "10.0"),
            ("chrome", "90.0"),
        ]

        results = {}
        for package, version in test_packages:
            try:
                matches = matcher.find_cves_for_package(package, version, "generic")
                results[package] = len(matches)
                if matches:
                    print(f"\nFound {len(matches)} CVEs for {package}@{version}")
                    for match in matches[:3]:  # Show first 3
                        print(f"  - {match.cve_id}: {match.description[:80]}...")
            except Exception as e:
                print(f"Error querying {package}: {e}")

        print(f"\nMatching results: {results}")

    def test_real_database_metadata(self, real_db):
        """Test and display real database statistics."""
        from sqlalchemy import func

        stats = {}

        # Total CVEs
        stats["total_cves"] = real_db.query(CVE).count()

        # CVEs with vendor/product
        stats["cves_with_vendor"] = real_db.query(CVE).filter(CVE.vendor.isnot(None)).count()
        stats["cves_with_product"] = real_db.query(CVE).filter(CVE.product.isnot(None)).count()
        stats["cves_with_version"] = real_db.query(CVE).filter(CVE.version.isnot(None)).count()

        # Top vendors
        top_vendors = (
            real_db.query(CVE.vendor, func.count(CVE.vendor))
            .filter(CVE.vendor.isnot(None))
            .group_by(CVE.vendor)
            .order_by(func.count(CVE.vendor).desc())
            .limit(5)
            .all()
        )

        print("\n=== Real Database Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")

        print("\nTop 5 vendors:")
        for vendor, count in top_vendors:
            print(f"  {vendor}: {count} CVEs")

        assert stats["total_cves"] > 0, "Database should have CVEs"


class TestRealWorldScenarios:
    """Test real-world scanning scenarios."""

    @pytest.mark.slow
    def test_scan_multiple_packages(self, real_db):
        """Test scanning multiple common packages (slow test)."""
        matcher = CpeMatcher(real_db)

        # Common packages that might have CVEs
        packages = [
            ("npm", "lodash", "4.17.15"),
            ("npm", "axios", "0.21.0"),
            ("pip", "django", "3.1.0"),
            ("pip", "flask", "1.1.0"),
            ("pip", "requests", "2.25.0"),
        ]

        results = []
        for ecosystem, package, version in packages:
            matches = matcher.find_cves_for_package(package, version, ecosystem)
            results.append(
                {
                    "package": f"{package}@{version}",
                    "ecosystem": ecosystem,
                    "cves_found": len(matches),
                    "critical": len([m for m in matches if m.severity == "CRITICAL"]),
                    "high": len([m for m in matches if m.severity == "HIGH"]),
                }
            )

        print("\n=== Real-World Package Scan Results ===")
        for result in results:
            print(f"{result['package']} ({result['ecosystem']}): {result['cves_found']} CVEs")
            print(f"  Critical: {result['critical']}, High: {result['high']}")

        # This test documents results, doesn't assert specific counts
        # since real NVD data changes over time

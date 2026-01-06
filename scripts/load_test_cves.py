#!/usr/bin/env python3
"""Load test CVE data into database for demo purposes."""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db import get_db_session  # noqa: E402
from database.models import CVE  # noqa: E402


def load_test_cves():
    """Load test CVE data from fixtures into database."""

    # Load test CVE data
    test_cves_file = project_root / "tests/fixtures/test_cves.json"

    if not test_cves_file.exists():
        print(f"Error: Test CVE file not found: {test_cves_file}")
        sys.exit(1)

    with open(test_cves_file) as f:
        data = json.load(f)

    test_cves = data.get("test_cves", [])

    print(f"Loading {len(test_cves)} test CVEs into database...")

    with get_db_session() as session:
        # Check how many CVEs already exist
        existing_count = session.query(CVE).count()
        print(f"Existing CVEs in database: {existing_count}")

        added_count = 0
        skipped_count = 0

        for cve_data in test_cves:
            cve_id = cve_data["cve_id"]

            # Check if CVE already exists
            existing = session.query(CVE).filter(CVE.cve_id == cve_id).first()

            if existing:
                print(f"  Skipping {cve_id} (already exists)")
                skipped_count += 1
                continue

            # Create new CVE
            from datetime import datetime

            now = datetime.now()

            cve = CVE(
                cve_id=cve_id,
                description=cve_data.get("description", ""),
                severity=cve_data.get("severity", "MEDIUM"),
                cvss_score=cve_data.get("cvss_score", 5.0),
                published_date=now,
                last_modified=now,
                vendor=cve_data.get("vendor", ""),
                product=cve_data.get("product", ""),
                version=cve_data.get("version", ""),
                references=[f"https://nvd.nist.gov/vuln/detail/{cve_id}"],
                source="TEST",
            )

            session.add(cve)
            print(
                f"  Added {cve_id} - {cve_data.get('severity')} - {cve_data.get('product')} {cve_data.get('version')}"
            )
            added_count += 1

        session.commit()

        print("\nSummary:")
        print(f"  Added: {added_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Total CVEs in database: {session.query(CVE).count()}")
        print("\nTest CVEs loaded successfully!")
        print("\nYou can now upload test files and see vulnerabilities detected.")


if __name__ == "__main__":
    try:
        load_test_cves()
    except Exception as e:
        print(f"Error loading test CVEs: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

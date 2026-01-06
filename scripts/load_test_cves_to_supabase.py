#!/usr/bin/env python3
"""
Load test CVE data directly into Supabase PostgreSQL database.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
project_root = Path(__file__).parent.parent


def load_test_cves_to_supabase():
    """Load test CVE data from fixtures into Supabase database."""

    # Load test CVE data
    test_cves_file = project_root / "tests/fixtures/test_cves.json"

    if not test_cves_file.exists():
        print(f"Error: Test CVE file not found: {test_cves_file}")
        sys.exit(1)

    with open(test_cves_file) as f:
        data = json.load(f)

    test_cves = data.get("test_cves", [])

    print(f"Loading {len(test_cves)} test CVEs into Supabase...")
    print(f"Database: {DATABASE_URL[:50]}...")

    # Connect to Supabase
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Check existing CVEs
    cursor.execute("SELECT COUNT(*) FROM cves WHERE source = 'TEST';")
    existing_count = cursor.fetchone()[0]
    print(f"Existing TEST CVEs in database: {existing_count}")

    added_count = 0
    skipped_count = 0

    for cve_data in test_cves:
        cve_id = cve_data["cve_id"]

        # Check if CVE already exists
        cursor.execute("SELECT cve_id FROM cves WHERE cve_id = %s;", (cve_id,))
        existing = cursor.fetchone()

        if existing:
            print(f"  Skipping {cve_id} (already exists)")
            skipped_count += 1
            continue

        # Insert new CVE
        now = datetime.now()

        insert_query = """
        INSERT INTO cves (
            cve_id, description, severity, cvss_score, cvss_vector,
            published_date, last_modified, vendor, product, version,
            "references", source, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        );
        """

        values = (
            cve_id,
            cve_data.get("description", ""),
            cve_data.get("severity", "MEDIUM"),
            cve_data.get("cvss_score", 5.0),
            cve_data.get("cvss_vector", ""),
            now,
            now,
            cve_data.get("vendor", ""),
            cve_data.get("product", ""),
            cve_data.get("version"),
            json.dumps([f"https://nvd.nist.gov/vuln/detail/{cve_id}"]),
            "TEST",
            now,
            now,
        )

        try:
            cursor.execute(insert_query, values)
            conn.commit()  # Commit each CVE individually
            print(
                f"  Added {cve_id} - {cve_data.get('severity')} - "
                f"{cve_data.get('product')} {cve_data.get('version')}"
            )
            added_count += 1
        except Exception as e:
            print(f"  Error adding {cve_id}: {e}")
            conn.rollback()
            continue

    # Commit all changes
    conn.commit()

    # Final count
    cursor.execute("SELECT COUNT(*) FROM cves WHERE source = 'TEST';")
    final_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    print("\nSummary:")
    print(f"  Added: {added_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total TEST CVEs in database: {final_count}")
    print("\nTest CVEs loaded successfully into Supabase!")


if __name__ == "__main__":
    try:
        load_test_cves_to_supabase()
    except Exception as e:
        print(f"Error loading test CVEs: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

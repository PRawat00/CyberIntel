#!/usr/bin/env python3
"""
Generate a sample requirements.txt file based on CVEs in Supabase database.
This script queries the live Supabase database and creates a test file with
a mix of vulnerable and safe packages.
"""

import os
import sys
from datetime import datetime

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def connect_to_db():
    """Connect to Supabase PostgreSQL database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)


def fetch_pip_cves(conn) -> list[dict]:
    """Fetch all CVEs for pip/Python packages"""
    cursor = conn.cursor()

    # Query for pip ecosystem CVEs - get all non-npm test CVEs with versions
    query = """
    SELECT
        vendor,
        product,
        version,
        severity,
        cvss_score,
        cve_id,
        description
    FROM cves
    WHERE
        source = 'TEST'
        AND product NOT IN ('lodash', 'axios', 'express', 'moment', 'react', 'webpack',
                            'typescript', 'babel-core')  -- Exclude npm packages
        AND version IS NOT NULL
    ORDER BY
        CASE severity
            WHEN 'CRITICAL' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            WHEN 'LOW' THEN 4
            ELSE 5
        END,
        cvss_score DESC NULLS LAST,
        product,
        version;
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    cves = []
    for row in rows:
        cves.append(
            {
                "vendor": row[0],
                "product": row[1],
                "version": row[2],
                "severity": row[3],
                "cvss_score": row[4],
                "cve_id": row[5],
                "description": row[6][:100] if row[6] else "",  # Truncate description
            }
        )

    cursor.close()
    return cves


def generate_requirements_file(cves: list[dict], output_path: str):
    """Generate a requirements.txt file with vulnerable and safe packages"""

    # Group CVEs by product
    vulnerable_packages = {}
    for cve in cves:
        product = cve["product"]
        if product not in vulnerable_packages:
            vulnerable_packages[product] = []
        vulnerable_packages[product].append(cve)

    # Safe packages (common Python packages with known safe versions)
    safe_packages = [
        "certifi==2024.8.30",
        "charset-normalizer==3.3.2",
        "idna==3.10",
        "python-dotenv==1.0.1",
        "click==8.1.7",
        "colorama==0.4.6",
        "markdown==3.7",
        "pygments==2.18.0",
    ]

    # Generate file content
    lines = []
    lines.append("# Sample Requirements File Generated from Supabase CVE Data")
    lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"# Total CVEs found: {len(cves)}")
    lines.append(f"# Vulnerable packages: {len(vulnerable_packages)}")
    lines.append("")
    lines.append("# ========================================")
    lines.append("# VULNERABLE PACKAGES (Should trigger CVE matches)")
    lines.append("# ========================================")
    lines.append("")

    # Add vulnerable packages
    for product, product_cves in sorted(vulnerable_packages.items())[
        :10
    ]:  # Limit to 10 for readability
        # Get the highest severity CVE for this product
        highest_cve = max(product_cves, key=lambda x: x["cvss_score"] if x["cvss_score"] else 0)

        severity = highest_cve["severity"] or "UNKNOWN"
        cvss = highest_cve["cvss_score"] or "N/A"
        cve_id = highest_cve["cve_id"]
        version = highest_cve["version"]

        lines.append(f"# {product} - {severity} (CVSS: {cvss}) - {cve_id}")
        lines.append(f"{product}=={version}")
        lines.append("")

    lines.append("# ========================================")
    lines.append("# SAFE PACKAGES (Should NOT trigger CVE matches)")
    lines.append("# ========================================")
    lines.append("")

    # Add safe packages
    for pkg in safe_packages:
        lines.append(pkg)

    lines.append("")
    lines.append("# ========================================")
    lines.append("# DEVELOPMENT DEPENDENCIES")
    lines.append("# ========================================")
    lines.append("")
    lines.append("pytest==8.3.3")
    lines.append("pytest-cov==6.0.0")
    lines.append("black==24.10.0")

    # Write to file
    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return len(vulnerable_packages), len(safe_packages)


def main():
    print("Connecting to Supabase database...")
    conn = connect_to_db()

    print("Fetching CVE data for pip/Python packages...")
    cves = fetch_pip_cves(conn)

    if not cves:
        print("WARNING: No CVEs found in database for pip/Python packages!")
        print("The generated file will only contain safe packages.")
    else:
        print(f"Found {len(cves)} CVE records")

    # Create output directory if it doesn't exist
    os.makedirs("test_samples", exist_ok=True)

    output_path = "test_samples/supabase-sample-requirements.txt"
    print(f"\nGenerating requirements file: {output_path}")

    vulnerable_count, safe_count = generate_requirements_file(cves, output_path)

    conn.close()

    print("\n✓ Sample requirements file created successfully!")
    print(f"  - Vulnerable packages: {vulnerable_count}")
    print(f"  - Safe packages: {safe_count}")
    print(f"  - Location: {output_path}")
    print("\nYou can now test this file with:")
    print("  curl -X POST http://localhost:5000/scans \\")
    print(f"       -F 'file=@{output_path}'")


if __name__ == "__main__":
    main()

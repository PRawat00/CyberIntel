"""Pytest configuration and shared fixtures."""

import json
import tempfile

# Fix torch import issue with pytest
# This must happen before any torch-dependent imports
import warnings
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import CVE, Base

warnings.filterwarnings("ignore", message=".*torch.*docstring.*")


@pytest.fixture(scope="session", autouse=True)
def setup_torch_environment():
    """Setup environment for torch-based tests."""
    # Suppress torch warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="torch")
    yield


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_package_json():
    """Sample package.json content."""
    return {
        "name": "test-app",
        "version": "1.0.0",
        "dependencies": {"lodash": "^4.17.0", "axios": ">=0.21.0", "express": "4.17.1"},
        "devDependencies": {"jest": "~26.0.0"},
    }


@pytest.fixture
def sample_requirements_txt():
    """Sample requirements.txt content."""
    return """# Test requirements
django==3.1.0
flask>=1.1.0
requests~=2.25.0
# Comment line
numpy==1.19.5
"""


@pytest.fixture
def test_db():
    """Create an in-memory test database with sample CVE data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Add sample CVE data
    sample_cves = [
        CVE(
            cve_id="CVE-2021-1234",
            description="Test vulnerability in lodash",
            published_date=datetime(2021, 1, 1),
            last_modified=datetime(2021, 1, 1),
            severity="High",
            cvss_score=7.5,
            vendor="lodash",
            product="lodash",
            version="4.17.15",
            source="NVD",
        ),
        CVE(
            cve_id="CVE-2021-5678",
            description="Test vulnerability in axios",
            published_date=datetime(2021, 2, 1),
            last_modified=datetime(2021, 2, 1),
            severity="Critical",
            cvss_score=9.8,
            vendor="axios",
            product="axios",
            version="0.21.0",
            source="NVD",
        ),
    ]

    for cve in sample_cves:
        session.add(cve)
    session.commit()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def package_json_file(temp_dir, sample_package_json):
    """Create a temporary package.json file."""
    file_path = temp_dir / "package.json"
    with open(file_path, "w") as f:
        json.dump(sample_package_json, f)
    return file_path


@pytest.fixture
def requirements_txt_file(temp_dir, sample_requirements_txt):
    """Create a temporary requirements.txt file."""
    file_path = temp_dir / "requirements.txt"
    with open(file_path, "w") as f:
        f.write(sample_requirements_txt)
    return file_path


@pytest.fixture
def mock_cve_data():
    """Mock CVE data for testing."""
    return {
        "cve_id": "CVE-2025-12345",
        "severity": "CRITICAL",
        "cvss_score": 9.8,
        "description": "Remote code execution vulnerability",
        "published_date": "2025-01-15T10:00:00",
        "product": "lodash",
        "version": "4.17.15",
    }


@pytest.fixture
def mock_nvd_response():
    """Mock NVD API response."""
    return {
        "resultsPerPage": 1,
        "startIndex": 0,
        "totalResults": 1,
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2025-12345",
                    "descriptions": [
                        {"lang": "en", "value": "Remote code execution vulnerability"}
                    ],
                    "metrics": {
                        "cvssMetricV31": [
                            {"cvssData": {"baseScore": 9.8, "baseSeverity": "CRITICAL"}}
                        ]
                    },
                }
            }
        ],
    }


@pytest.fixture
def comprehensive_test_db():
    """Create an in-memory test database with comprehensive CVE coverage.

    Loads CVE data from tests/fixtures/test_cves.json to provide extensive
    test coverage for CPE matching, version comparison, and edge cases.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Load test CVEs from JSON fixture
    fixtures_dir = Path(__file__).parent / "fixtures"
    test_cves_file = fixtures_dir / "test_cves.json"

    if test_cves_file.exists():
        with open(test_cves_file) as f:
            test_data = json.load(f)

        for cve_data in test_data["test_cves"]:
            cve = CVE(
                cve_id=cve_data["cve_id"],
                vendor=cve_data["vendor"],
                product=cve_data["product"],
                version=cve_data.get("version"),
                severity=cve_data["severity"],
                cvss_score=cve_data["cvss_score"],
                description=cve_data["description"],
                published_date=datetime(2021, 1, 1),
                last_modified=datetime(2021, 1, 1),
                source="TEST",
            )
            session.add(cve)

        session.commit()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def load_test_cves_data():
    """Load test CVE data from JSON file for inspection."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    test_cves_file = fixtures_dir / "test_cves.json"

    if test_cves_file.exists():
        with open(test_cves_file) as f:
            return json.load(f)
    return {"test_cves": []}

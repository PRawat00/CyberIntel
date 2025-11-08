"""End-to-end tests for the dependency scanner."""

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from database.models import Base, Dependency, Scan
from scripts.scan_dependencies import DependencyScanner


@pytest.fixture
def test_db_path():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Initialize database
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


class TestDependencyScanner:
    """Tests for DependencyScanner end-to-end functionality."""

    def test_scan_package_json(self, package_json_file, test_db_path):
        """Test scanning a package.json file end-to-end."""
        scanner = DependencyScanner(db_path=test_db_path)
        results = scanner.scan_file(package_json_file, verbose=False)

        # Verify results structure
        assert results["file_name"] == "package.json"
        assert results["file_type"] == "npm"
        assert results["total_dependencies"] == 4
        assert results["scan_id"] is not None

        # Verify database persistence
        session = scanner.Session()
        try:
            scan = session.query(Scan).filter_by(id=results["scan_id"]).first()
            assert scan is not None
            assert scan.file_name == "package.json"
            assert scan.total_dependencies == 4

            # Check dependencies were stored
            deps = session.query(Dependency).filter_by(scan_id=scan.id).all()
            assert len(deps) == 4

            dep_names = [d.package_name for d in deps]
            assert "lodash" in dep_names
            assert "axios" in dep_names
            assert "express" in dep_names
            assert "jest" in dep_names
        finally:
            session.close()

    def test_scan_requirements_txt(self, requirements_txt_file, test_db_path):
        """Test scanning a requirements.txt file end-to-end."""
        scanner = DependencyScanner(db_path=test_db_path)
        results = scanner.scan_file(requirements_txt_file, verbose=False)

        # Verify results structure
        assert results["file_name"] == "requirements.txt"
        assert results["file_type"] == "pip"
        assert results["total_dependencies"] == 4
        assert results["scan_id"] is not None

        # Verify database persistence
        session = scanner.Session()
        try:
            scan = session.query(Scan).filter_by(id=results["scan_id"]).first()
            assert scan is not None
            assert scan.file_name == "requirements.txt"
            assert scan.total_dependencies == 4

            deps = session.query(Dependency).filter_by(scan_id=scan.id).all()
            assert len(deps) == 4
        finally:
            session.close()

    def test_detect_file_type(self, test_db_path):
        """Test automatic file type detection."""
        scanner = DependencyScanner(db_path=test_db_path)

        assert scanner.detect_file_type(Path("package.json")) == "npm"
        assert scanner.detect_file_type(Path("requirements.txt")) == "pip"
        assert scanner.detect_file_type(Path("requirements-dev.txt")) == "pip"

    def test_unsupported_file_type(self, test_db_path):
        """Test handling of unsupported file types."""
        scanner = DependencyScanner(db_path=test_db_path)

        with pytest.raises(ValueError, match="Unsupported file type"):
            scanner.detect_file_type(Path("Cargo.toml"))

    def test_missing_file(self, test_db_path):
        """Test handling of missing files."""
        scanner = DependencyScanner(db_path=test_db_path)

        with pytest.raises(FileNotFoundError):
            scanner.scan_file(Path("/nonexistent/file.json"))

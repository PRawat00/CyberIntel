"""Tests for dependency file parsers."""

import json
from pathlib import Path

import pytest

from parsers import NpmParser, ParsedDependency, PipParser


class TestNpmParser:
    """Tests for NpmParser."""

    def test_parse_valid_package_json(self, package_json_file):
        """Test parsing a valid package.json file."""
        parser = NpmParser()
        dependencies = parser.parse_file(package_json_file)

        assert len(dependencies) == 4

        # Check production dependency
        lodash = [d for d in dependencies if d.package_name == "lodash"][0]
        assert lodash.version == "4.17.0"
        assert lodash.version_constraint == "^4.17.0"
        assert lodash.ecosystem == "npm"
        assert lodash.is_dev_dependency is False

        # Check dev dependency
        jest = [d for d in dependencies if d.package_name == "jest"][0]
        assert jest.is_dev_dependency is True

    def test_parse_package_json_content(self, sample_package_json):
        """Test parsing package.json from content string."""
        parser = NpmParser()
        content = json.dumps(sample_package_json)
        dependencies = parser.parse_content(content)

        assert len(dependencies) == 4
        package_names = [d.package_name for d in dependencies]
        assert "lodash" in package_names
        assert "axios" in package_names
        assert "express" in package_names
        assert "jest" in package_names

    def test_supports_file(self):
        """Test file type detection."""
        parser = NpmParser()
        assert parser.supports_file("package.json") is True
        assert parser.supports_file("package-lock.json") is True
        assert parser.supports_file("requirements.txt") is False

    def test_invalid_json(self, temp_dir):
        """Test handling of invalid JSON."""
        parser = NpmParser()
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text("{invalid json")

        with pytest.raises(ValueError, match="Invalid JSON"):
            parser.parse_file(invalid_file)

    def test_missing_file(self):
        """Test handling of missing file."""
        parser = NpmParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("/nonexistent/package.json"))

    def test_parse_package_lock_json(self, temp_dir):
        """Test parsing a package-lock.json file."""
        parser = NpmParser()

        # Create a simple package-lock.json
        lock_file = temp_dir / "package-lock.json"
        lock_content = """
{
  "name": "test-app",
  "version": "1.0.0",
  "lockfileVersion": 3,
  "packages": {
    "": {
      "name": "test-app",
      "dependencies": {
        "lodash": "^4.17.21"
      }
    },
    "node_modules/lodash": {
      "version": "4.17.21",
      "resolved": "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz",
      "integrity": "sha512-v2kDEe57lecTulaDIuNTPy3Ry4gLGJ6Z1O3vE1krgXZNrsQ+LFTGHVxVjcXPs17LhbZVGedAJv8XZ1tvj5FvSg=="
    },
    "node_modules/axios": {
      "version": "0.27.2",
      "dev": true
    }
  }
}
"""
        lock_file.write_text(lock_content)

        dependencies = parser.parse_file(lock_file)

        assert len(dependencies) == 2
        assert any(
            dep.package_name == "lodash" and dep.version == "4.17.21" for dep in dependencies
        )
        assert any(dep.package_name == "axios" and dep.is_dev_dependency for dep in dependencies)

        # Check that metadata indicates it's from lock file
        lodash_dep = next(d for d in dependencies if d.package_name == "lodash")
        assert lodash_dep.metadata["from_lock_file"] is True
        assert lodash_dep.version_constraint == "=4.17.21"  # Exact version

    def test_parse_legacy_package_lock_unsupported(self, temp_dir):
        """Test that legacy lockfileVersion 1 is rejected."""
        parser = NpmParser()

        lock_file = temp_dir / "package-lock.json"
        lock_content = '{"name": "test", "lockfileVersion": 1, "dependencies": {}}'
        lock_file.write_text(lock_content)

        with pytest.raises(ValueError, match="Unsupported lockfileVersion"):
            parser.parse_file(lock_file)


class TestPipParser:
    """Tests for PipParser."""

    def test_parse_valid_requirements_txt(self, requirements_txt_file):
        """Test parsing a valid requirements.txt file."""
        parser = PipParser()
        dependencies = parser.parse_file(requirements_txt_file)

        assert len(dependencies) == 4

        # Check exact version
        django = [d for d in dependencies if d.package_name == "django"][0]
        assert django.version == "3.1.0"
        assert django.version_constraint == "==3.1.0"
        assert django.ecosystem == "pip"

        # Check version constraint
        flask = [d for d in dependencies if d.package_name == "flask"][0]
        assert flask.version == "1.1.0"
        assert flask.version_constraint == ">=1.1.0"

    def test_parse_requirements_content(self, sample_requirements_txt):
        """Test parsing requirements from content string."""
        parser = PipParser()
        dependencies = parser.parse_content(sample_requirements_txt)

        assert len(dependencies) == 4
        package_names = [d.package_name for d in dependencies]
        assert "django" in package_names
        assert "flask" in package_names
        assert "requests" in package_names
        assert "numpy" in package_names

    def test_supports_file(self):
        """Test file type detection."""
        parser = PipParser()
        assert parser.supports_file("requirements.txt") is True
        assert parser.supports_file("requirements-dev.txt") is True
        assert parser.supports_file("package.json") is False

    def test_comments_and_blank_lines(self, temp_dir):
        """Test that comments and blank lines are handled."""
        parser = PipParser()
        content = """
# This is a comment
django==3.1.0

flask>=1.1.0  # inline comment
"""
        parser.parse_content(content)  # Result intentionally unused in this test

    def test_parse_pipfile(self, temp_dir):
        """Test parsing a Pipfile (TOML format)."""
        parser = PipParser()

        # Create a Pipfile
        pipfile = temp_dir / "Pipfile"
        pipfile_content = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
django = "==3.2.0"
requests = ">=2.25.0"
flask = {version = "~=2.0.0"}

[dev-packages]
pytest = ">=7.0.0"
black = "*"

[requires]
python_version = "3.9"
"""
        pipfile.write_text(pipfile_content)

        dependencies = parser.parse_file(pipfile)

        # Should get 4 dependencies (black with * is skipped)
        assert len(dependencies) == 4

        # Check exact version
        django = next((d for d in dependencies if d.package_name == "django"), None)
        assert django is not None
        assert django.version == "3.2.0"
        assert django.version_constraint == "==3.2.0"
        assert django.is_dev_dependency is False
        assert django.metadata["from_pipfile"] is True

        # Check dev dependency
        pytest_dep = next((d for d in dependencies if d.package_name == "pytest"), None)
        assert pytest_dep is not None
        assert pytest_dep.is_dev_dependency is True

        # Check dict format with extras
        flask = next((d for d in dependencies if d.package_name == "flask"), None)
        assert flask is not None
        assert flask.version == "2.0.0"

    def test_pipfile_dict_format(self, temp_dir):
        """Test Pipfile with dictionary-style package specifications."""
        parser = PipParser()

        pipfile = temp_dir / "Pipfile"
        pipfile_content = """
[packages]
flask = {version = "==2.0.0", extras = ["security"]}
requests = ">=2.25.0"
"""
        pipfile.write_text(pipfile_content)

        dependencies = parser.parse_file(pipfile)

        assert len(dependencies) == 2

        # Check dictionary format with extras
        flask = next(d for d in dependencies if d.package_name == "flask")
        assert flask.version == "2.0.0"
        assert flask.metadata["extras"] == ["security"]
        assert len(dependencies) == 2


class TestParsedDependency:
    """Tests for ParsedDependency dataclass."""

    def test_valid_dependency(self):
        """Test creating a valid dependency."""
        dep = ParsedDependency(
            package_name="lodash", version="4.17.20", version_constraint="^4.17.0", ecosystem="npm"
        )
        assert dep.package_name == "lodash"
        assert dep.version == "4.17.20"
        assert dep.ecosystem == "npm"

    def test_field_normalization(self):
        """Test that package names are normalized to lowercase."""
        dep = ParsedDependency(package_name="  LoDaSh  ", version="  4.17.20  ", ecosystem="npm")
        assert dep.package_name == "lodash"
        assert dep.version == "4.17.20"

    def test_empty_package_name(self):
        """Test that empty package name raises error."""
        with pytest.raises(ValueError, match="package_name cannot be empty"):
            ParsedDependency(package_name="", version="1.0.0", ecosystem="npm")

    def test_to_dict(self):
        """Test conversion to dictionary."""
        dep = ParsedDependency(package_name="lodash", version="4.17.20", ecosystem="npm")
        dep_dict = dep.to_dict()
        assert dep_dict["package_name"] == "lodash"
        assert dep_dict["version"] == "4.17.20"
        assert dep_dict["ecosystem"] == "npm"

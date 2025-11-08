"""Tests for version comparison functionality."""

import pytest

from matching import VersionComparator


class TestVersionComparator:
    """Tests for VersionComparator."""

    def test_parse_version_valid(self):
        """Test parsing valid version strings."""
        vc = VersionComparator()
        assert vc.parse_version("1.2.3") is not None
        assert vc.parse_version("2.0.0") is not None
        assert vc.parse_version("v1.2.3") is not None  # Leading 'v'
        assert vc.parse_version("1.2.3-beta.1") is not None  # Pre-release

    def test_compare_versions(self):
        """Test version comparison."""
        vc = VersionComparator()
        assert vc.compare_versions("1.2.3", "2.0.0") == -1  # Less than
        assert vc.compare_versions("2.0.0", "1.2.3") == 1  # Greater than
        assert vc.compare_versions("1.2.3", "1.2.3") == 0  # Equal

    @pytest.mark.parametrize(
        "version,constraint,expected",
        [
            # NPM caret (^) - compatible with same major version
            ("1.2.5", "^1.2.3", True),  # Patch update OK
            ("1.5.0", "^1.2.3", True),  # Minor update OK
            ("2.0.0", "^1.2.3", False),  # Major update NOT OK
            # NPM tilde (~) - compatible with same minor version
            ("1.2.5", "~1.2.3", True),  # Patch update OK
            ("1.3.0", "~1.2.3", False),  # Minor update NOT OK
            # Comparison operators
            ("1.5.0", ">=1.0.0", True),
            ("0.9.0", ">=1.0.0", False),
            ("1.9.0", "<2.0.0", True),
            ("2.0.0", "<2.0.0", False),
        ],
    )
    def test_npm_version_constraints(self, version, constraint, expected):
        """Test NPM-style version constraints."""
        vc = VersionComparator()
        result = vc.version_satisfies_constraint(version, constraint, ecosystem="npm")
        assert result == expected

    @pytest.mark.parametrize(
        "version,constraint,expected",
        [
            # PIP exact match
            ("1.2.3", "==1.2.3", True),
            ("1.2.4", "==1.2.3", False),
            # PIP compatible release (~=)
            ("1.2.5", "~=1.2.3", True),  # Same major.minor OK
            ("1.3.0", "~=1.2.3", False),  # Different minor NOT OK
            # PIP comparison operators
            ("2.0.0", ">=1.5.0", True),
            ("1.0.0", ">=1.5.0", False),
        ],
    )
    def test_pip_version_constraints(self, version, constraint, expected):
        """Test PIP-style version constraints."""
        vc = VersionComparator()
        result = vc.version_satisfies_constraint(version, constraint, ecosystem="pip")
        assert result == expected

    def test_version_in_range(self):
        """Test checking if version is within a range."""
        vc = VersionComparator()

        # Within range
        assert vc.is_version_in_range("1.5.0", "1.0.0", "2.0.0") is True

        # Below range
        assert vc.is_version_in_range("0.5.0", "1.0.0", "2.0.0") is False

        # Above range (max is exclusive)
        assert vc.is_version_in_range("2.0.0", "1.0.0", "2.0.0") is False

        # No lower bound
        assert vc.is_version_in_range("0.5.0", None, "2.0.0") is True

        # No upper bound
        assert vc.is_version_in_range("5.0.0", "1.0.0", None) is True

    def test_invalid_version(self):
        """Test handling of invalid version strings."""
        vc = VersionComparator()
        assert vc.parse_version("not-a-version") is None
        assert vc.parse_version("") is None
        assert vc.compare_versions("1.2.3", "invalid") is None

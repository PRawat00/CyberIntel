"""Version comparison utilities for dependency matching.

This module provides version comparison functionality to determine if a
specific package version falls within a vulnerable version range specified
in CVE data.
"""

import re

from packaging import version as packaging_version
from packaging.version import InvalidVersion, Version


class VersionComparator:
    """Utility class for comparing and evaluating version constraints."""

    @staticmethod
    def parse_version(version_str: str) -> Version | None:
        """Parse a version string into a Version object.

        Args:
            version_str: Version string (e.g., "1.2.3", "2.0.0-beta.1")

        Returns:
            Version object or None if parsing fails
        """
        try:
            # Clean version string
            version_str = version_str.strip()
            # Remove leading 'v' if present
            if version_str.lower().startswith("v"):
                version_str = version_str[1:]
            return packaging_version.parse(version_str)
        except (InvalidVersion, AttributeError, TypeError):
            return None

    @staticmethod
    def compare_versions(version1: str, version2: str) -> int | None:
        """Compare two version strings.

        Args:
            version1: First version string
            version2: Second version string

        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
             None if comparison fails
        """
        v1 = VersionComparator.parse_version(version1)
        v2 = VersionComparator.parse_version(version2)

        if v1 is None or v2 is None:
            return None

        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0

    @staticmethod
    def version_satisfies_constraint(version: str, constraint: str, ecosystem: str = "npm") -> bool:
        """Check if a version satisfies a version constraint.

        Args:
            version: Version to check (e.g., "1.2.3")
            constraint: Version constraint (e.g., ">=1.0.0", "^1.2.0")
            ecosystem: Package ecosystem (npm, pip, go, etc.)

        Returns:
            True if version satisfies constraint, False otherwise

        Examples:
            version_satisfies_constraint("1.2.3", ">=1.0.0") -> True
            version_satisfies_constraint("1.2.3", "^1.0.0") -> True
            version_satisfies_constraint("2.0.0", "^1.0.0") -> False
        """
        v = VersionComparator.parse_version(version)
        if v is None:
            return False

        # Handle npm-style constraints
        if ecosystem == "npm":
            return VersionComparator._check_npm_constraint(v, constraint)
        # Handle pip-style constraints
        elif ecosystem == "pip":
            return VersionComparator._check_pip_constraint(v, constraint)
        else:
            # Generic constraint checking
            return VersionComparator._check_generic_constraint(v, constraint)

    @staticmethod
    def _check_npm_constraint(v: Version, constraint: str) -> bool:
        """Check if version satisfies npm-style constraint.

        Supports:
        - Exact: "1.2.3", "=1.2.3"
        - Caret: "^1.2.3" (compatible with 1.x.x, not 2.x.x)
        - Tilde: "~1.2.3" (compatible with 1.2.x, not 1.3.x)
        - Ranges: ">=1.0.0 <2.0.0", ">=1.0.0", "<2.0.0"
        - Wildcards: "1.x", "1.2.x", "*"

        Args:
            v: Parsed version
            constraint: npm-style constraint

        Returns:
            True if version satisfies constraint
        """
        constraint = constraint.strip()

        # Handle wildcard
        if constraint == "*":
            return True

        # Handle caret (^) - allows changes that do not modify left-most non-zero digit
        if constraint.startswith("^"):
            base_version = constraint[1:].strip()
            base = VersionComparator.parse_version(base_version)
            if base is None:
                return False

            # ^1.2.3 means >=1.2.3 <2.0.0
            # ^0.2.3 means >=0.2.3 <0.3.0
            # ^0.0.3 means >=0.0.3 <0.0.4
            if base.major > 0:
                return v >= base and v.major == base.major
            elif base.minor > 0:
                return v >= base and v.major == base.major and v.minor == base.minor
            else:
                return (
                    v >= base
                    and v.major == base.major
                    and v.minor == base.minor
                    and v.micro == base.micro
                )

        # Handle tilde (~) - allows patch-level changes
        if constraint.startswith("~"):
            base_version = constraint[1:].strip()
            base = VersionComparator.parse_version(base_version)
            if base is None:
                return False

            # ~1.2.3 means >=1.2.3 <1.3.0
            return v >= base and v.major == base.major and v.minor == base.minor

        # Handle x-ranges (1.x, 1.2.x)
        if "x" in constraint.lower():
            return VersionComparator._check_x_range(v, constraint)

        # Handle comparison operators
        return VersionComparator._check_generic_constraint(v, constraint)

    @staticmethod
    def _check_pip_constraint(v: Version, constraint: str) -> bool:
        """Check if version satisfies pip-style constraint.

        Supports:
        - Exact: "==1.2.3"
        - Ranges: ">=1.0.0", "<=2.0.0", ">1.0.0", "<2.0.0"
        - Compatible: "~=1.2.3" (equivalent to >=1.2.3, ==1.2.*)
        - Not equal: "!=1.2.3"

        Args:
            v: Parsed version
            constraint: pip-style constraint

        Returns:
            True if version satisfies constraint
        """
        constraint = constraint.strip()

        # Handle compatible release (~=)
        if constraint.startswith("~="):
            base_version = constraint[2:].strip()
            base = VersionComparator.parse_version(base_version)
            if base is None:
                return False

            # ~=1.2.3 means >=1.2.3, ==1.2.*
            return v >= base and v.major == base.major and v.minor == base.minor

        # Handle comparison operators
        return VersionComparator._check_generic_constraint(v, constraint)

    @staticmethod
    def _check_generic_constraint(v: Version, constraint: str) -> bool:
        """Check if version satisfies generic constraint with operators.

        Args:
            v: Parsed version
            constraint: Constraint with operators (>=, <=, >, <, ==, !=)

        Returns:
            True if version satisfies constraint
        """
        # Handle multiple constraints separated by space or comma
        if " " in constraint or "," in constraint:
            # Split on space or comma
            constraints = re.split(r"[,\s]+", constraint)
            # All constraints must be satisfied (AND logic)
            return all(
                VersionComparator._check_single_constraint(v, c.strip())
                for c in constraints
                if c.strip()
            )

        return VersionComparator._check_single_constraint(v, constraint)

    @staticmethod
    def _check_single_constraint(v: Version, constraint: str) -> bool:
        """Check a single constraint with one operator.

        Args:
            v: Parsed version
            constraint: Single constraint (e.g., ">=1.0.0")

        Returns:
            True if version satisfies constraint
        """
        # Extract operator and version
        match = re.match(r"^(>=|<=|>|<|==|=|!=)(.+)$", constraint)

        if match:
            operator = match.group(1)
            version_str = match.group(2).strip()
            constraint_v = VersionComparator.parse_version(version_str)

            if constraint_v is None:
                return False

            if operator == ">=" or operator == "gte":
                return v >= constraint_v
            elif operator == "<=" or operator == "lte":
                return v <= constraint_v
            elif operator == ">" or operator == "gt":
                return v > constraint_v
            elif operator == "<" or operator == "lt":
                return v < constraint_v
            elif operator == "==" or operator == "=" or operator == "eq":
                return v == constraint_v
            elif operator == "!=" or operator == "ne":
                return v != constraint_v

        # No operator - treat as exact match
        constraint_v = VersionComparator.parse_version(constraint)
        if constraint_v is None:
            return False
        return v == constraint_v

    @staticmethod
    def _check_x_range(v: Version, x_range: str) -> bool:
        """Check if version matches an x-range pattern.

        Examples:
            1.x or 1.X -> 1.0.0 <= v < 2.0.0
            1.2.x -> 1.2.0 <= v < 1.3.0

        Args:
            v: Parsed version
            x_range: X-range pattern

        Returns:
            True if version matches pattern
        """
        x_range = x_range.lower().replace("x", "0")
        parts = x_range.split(".")

        if len(parts) >= 1 and parts[0] != "*":
            try:
                major = int(parts[0])
                if v.major != major:
                    return False

                if len(parts) >= 2 and parts[1] != "0":
                    minor = int(parts[1])
                    if v.minor != minor:
                        return False

                return True
            except ValueError:
                return False

        return True

    @staticmethod
    def is_version_in_range(
        version: str, min_version: str | None = None, max_version: str | None = None
    ) -> bool:
        """Check if a version is within a range.

        Args:
            version: Version to check
            min_version: Minimum version (inclusive), None for no lower bound
            max_version: Maximum version (exclusive), None for no upper bound

        Returns:
            True if version is in range

        Examples:
            is_version_in_range("1.5.0", "1.0.0", "2.0.0") -> True
            is_version_in_range("2.5.0", "1.0.0", "2.0.0") -> False
        """
        v = VersionComparator.parse_version(version)
        if v is None:
            return False

        if min_version is not None:
            min_v = VersionComparator.parse_version(min_version)
            if min_v is not None and v < min_v:
                return False

        if max_version is not None:
            max_v = VersionComparator.parse_version(max_version)
            if max_v is not None and v >= max_v:
                return False

        return True

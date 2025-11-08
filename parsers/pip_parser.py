"""Parser for pip requirements files and Python dependencies."""

import re
from pathlib import Path

from parsers.base_parser import BaseParser, ParsedDependency


class PipParser(BaseParser):
    """Parser for pip requirements.txt and similar Python dependency files."""

    def __init__(self):
        """Initialize the pip parser."""
        super().__init__(ecosystem="pip")
        self.supported_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-test.txt",
            "dev-requirements.txt",
            "test-requirements.txt",
            "requirements.in",
            "setup.py",
            "Pipfile",
        ]

    def supports_file(self, file_name: str) -> bool:
        """Check if this parser supports the given file.

        Args:
            file_name: Name of the file

        Returns:
            True if file is a supported Python dependency file
        """
        file_name_lower = file_name.lower()
        return (
            file_name_lower in self.supported_files
            or file_name_lower.startswith("requirements")
            and file_name_lower.endswith(".txt")
        )

    def parse_file(self, file_path: Path) -> list[ParsedDependency]:
        """Parse a pip requirements file and extract dependencies.

        Args:
            file_path: Path to requirements file

        Returns:
            List of ParsedDependency objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        content = self.read_file_content(file_path)
        is_dev = self._is_dev_file(file_path.name)
        return self.parse_content(content, is_dev=is_dev)

    def parse_content(self, content: str, is_dev: bool = False) -> list[ParsedDependency]:
        """Parse requirements.txt content and extract dependencies.

        Args:
            content: String content of requirements file
            is_dev: Whether these are dev dependencies

        Returns:
            List of ParsedDependency objects
        """
        dependencies = []

        for _line_num, line in enumerate(content.split("\n"), start=1):
            # Remove comments
            if "#" in line:
                line = line[: line.index("#")]

            # Strip whitespace
            line = line.strip()

            # Skip empty lines, comments, and pip options
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            # Parse the dependency line
            dep = self._parse_requirement_line(line, is_dev)
            if dep:
                dependencies.append(dep)

        return dependencies

    def _parse_requirement_line(self, line: str, is_dev: bool = False) -> ParsedDependency | None:
        """Parse a single requirement line from requirements.txt.

        Supports various pip requirement formats:
        - package==1.2.3
        - package>=1.2.3
        - package~=1.2.3
        - package!=1.2.3
        - package[extra]==1.2.3
        - git+https://github.com/user/repo.git@v1.2.3#egg=package

        Args:
            line: Single requirement line
            is_dev: Whether this is a dev dependency

        Returns:
            ParsedDependency object or None if line cannot be parsed
        """
        line = line.strip()

        # Handle git/VCS dependencies
        if any(line.startswith(prefix) for prefix in ["git+", "hg+", "svn+", "bzr+"]):
            return self._parse_vcs_requirement(line, is_dev)

        # Handle URL dependencies
        if line.startswith("http://") or line.startswith("https://"):
            return None  # Skip URL dependencies for now

        # Parse standard pip requirement
        # Pattern: package_name[extras]operator version
        # Examples: django==3.2.0, requests>=2.25.0, flask[security]~=2.0.0

        # Remove extras (content in square brackets)
        extras_match = re.search(r"\[([^\]]+)\]", line)
        extras = extras_match.group(1) if extras_match else None
        line_without_extras = re.sub(r"\[[^\]]+\]", "", line)

        # Match package name and version specification
        # Pattern: name (operator version)?
        pattern = r"^([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?)\s*(==|>=|<=|>|<|~=|!=)?\s*([a-zA-Z0-9.*+-]+)?$"
        match = re.match(pattern, line_without_extras)

        if not match:
            return None

        package_name = match.group(1)
        operator = match.group(3)
        version_spec = match.group(4)

        # If no version specified, skip (we need a version for CVE matching)
        if not version_spec or version_spec == "*":
            return None

        # Resolve version and version constraint
        if operator == "==":
            # Exact version
            resolved_version = version_spec
            version_constraint = f"=={version_spec}"
        elif operator in [">=", "<=", ">", "<", "~=", "!="]:
            # Version constraint
            resolved_version = self._resolve_version_from_constraint(version_spec)
            version_constraint = f"{operator}{version_spec}"
        else:
            # No operator, treat as exact version
            resolved_version = version_spec
            version_constraint = f"=={version_spec}"

        if not resolved_version:
            return None

        metadata = {
            "original_line": line,
            "extras": extras,
            "operator": operator,
            "dependency_type": "dev" if is_dev else "prod",
        }

        try:
            return ParsedDependency(
                package_name=package_name,
                version=resolved_version,
                version_constraint=version_constraint,
                ecosystem=self.ecosystem,
                is_dev_dependency=is_dev,
                metadata=metadata,
            )
        except ValueError:
            return None

    def _parse_vcs_requirement(self, line: str, is_dev: bool = False) -> ParsedDependency | None:
        """Parse a VCS (git/hg/svn/bzr) requirement line.

        Example: git+https://github.com/user/repo.git@v1.2.3#egg=package

        Args:
            line: VCS requirement line
            is_dev: Whether this is a dev dependency

        Returns:
            ParsedDependency object or None if cannot be parsed
        """
        # Extract package name from egg parameter
        egg_match = re.search(r"#egg=([a-zA-Z0-9_-]+)", line)
        if not egg_match:
            return None

        package_name = egg_match.group(1)

        # Try to extract version from tag/branch
        # Look for patterns like @v1.2.3, @1.2.3, @release-1.2.3
        version_match = re.search(r"@[^#]*?v?(\d+\.\d+\.\d+)", line)
        if version_match:
            version = version_match.group(1)
        else:
            # No version found in URL, skip
            return None

        metadata = {
            "original_line": line,
            "vcs_url": line,
            "dependency_type": "dev" if is_dev else "prod",
        }

        try:
            return ParsedDependency(
                package_name=package_name,
                version=version,
                version_constraint=None,
                ecosystem=self.ecosystem,
                is_dev_dependency=is_dev,
                metadata=metadata,
            )
        except ValueError:
            return None

    def _resolve_version_from_constraint(self, version_spec: str) -> str | None:
        """Resolve a version from a constraint specification.

        For constraints like ">=1.2.3", we extract "1.2.3" as the base version.

        Args:
            version_spec: Version specification

        Returns:
            Resolved version string or None
        """
        # Extract semantic version pattern
        version_pattern = r"(\d+\.\d+(?:\.\d+)?(?:[-+][a-zA-Z0-9.-]+)?)"
        match = re.search(version_pattern, version_spec)

        if match:
            return match.group(1)

        return None

    def _is_dev_file(self, file_name: str) -> bool:
        """Determine if a file contains dev dependencies.

        Args:
            file_name: Name of the file

        Returns:
            True if file likely contains dev dependencies
        """
        file_name_lower = file_name.lower()
        dev_indicators = ["dev", "test", "testing"]
        return any(indicator in file_name_lower for indicator in dev_indicators)

    def __repr__(self) -> str:
        return f"<PipParser(ecosystem='{self.ecosystem}')>"

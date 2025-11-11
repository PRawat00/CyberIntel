"""Parser for pip requirements files and Python dependencies."""

import re
import sys
from pathlib import Path

# Python 3.11+ has built-in tomllib, earlier versions need tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

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

    def supports_file(self, file_name: str, content: str = None) -> bool:
        """Check if this parser supports the given file.

        Uses intelligent detection: checks filename, extension, and content structure.
        This allows users to upload files with ANY name (e.g., "prod-deps.txt").

        Args:
            file_name: Name of the file
            content: Optional file content for structure validation

        Returns:
            True if file is pip-compatible (requirements.txt or Pipfile structure)
        """
        file_name_lower = file_name.lower()

        # Strategy 1: Check standard filenames (backwards compatibility)
        if file_name_lower in self.supported_files:
            return True

        # Strategy 2: Check filename patterns
        if file_name_lower.startswith("requirements") and file_name_lower.endswith(".txt"):
            return True

        # Strategy 3: Check .txt extension and validate content
        if file_name_lower.endswith(".txt"):
            # Plain text files - validate content if provided
            if content is not None:
                return self._is_pip_requirements_structure(content)
            # Without content, optimistically assume it's pip
            return True

        # Strategy 4: Check for Pipfile (TOML)
        if file_name_lower.endswith(".toml") or "pipfile" in file_name_lower:
            if content is not None:
                return self._is_pipfile_structure(content)
            return True

        return False

    def _is_pip_requirements_structure(self, content: str) -> bool:
        """Detect if text content is pip requirements format.

        Looks for pip requirement patterns:
        - package==1.2.3
        - package>=1.2.3
        - git+https://...
        - Comments with #

        Args:
            content: File content as string

        Returns:
            True if content looks like pip requirements
        """
        if not isinstance(content, str):
            return False

        lines = content.strip().split("\n")

        # Count lines that look like pip requirements
        valid_patterns = 0
        total_non_empty = 0

        for line in lines:
            # Remove comments
            if "#" in line:
                line = line[: line.index("#")]
            line = line.strip()

            # Skip empty lines and pip options
            if not line or line.startswith("-"):
                continue

            total_non_empty += 1

            # Check for pip requirement patterns
            if any(
                [
                    "==" in line,
                    ">=" in line,
                    "<=" in line,
                    "~=" in line,
                    "!=" in line,
                    line.startswith("git+"),
                    line.startswith("http"),
                    # Simple package name (letters, numbers, hyphens, underscores)
                    re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$", line),
                ]
            ):
                valid_patterns += 1

        # If >50% of non-empty lines look like pip requirements, accept it
        if total_non_empty == 0:
            return False

        return (valid_patterns / total_non_empty) >= 0.5

    def _is_pipfile_structure(self, content: str) -> bool:
        """Detect if content is Pipfile TOML format.

        Args:
            content: File content as string

        Returns:
            True if content looks like a Pipfile
        """
        if not isinstance(content, str):
            return False

        # Check for TOML-like structure and Pipfile-specific sections
        has_packages = "[packages]" in content or "[[source]]" in content
        has_dev_packages = "[dev-packages]" in content
        has_toml_syntax = "=" in content and ("[" in content or "[[" in content)

        return has_packages or has_dev_packages or has_toml_syntax

    def parse_file(self, file_path: Path) -> list[ParsedDependency]:
        """Parse a pip requirements file or Pipfile and extract dependencies.

        Args:
            file_path: Path to requirements file or Pipfile

        Returns:
            List of ParsedDependency objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        # Detect if this is a Pipfile
        if file_path.name.lower() == "pipfile":
            return self.parse_pipfile(file_path)

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

    def parse_pipfile(self, file_path: Path) -> list[ParsedDependency]:
        """Parse a Pipfile (TOML format) and extract dependencies.

        Pipfile is used by Pipenv and contains both regular and dev dependencies.

        Args:
            file_path: Path to Pipfile

        Returns:
            List of ParsedDependency objects

        Raises:
            ValueError: If TOML parsing fails or tomllib is not available
        """
        if tomllib is None:
            raise ValueError(
                "TOML parsing not available. Install 'tomli' for Python <3.11 or upgrade to Python 3.11+"
            )

        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse Pipfile: {e}") from e

        dependencies = []

        # Parse production packages
        packages = data.get("packages", {})
        for package_name, version_spec in packages.items():
            dep = self._parse_pipfile_package(package_name, version_spec, is_dev=False)
            if dep:
                dependencies.append(dep)

        # Parse dev packages
        dev_packages = data.get("dev-packages", {})
        for package_name, version_spec in dev_packages.items():
            dep = self._parse_pipfile_package(package_name, version_spec, is_dev=True)
            if dep:
                dependencies.append(dep)

        return dependencies

    def _parse_pipfile_package(
        self, package_name: str, version_spec: str | dict, is_dev: bool = False
    ) -> ParsedDependency | None:
        """Parse a package entry from Pipfile.

        Pipfile packages can be specified as:
        - Simple string: "==1.2.3" or ">=1.2.3"
        - Dictionary: {version = "==1.2.3", extras = ["security"]}
        - Wildcard: "*" (any version)

        Args:
            package_name: Name of the package
            version_spec: Version specification (string or dict)
            is_dev: Whether this is a dev dependency

        Returns:
            ParsedDependency object or None if cannot be parsed
        """
        # Handle dictionary format
        if isinstance(version_spec, dict):
            version_str = version_spec.get("version", "*")
            extras = version_spec.get("extras", [])
        else:
            version_str = str(version_spec)
            extras = []

        # Handle wildcard (any version)
        if version_str == "*":
            # Skip packages without specific versions
            return None

        # Parse version specification
        # Pipfile uses pip-style operators: ==, >=, <=, ~=, etc.
        version_pattern = r"^(==|>=|<=|>|<|~=|!=)?\s*(.+)$"
        match = re.match(version_pattern, version_str)

        if not match:
            return None

        operator = match.group(1) or "=="
        version = match.group(2).strip()

        # Resolve to concrete version
        if operator == "==":
            resolved_version = version
            constraint = f"=={version}"
        elif operator in [">=", "<=", ">", "<", "~=", "!="]:
            resolved_version = version
            constraint = f"{operator}{version}"
        else:
            resolved_version = version
            constraint = f"=={version}"

        metadata = {
            "original_spec": version_str,
            "operator": operator,
            "extras": extras,
            "dependency_type": "dev" if is_dev else "prod",
            "from_pipfile": True,
        }

        try:
            return ParsedDependency(
                package_name=package_name,
                version=resolved_version,
                version_constraint=constraint,
                ecosystem=self.ecosystem,
                is_dev_dependency=is_dev,
                metadata=metadata,
            )
        except ValueError:
            return None

    def __repr__(self) -> str:
        return f"<PipParser(ecosystem='{self.ecosystem}')>"

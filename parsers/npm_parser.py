"""Parser for npm package.json files."""

import json
import re
from pathlib import Path

from parsers.base_parser import BaseParser, ParsedDependency


class NpmParser(BaseParser):
    """Parser for npm package.json dependency files."""

    def __init__(self):
        """Initialize the npm parser."""
        super().__init__(ecosystem="npm")
        self.supported_files = ["package.json", "package-lock.json"]

    def supports_file(self, file_name: str) -> bool:
        """Check if this parser supports the given file.

        Args:
            file_name: Name of the file

        Returns:
            True if file is package.json or package-lock.json
        """
        return file_name.lower() in self.supported_files

    def parse_file(self, file_path: Path) -> list[ParsedDependency]:
        """Parse a package.json file and extract dependencies.

        Args:
            file_path: Path to package.json

        Returns:
            List of ParsedDependency objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid
        """
        content = self.read_file_content(file_path)
        return self.parse_content(content)

    def parse_content(self, content: str) -> list[ParsedDependency]:
        """Parse package.json content and extract dependencies.

        Args:
            content: String content of package.json

        Returns:
            List of ParsedDependency objects

        Raises:
            ValueError: If JSON is invalid or missing required fields
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in package.json: {str(e)}") from e

        if not isinstance(data, dict):
            raise ValueError("package.json must contain a JSON object")

        dependencies = []

        # Parse production dependencies
        if "dependencies" in data and isinstance(data["dependencies"], dict):
            for package_name, version_spec in data["dependencies"].items():
                dep = self._create_dependency(package_name, version_spec, is_dev=False)
                if dep:
                    dependencies.append(dep)

        # Parse dev dependencies
        if "devDependencies" in data and isinstance(data["devDependencies"], dict):
            for package_name, version_spec in data["devDependencies"].items():
                dep = self._create_dependency(package_name, version_spec, is_dev=True)
                if dep:
                    dependencies.append(dep)

        # Parse peer dependencies (treat as production)
        if "peerDependencies" in data and isinstance(data["peerDependencies"], dict):
            for package_name, version_spec in data["peerDependencies"].items():
                dep = self._create_dependency(package_name, version_spec, is_dev=False)
                if dep:
                    dependencies.append(dep)

        # Parse optional dependencies (treat as production)
        if "optionalDependencies" in data and isinstance(data["optionalDependencies"], dict):
            for package_name, version_spec in data["optionalDependencies"].items():
                dep = self._create_dependency(package_name, version_spec, is_dev=False)
                if dep:
                    dependencies.append(dep)

        return dependencies

    def _create_dependency(
        self, package_name: str, version_spec: str, is_dev: bool = False
    ) -> ParsedDependency | None:
        """Create a ParsedDependency from npm package info.

        Args:
            package_name: Name of the npm package
            version_spec: Version specifier (e.g., "^1.2.3", ">=4.0.0")
            is_dev: Whether this is a dev dependency

        Returns:
            ParsedDependency object or None if version cannot be resolved
        """
        # Extract version constraint and resolved version
        version_constraint = version_spec.strip()
        resolved_version = self._resolve_version(version_spec)

        if not resolved_version:
            # Skip if we can't determine a version
            return None

        metadata = {
            "original_spec": version_spec,
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
            # Skip invalid dependencies
            return None

    def _resolve_version(self, version_spec: str) -> str | None:
        """Resolve a version specifier to a concrete version.

        For npm version ranges like "^1.2.3", "~1.2.3", ">=1.2.3",
        we extract the base version number.

        Args:
            version_spec: npm version specifier

        Returns:
            Resolved version string or None if cannot be resolved

        Examples:
            "^1.2.3" -> "1.2.3"
            "~1.2.3" -> "1.2.3"
            ">=1.2.3" -> "1.2.3"
            "1.2.3" -> "1.2.3"
            "latest" -> None (cannot resolve without registry)
            "*" -> None (any version)
        """
        # Remove whitespace
        version_spec = version_spec.strip()

        # Handle special cases
        if version_spec in ["*", "latest", "next", ""]:
            return None

        # Handle URL dependencies (git, http, file)
        if any(
            version_spec.startswith(prefix)
            for prefix in ["git+", "http://", "https://", "file:", "github:"]
        ):
            return None

        # Handle version ranges with ||
        if "||" in version_spec:
            # Take the first alternative
            version_spec = version_spec.split("||")[0].strip()

        # Remove common npm version prefixes
        # ^1.2.3 -> 1.2.3
        # ~1.2.3 -> 1.2.3
        # >=1.2.3 -> 1.2.3
        # >1.2.3 -> 1.2.3
        # <=1.2.3 -> 1.2.3
        # <1.2.3 -> 1.2.3
        # =1.2.3 -> 1.2.3
        version_spec = re.sub(r"^[\^~><=]+", "", version_spec)

        # Handle version ranges like "1.2.3 - 2.0.0"
        if " - " in version_spec:
            # Take the first version in the range
            version_spec = version_spec.split(" - ")[0].strip()

        # Handle workspace protocol (yarn/pnpm)
        if version_spec.startswith("workspace:"):
            return None

        # Extract version using regex
        # Match semantic version patterns like 1.2.3, 1.2.3-beta.1, etc.
        version_pattern = r"(\d+\.\d+\.\d+(?:[-+][a-zA-Z0-9.-]+)?)"
        match = re.search(version_pattern, version_spec)

        if match:
            return match.group(1)

        return None

    def __repr__(self) -> str:
        return f"<NpmParser(ecosystem='{self.ecosystem}', supports={self.supported_files})>"

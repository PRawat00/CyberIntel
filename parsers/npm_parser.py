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

    def supports_file(self, file_name: str, content: str = None) -> bool:
        """Check if this parser supports the given file.

        Uses intelligent detection: checks filename, extension, and content structure.
        This allows users to upload files with ANY name (e.g., "my-app.json").

        Args:
            file_name: Name of the file
            content: Optional file content for structure validation

        Returns:
            True if file is npm-compatible (package.json or package-lock.json structure)
        """
        file_name_lower = file_name.lower()

        # Strategy 1: Check standard filenames (backwards compatibility)
        if file_name_lower in self.supported_files:
            return True

        # Strategy 2: Check file extension and validate content
        if file_name_lower.endswith(".json"):
            # If content provided, validate JSON structure
            if content is not None:
                return self._is_npm_json_structure(content)
            # Without content, optimistically assume it's npm (will fail later if not)
            return True

        return False

    def _is_npm_json_structure(self, content: str) -> bool:
        """Detect if JSON content is npm package.json or package-lock.json.

        Checks for characteristic npm fields:
        - package.json: "dependencies", "devDependencies", "name", "version"
        - package-lock.json: "lockfileVersion", "packages"

        Args:
            content: File content as string

        Returns:
            True if content matches npm JSON structure
        """
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                return False

            # package.json indicators
            has_pkg_json_fields = any(
                key in data
                for key in [
                    "dependencies",
                    "devDependencies",
                    "peerDependencies",
                    "optionalDependencies",
                ]
            )

            # package-lock.json indicators
            has_lock_fields = "lockfileVersion" in data or "packages" in data

            return has_pkg_json_fields or has_lock_fields
        except (json.JSONDecodeError, ValueError, TypeError):
            return False

    def _is_lock_file_structure(self, content: str) -> bool:
        """Detect if JSON content is package-lock.json structure.

        package-lock.json has specific fields that distinguish it from package.json:
        - "lockfileVersion" field (always present)
        - "packages" field with node_modules paths (lockfileVersion 2+)

        Args:
            content: File content as string

        Returns:
            True if content is package-lock.json structure
        """
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                return False

            # Lock file must have lockfileVersion
            if "lockfileVersion" in data:
                return True

            # Or have packages field with node_modules structure
            if "packages" in data and isinstance(data["packages"], dict):
                # Check if any key starts with "node_modules/" (indicates lock file)
                for key in data["packages"].keys():
                    if key.startswith("node_modules/"):
                        return True

            return False
        except (json.JSONDecodeError, ValueError, TypeError):
            return False

    def parse_file(self, file_path: Path) -> list[ParsedDependency]:
        """Parse a package.json or package-lock.json file and extract dependencies.

        Args:
            file_path: Path to package.json or package-lock.json

        Returns:
            List of ParsedDependency objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid
        """
        content = self.read_file_content(file_path)

        # Detect if this is a lock file by content structure (not just filename)
        # This allows files with ANY name to be correctly parsed
        if self._is_lock_file_structure(content):
            return self.parse_lock_file_content(content)
        else:
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

    def parse_lock_file_content(self, content: str) -> list[ParsedDependency]:
        """Parse package-lock.json content and extract all dependencies.

        package-lock.json contains exact versions of all dependencies (including transitive).
        This provides more accurate vulnerability scanning than package.json alone.

        Supports lockfileVersion 2 and 3 (npm 7+).

        Args:
            content: String content of package-lock.json

        Returns:
            List of ParsedDependency objects with exact versions

        Raises:
            ValueError: If JSON is invalid or unsupported lock file version
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in package-lock.json: {str(e)}") from e

        if not isinstance(data, dict):
            raise ValueError("package-lock.json must contain a JSON object")

        # Check lock file version
        lockfile_version = data.get("lockfileVersion", 1)

        if lockfile_version < 2:
            # Legacy lockfileVersion 1 (npm 5-6) - not supported yet
            raise ValueError(
                f"Unsupported lockfileVersion {lockfile_version}. "
                "Please upgrade to npm 7+ (lockfileVersion 2 or 3) "
                "or use package.json instead."
            )

        dependencies = []

        # Parse packages object (lockfileVersion 2 and 3)
        packages = data.get("packages", {})

        for pkg_path, pkg_info in packages.items():
            # Skip root package (empty string key)
            if pkg_path == "":
                continue

            # Extract package name from path (node_modules/package-name)
            if not pkg_path.startswith("node_modules/"):
                continue

            # Handle scoped packages (@org/package) and regular packages
            package_name = pkg_path.replace("node_modules/", "")

            # Get exact version
            version = pkg_info.get("version")
            if not version:
                continue

            # Determine if dev dependency
            is_dev = pkg_info.get("dev", False)

            # Get integrity hash for verification (optional)
            integrity = pkg_info.get("integrity")

            metadata = {
                "original_spec": f"={version}",  # Exact version from lock file
                "dependency_type": "dev" if is_dev else "prod",
                "from_lock_file": True,
                "integrity": integrity,
                "resolved": pkg_info.get("resolved"),
            }

            try:
                dep = ParsedDependency(
                    package_name=package_name,
                    version=version,
                    version_constraint=f"={version}",  # Exact version
                    ecosystem=self.ecosystem,
                    is_dev_dependency=is_dev,
                    metadata=metadata,
                )
                dependencies.append(dep)
            except ValueError:
                # Skip invalid dependencies
                continue

        return dependencies

    def __repr__(self) -> str:
        return f"<NpmParser(ecosystem='{self.ecosystem}', supports={self.supported_files})>"

"""Base parser interface for dependency files."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ParsedDependency:
    """Data class representing a parsed dependency."""

    package_name: str
    version: str
    version_constraint: str | None = None  # e.g., ">=4.0.0", "^1.2.3"
    ecosystem: str = ""  # npm, pip, go, ruby, maven
    is_dev_dependency: bool = False
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """Validate and normalize fields after initialization."""
        if not self.package_name:
            raise ValueError("package_name cannot be empty")
        if not self.version:
            raise ValueError("version cannot be empty")
        if not self.ecosystem:
            raise ValueError("ecosystem cannot be empty")

        # Normalize package name (lowercase, strip whitespace)
        self.package_name = self.package_name.strip().lower()
        self.version = self.version.strip()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "package_name": self.package_name,
            "version": self.version,
            "version_constraint": self.version_constraint,
            "ecosystem": self.ecosystem,
            "is_dev_dependency": self.is_dev_dependency,
            "metadata": self.metadata,
        }


class BaseParser(ABC):
    """Abstract base class for dependency file parsers.

    All ecosystem-specific parsers (npm, pip, go, ruby, maven) should inherit
    from this class and implement the required methods.
    """

    def __init__(self, ecosystem: str):
        """Initialize the parser.

        Args:
            ecosystem: The package ecosystem (npm, pip, go, ruby, maven)
        """
        self.ecosystem = ecosystem

    @abstractmethod
    def parse_file(self, file_path: Path) -> list[ParsedDependency]:
        """Parse a dependency file and extract package information.

        Args:
            file_path: Path to the dependency file

        Returns:
            List of ParsedDependency objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid or cannot be parsed
        """
        pass

    @abstractmethod
    def parse_content(self, content: str) -> list[ParsedDependency]:
        """Parse dependency file content and extract package information.

        Args:
            content: String content of the dependency file

        Returns:
            List of ParsedDependency objects

        Raises:
            ValueError: If content format is invalid or cannot be parsed
        """
        pass

    @abstractmethod
    def supports_file(self, file_name: str) -> bool:
        """Check if this parser supports the given file.

        Args:
            file_name: Name of the file (e.g., "package.json", "requirements.txt")

        Returns:
            True if this parser can handle the file, False otherwise
        """
        pass

    def validate_file_exists(self, file_path: Path) -> None:
        """Validate that the file exists and is readable.

        Args:
            file_path: Path to validate

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If path is not a file
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

    def read_file_content(self, file_path: Path) -> str:
        """Read and return file content as string.

        Args:
            file_path: Path to the file

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        self.validate_file_exists(file_path)
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise OSError(f"Failed to read file {file_path}: {str(e)}") from e

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(ecosystem='{self.ecosystem}')>"

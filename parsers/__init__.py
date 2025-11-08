"""Dependency file parsers for multiple ecosystems."""

from parsers.base_parser import BaseParser, ParsedDependency
from parsers.npm_parser import NpmParser
from parsers.pip_parser import PipParser

__all__ = [
    "BaseParser",
    "ParsedDependency",
    "NpmParser",
    "PipParser",
]

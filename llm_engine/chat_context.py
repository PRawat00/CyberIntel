"""
Core data structures for the unified chat system.

This module defines the context objects that flow through the chat system,
enabling dynamic, flexible context management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ChatContext:
    """
    Unified context object that holds all information needed for chat generation.

    This replaces the old session_type-based routing with a flexible context that
    can contain any combination of scans, dependencies, CVEs, and filters.
    """

    # Session identification
    session_id: int
    user_id: str

    # Conversation history
    conversation_history: list[dict[str, str]] = field(default_factory=list)

    # Dynamic contexts (can have multiple of each!)
    scans: list[int] = field(default_factory=list)
    dependencies: list[int] = field(default_factory=list)
    cves: list[str] = field(default_factory=list)

    # Query filters
    filters: dict[str, Any] = field(default_factory=dict)

    # Feature flags
    enabled_features: set[str] = field(default_factory=set)

    # Context metadata
    context_metadata: dict[str, Any] = field(default_factory=dict)

    # Timestamp
    created_at: datetime = field(default_factory=datetime.utcnow)

    def has_scan_context(self) -> bool:
        """Check if any scan context is present."""
        return len(self.scans) > 0

    def has_dependency_context(self) -> bool:
        """Check if any dependency context is present."""
        return len(self.dependencies) > 0

    def has_cve_context(self) -> bool:
        """Check if any CVE context is present."""
        return len(self.cves) > 0

    def is_empty(self) -> bool:
        """Check if context has no specific context (general query)."""
        return not (
            self.has_scan_context() or self.has_dependency_context() or self.has_cve_context()
        )

    def copy(self, **updates) -> "ChatContext":
        """Create a copy with updated fields."""
        from copy import deepcopy

        new_context = deepcopy(self)
        for key, value in updates.items():
            if hasattr(new_context, key):
                setattr(new_context, key, value)
        return new_context

    def merge(self, update: "ContextUpdate") -> "ChatContext":
        """Merge a context update into this context, creating a new context."""
        new_context = self.copy()

        if update.add_scans:
            new_context.scans = list(set(new_context.scans + update.add_scans))
        if update.remove_scans:
            new_context.scans = [s for s in new_context.scans if s not in update.remove_scans]

        if update.add_dependencies:
            new_context.dependencies = list(set(new_context.dependencies + update.add_dependencies))
        if update.remove_dependencies:
            new_context.dependencies = [
                d for d in new_context.dependencies if d not in update.remove_dependencies
            ]

        if update.add_cves:
            new_context.cves = list(set(new_context.cves + update.add_cves))
        if update.remove_cves:
            new_context.cves = [c for c in new_context.cves if c not in update.remove_cves]

        if update.filters:
            new_context.filters.update(update.filters)

        if update.enabled_features is not None:
            new_context.enabled_features = update.enabled_features

        if update.context_metadata:
            new_context.context_metadata.update(update.context_metadata)

        new_context.created_at = datetime.utcnow()

        return new_context

    @classmethod
    def empty(cls, session_id: int, user_id: str) -> "ChatContext":
        """Create an empty context for a new session."""
        return cls(session_id=session_id, user_id=user_id)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "conversation_history": self.conversation_history,
            "scans": self.scans,
            "dependencies": self.dependencies,
            "cves": self.cves,
            "filters": self.filters,
            "enabled_features": list(self.enabled_features),
            "context_metadata": self.context_metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatContext":
        """Create from dictionary (deserialization)."""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            conversation_history=data.get("conversation_history", []),
            scans=data.get("scans", []),
            dependencies=data.get("dependencies", []),
            cves=data.get("cves", []),
            filters=data.get("filters", {}),
            enabled_features=set(data.get("enabled_features", [])),
            context_metadata=data.get("context_metadata", {}),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if "created_at" in data
                else datetime.utcnow()
            ),
        )


@dataclass
class ContextUpdate:
    """
    Incremental update to a ChatContext.

    Used for dynamic context modifications mid-conversation.
    """

    # Add or remove scans
    add_scans: list[int] = field(default_factory=list)
    remove_scans: list[int] = field(default_factory=list)

    # Add or remove dependencies
    add_dependencies: list[int] = field(default_factory=list)
    remove_dependencies: list[int] = field(default_factory=list)

    # Add or remove CVEs
    add_cves: list[str] = field(default_factory=list)
    remove_cves: list[str] = field(default_factory=list)

    # Update filters (merged with existing)
    filters: dict[str, Any] | None = None

    # Replace enabled features
    enabled_features: set[str] | None = None

    # Update metadata (merged with existing)
    context_metadata: dict[str, Any] | None = None


@dataclass
class RetrievalResult:
    """
    Standardized result from a retrieval strategy.

    All strategies return this format for consistent processing.
    """

    # Retrieval metadata
    strategy_name: str
    query: str

    # Retrieved data
    cves: list[dict[str, Any]] = field(default_factory=list)
    scan_info: dict[str, Any] | None = None
    dependency_info: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    # Confidence/relevance scoring
    relevance_scores: dict[str, float] = field(default_factory=dict)

    def merge_with(self, other: "RetrievalResult") -> "RetrievalResult":
        """Merge two retrieval results, deduplicating CVEs by ID."""
        merged_cves = {cve["cve_id"]: cve for cve in self.cves}

        for cve in other.cves:
            cve_id = cve["cve_id"]
            if cve_id not in merged_cves:
                merged_cves[cve_id] = cve
            else:
                # Merge relevance scores (take max)
                if "relevance_score" in cve and "relevance_score" in merged_cves[cve_id]:
                    merged_cves[cve_id]["relevance_score"] = max(
                        cve["relevance_score"], merged_cves[cve_id]["relevance_score"]
                    )

        return RetrievalResult(
            strategy_name=f"{self.strategy_name}+{other.strategy_name}",
            query=self.query,
            cves=list(merged_cves.values()),
            scan_info=self.scan_info or other.scan_info,
            dependency_info=self.dependency_info + other.dependency_info,
            metadata={**self.metadata, **other.metadata},
            relevance_scores={**self.relevance_scores, **other.relevance_scores},
        )

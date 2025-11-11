"""
Intent router for smart strategy selection.

Analyzes user query and context to automatically select the most appropriate
retrieval strategies using a chain of responsibility pattern.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from llm_engine.chat_context import ChatContext
from llm_engine.intent_detector import DependencyIntentDetector, detect_intent
from llm_engine.strategies.base import RetrievalStrategy
from llm_engine.strategies.direct_dependency_strategy import DirectDependencyStrategy
from llm_engine.strategies.general_cve_strategy import GeneralCVEStrategy
from llm_engine.strategies.project_cve_strategy import ProjectCVEStrategy

logger = logging.getLogger(__name__)


class IntentHandler(ABC):
    """
    Abstract base class for intent handlers.

    Each handler checks if it can handle the query+context combination,
    and returns appropriate strategies if so.
    """

    def __init__(self, next_handler: Optional["IntentHandler"] = None):
        self.next_handler = next_handler

    @abstractmethod
    def can_handle(self, query: str, context: ChatContext) -> bool:
        """Check if this handler can handle the query/context."""
        pass

    @abstractmethod
    def select_strategies(self, query: str, context: ChatContext) -> list[RetrievalStrategy]:
        """Select strategies for this query/context."""
        pass

    def handle(self, query: str, context: ChatContext) -> list[RetrievalStrategy] | None:
        """
        Try to handle the query, or delegate to next handler.

        Returns:
            List of strategies if handled, None if passed to next handler
        """
        if self.can_handle(query, context):
            strategies = self.select_strategies(query, context)
            logger.info(f"{self.__class__.__name__}: Selected {len(strategies)} strategies")
            return strategies

        if self.next_handler:
            return self.next_handler.handle(query, context)

        return None

    def get_required_features(self) -> list[str]:
        """Return list of feature flags required for this handler."""
        return []


class GreetingHandler(IntentHandler):
    """Handles greeting queries (no CVE retrieval needed)."""

    def can_handle(self, query: str, context: ChatContext) -> bool:
        intent = detect_intent(query)
        return intent == "greeting"

    def select_strategies(self, query: str, context: ChatContext) -> list[RetrievalStrategy]:
        # Greetings don't need retrieval, return empty list
        # UnifiedChatModel will handle greeting response directly
        return []


class DependencyFocusedHandler(IntentHandler):
    """
    Handles queries specifically about selected dependencies.

    Uses dependency intent detection with confidence threshold.
    """

    def __init__(
        self, next_handler: IntentHandler | None = None, confidence_threshold: float = 0.3
    ):
        super().__init__(next_handler)
        self.confidence_threshold = confidence_threshold
        self.dependency_detector = DependencyIntentDetector()

    def can_handle(self, query: str, context: ChatContext) -> bool:
        if not context.has_dependency_context():
            return False

        # Convert dependency IDs to dependency objects for intent detection
        from sqlalchemy.orm import selectinload

        from database.db import get_db_session
        from database.models import Dependency

        with get_db_session() as session:
            dependencies = (
                session.query(Dependency)
                .options(selectinload(Dependency.cves))
                .filter(Dependency.id.in_(context.dependencies))
                .all()
            )

            # Expunge to make detached
            for dep in dependencies:
                for cve in dep.cves:
                    session.expunge(cve)
                session.expunge(dep)

        intent_result = self.dependency_detector.detect_intent(
            query=query,
            selected_dependencies=dependencies,
            conversation_history=context.conversation_history,
        )

        return intent_result.is_relevant and intent_result.confidence >= self.confidence_threshold

    def select_strategies(self, query: str, context: ChatContext) -> list[RetrievalStrategy]:
        """Use direct dependency retrieval - fastest and most accurate."""
        return [DirectDependencyStrategy()]


class ProjectScanHandler(IntentHandler):
    """
    Handles queries about a project/scan without specific dependency focus.
    """

    def can_handle(self, query: str, context: ChatContext) -> bool:
        # Has scan context but query is not specifically about dependencies
        return context.has_scan_context()

    def select_strategies(self, query: str, context: ChatContext) -> list[RetrievalStrategy]:
        """Use project CVE strategy for scan-based retrieval."""
        return [ProjectCVEStrategy()]


class GeneralSecurityHandler(IntentHandler):
    """
    Handles general security queries without specific context.

    This is the fallback handler that handles all queries.
    """

    def can_handle(self, query: str, context: ChatContext) -> bool:
        # Can always handle (fallback)
        return True

    def select_strategies(self, query: str, context: ChatContext) -> list[RetrievalStrategy]:
        """Use general CVE search across all CVEs."""
        return [GeneralCVEStrategy()]


class IntentRouter:
    """
    Main router that coordinates intent detection and strategy selection.

    Uses chain of responsibility pattern with multiple handlers.
    """

    def __init__(self):
        # Build handler chain (order matters - most specific first!)
        self.handler_chain = self._build_handler_chain()
        logger.info("IntentRouter initialized with handler chain")

    def _build_handler_chain(self) -> IntentHandler:
        """
        Build the chain of handlers.

        Order (most specific to most general):
        1. Greeting - Handle greetings
        2. DependencyFocused - Handle queries about selected dependencies
        3. ProjectScan - Handle queries about scans/projects
        4. GeneralSecurity - Fallback for general queries
        """
        general = GeneralSecurityHandler()
        project = ProjectScanHandler(next_handler=general)
        dependency = DependencyFocusedHandler(next_handler=project)
        greeting = GreetingHandler(next_handler=dependency)

        return greeting

    def route(self, query: str, context: ChatContext, **kwargs) -> list[RetrievalStrategy]:
        """
        Route query to appropriate strategies.

        Args:
            query: User's query
            context: Current chat context
            **kwargs: Additional routing parameters

        Returns:
            List of strategies to execute (may be empty for greetings)
        """
        logger.info(f"IntentRouter: Routing query '{query[:50]}...'")
        logger.info(
            f"Context: scans={len(context.scans)}, "
            f"deps={len(context.dependencies)}, "
            f"cves={len(context.cves)}"
        )

        # Run through handler chain
        strategies = self.handler_chain.handle(query, context)

        if strategies is None:
            logger.warning("IntentRouter: No handler matched, using fallback")
            strategies = [GeneralCVEStrategy()]

        logger.info(f"IntentRouter: Selected {len(strategies)} strategies")
        for strategy in strategies:
            logger.info(f"  - {strategy.get_name()}")

        return strategies

    def add_handler(self, handler: IntentHandler, position: int = -1):
        """
        Add a custom handler to the chain.

        Args:
            handler: Handler to add
            position: Position in chain (-1 for end, 0 for start)
        """
        # TODO: Implement dynamic handler insertion
        # For now, handlers are fixed in _build_handler_chain()
        logger.warning("Dynamic handler addition not yet implemented")


# Singleton instance
_router_instance = None


def get_intent_router() -> IntentRouter:
    """Get the global intent router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = IntentRouter()
    return _router_instance

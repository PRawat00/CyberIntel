"""
Base classes and interfaces for retrieval strategies.

Defines the Strategy pattern interface that all retrieval implementations must follow.
"""

import logging
from abc import ABC, abstractmethod

from llm_engine.chat_context import ChatContext, RetrievalResult

logger = logging.getLogger(__name__)


class RetrievalStrategy(ABC):
    """
    Abstract base class for all retrieval strategies.

    Each strategy implements a specific way of retrieving CVEs/context based on
    the query and context. Strategies can be combined using CompositeStrategy.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this strategy for logging/debugging."""
        pass

    @abstractmethod
    def can_handle(self, context: ChatContext) -> bool:
        """
        Check if this strategy can handle the given context.

        Returns:
            True if the strategy has the necessary context to execute.
        """
        pass

    @abstractmethod
    def retrieve(self, query: str, context: ChatContext, **kwargs) -> RetrievalResult:
        """
        Execute the retrieval strategy.

        Args:
            query: The user's query
            context: The current chat context
            **kwargs: Additional strategy-specific parameters

        Returns:
            RetrievalResult with CVEs and metadata
        """
        pass

    def get_required_features(self) -> list[str]:
        """
        Return list of feature flags required for this strategy.

        Used by FeatureManager to determine if strategy should be available.
        """
        return []


class StrategyRegistry:
    """
    Registry for all available retrieval strategies.

    Provides a central place to register and retrieve strategies.
    Implements singleton pattern.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.strategies: dict[str, type[RetrievalStrategy]] = {}
        self._initialized = True
        logger.info("StrategyRegistry initialized")

    def register(self, name: str, strategy_class: type[RetrievalStrategy]):
        """Register a strategy by name."""
        if name in self.strategies:
            logger.warning(f"Strategy '{name}' is already registered, overwriting")

        self.strategies[name] = strategy_class
        logger.info(f"Registered strategy: {name}")

    def get(self, name: str) -> RetrievalStrategy:
        """Get a strategy instance by name."""
        if name not in self.strategies:
            raise ValueError(f"Unknown strategy: {name}. Available: {list(self.strategies.keys())}")

        return self.strategies[name]()

    def get_all_names(self) -> list[str]:
        """Get names of all registered strategies."""
        return list(self.strategies.keys())

    def create_chain(self, strategy_names: list[str]) -> list[RetrievalStrategy]:
        """Create a list of strategy instances from names."""
        return [self.get(name) for name in strategy_names]


# Global registry instance
_registry = StrategyRegistry()


def get_strategy_registry() -> StrategyRegistry:
    """Get the global strategy registry instance."""
    return _registry

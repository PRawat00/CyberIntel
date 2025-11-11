"""
Composite strategy for combining multiple retrieval strategies.

Executes multiple strategies and merges their results, allowing complex
multi-source retrieval patterns.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm_engine.chat_context import ChatContext, RetrievalResult
from llm_engine.strategies.base import RetrievalStrategy

logger = logging.getLogger(__name__)


class CompositeStrategy(RetrievalStrategy):
    """
    Combines multiple retrieval strategies into one.

    This strategy:
    - Executes multiple sub-strategies
    - Can run them in parallel or sequentially
    - Merges results, deduplicating CVEs by ID
    - Aggregates metadata from all strategies
    """

    def __init__(self, strategies: list[RetrievalStrategy], parallel: bool = False):
        """
        Initialize composite strategy.

        Args:
            strategies: List of strategies to execute
            parallel: If True, execute strategies in parallel (faster but more resources)
        """
        self.strategies = strategies
        self.parallel = parallel

    def get_name(self) -> str:
        strategy_names = [s.get_name() for s in self.strategies]
        return f"composite({'+'.join(strategy_names)})"

    def can_handle(self, context: ChatContext) -> bool:
        """
        Can handle if at least one sub-strategy can handle.
        """
        return any(s.can_handle(context) for s in self.strategies)

    def retrieve(self, query: str, context: ChatContext, **kwargs) -> RetrievalResult:
        """
        Execute all sub-strategies and merge results.

        Args:
            query: User's query
            context: Chat context
            **kwargs: Parameters passed to all sub-strategies

        Returns:
            Merged RetrievalResult from all strategies
        """
        if not self.strategies:
            logger.warning("CompositeStrategy: No sub-strategies configured")
            return RetrievalResult(
                strategy_name=self.get_name(),
                query=query,
                cves=[],
                metadata={"error": "No sub-strategies"},
            )

        logger.info(
            f"CompositeStrategy: Executing {len(self.strategies)} strategies "
            f"({'parallel' if self.parallel else 'sequential'})"
        )

        results = []

        if self.parallel:
            results = self._execute_parallel(query, context, **kwargs)
        else:
            results = self._execute_sequential(query, context, **kwargs)

        # Filter out failed strategies
        successful_results = [r for r in results if r.cves or not r.metadata.get("error")]

        if not successful_results:
            logger.warning("CompositeStrategy: All sub-strategies failed")
            return RetrievalResult(
                strategy_name=self.get_name(),
                query=query,
                cves=[],
                metadata={
                    "error": "All sub-strategies failed",
                    "attempted_strategies": len(self.strategies),
                },
            )

        # Merge all results
        merged = successful_results[0]
        for result in successful_results[1:]:
            merged = merged.merge_with(result)

        # Update strategy name
        merged.strategy_name = self.get_name()

        logger.info(
            f"CompositeStrategy: Merged results - {len(merged.cves)} unique CVEs "
            f"from {len(successful_results)} strategies"
        )

        return merged

    def _execute_sequential(
        self, query: str, context: ChatContext, **kwargs
    ) -> list[RetrievalResult]:
        """Execute strategies one by one."""
        results = []
        for strategy in self.strategies:
            if not strategy.can_handle(context):
                logger.debug(f"Skipping {strategy.get_name()} - cannot handle context")
                continue

            try:
                result = strategy.retrieve(query, context, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Strategy {strategy.get_name()} failed: {e}", exc_info=True)
                results.append(
                    RetrievalResult(
                        strategy_name=strategy.get_name(),
                        query=query,
                        cves=[],
                        metadata={"error": str(e)},
                    )
                )

        return results

    def _execute_parallel(
        self, query: str, context: ChatContext, **kwargs
    ) -> list[RetrievalResult]:
        """Execute strategies in parallel using thread pool."""
        results = []

        def execute_strategy(strategy):
            if not strategy.can_handle(context):
                logger.debug(f"Skipping {strategy.get_name()} - cannot handle context")
                return None

            try:
                return strategy.retrieve(query, context, **kwargs)
            except Exception as e:
                logger.error(f"Strategy {strategy.get_name()} failed: {e}", exc_info=True)
                return RetrievalResult(
                    strategy_name=strategy.get_name(),
                    query=query,
                    cves=[],
                    metadata={"error": str(e)},
                )

        with ThreadPoolExecutor(max_workers=len(self.strategies)) as executor:
            future_to_strategy = {executor.submit(execute_strategy, s): s for s in self.strategies}

            for future in as_completed(future_to_strategy):
                result = future.result()
                if result is not None:
                    results.append(result)

        return results

    def get_required_features(self) -> list[str]:
        """Return union of all sub-strategies' required features."""
        all_features = set()
        for strategy in self.strategies:
            all_features.update(strategy.get_required_features())
        return list(all_features)

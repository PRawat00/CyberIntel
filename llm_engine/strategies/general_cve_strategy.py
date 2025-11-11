"""
General CVE retrieval strategy.

Searches across all CVEs in the vector store without any filtering to specific
projects or dependencies. Used for general security queries.
"""

import logging

from llm_engine.chat_context import ChatContext, RetrievalResult
from llm_engine.rag_retriever import RAGRetriever
from llm_engine.strategies.base import RetrievalStrategy

logger = logging.getLogger(__name__)


class GeneralCVEStrategy(RetrievalStrategy):
    """
    Retrieves CVEs using general semantic search across all CVEs.

    This strategy:
    - Uses vector search across the entire CVE database
    - Applies optional filters (severity, CVSS, vendor, product, date range)
    - Returns top-k most relevant CVEs
    - Does NOT filter to specific scans or dependencies
    """

    def __init__(self):
        self.rag = RAGRetriever()

    def get_name(self) -> str:
        return "general_cve"

    def can_handle(self, context: ChatContext) -> bool:
        """
        Can always handle any query (fallback strategy).

        This strategy doesn't require any specific context.
        """
        return True

    def retrieve(self, query: str, context: ChatContext, **kwargs) -> RetrievalResult:
        """
        Execute general CVE search.

        Args:
            query: User's query
            context: Chat context (filters may be used)
            **kwargs: Additional parameters:
                - top_k: Number of results to return (default: 5)
                - filters: Additional filters to apply

        Returns:
            RetrievalResult with CVEs from general search
        """
        top_k = kwargs.get("top_k", 5)

        # Merge context filters with any additional filters
        filters = {**context.filters, **kwargs.get("filters", {})}

        logger.info(f"GeneralCVEStrategy: Searching for '{query[:50]}...' with filters: {filters}")

        try:
            # Use RAG retriever for general query
            rag_results = self.rag.query_general(query=query, top_k=top_k, **filters)

            # Convert RAG results to standardized format
            cves = rag_results.get("cves", [])

            logger.info(f"GeneralCVEStrategy: Found {len(cves)} CVEs")

            return RetrievalResult(
                strategy_name=self.get_name(),
                query=query,
                cves=cves,
                metadata={
                    "mode": "general",
                    "top_k": top_k,
                    "filters_applied": filters,
                    "total_results": len(cves),
                },
            )

        except Exception as e:
            logger.error(f"GeneralCVEStrategy failed: {e}", exc_info=True)
            # Return empty result on failure
            return RetrievalResult(
                strategy_name=self.get_name(), query=query, cves=[], metadata={"error": str(e)}
            )

    def get_required_features(self) -> list[str]:
        """No special features required for general search."""
        return []

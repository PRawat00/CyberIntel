"""
Project-specific CVE retrieval strategy.

Retrieves CVEs that are specific to a project/scan, filtering to only those
CVEs that affect dependencies in the scan.
"""

import logging

from llm_engine.chat_context import ChatContext, RetrievalResult
from llm_engine.rag_retriever import RAGRetriever
from llm_engine.strategies.base import RetrievalStrategy

logger = logging.getLogger(__name__)


class ProjectCVEStrategy(RetrievalStrategy):
    """
    Retrieves CVEs filtered to a specific project/scan.

    This strategy:
    - Requires at least one scan in context
    - Uses vector search but filters results to CVEs affecting the scan
    - Can optionally filter to selected dependencies within the scan
    - Returns scan metadata along with CVEs
    """

    def __init__(self):
        self.rag = RAGRetriever()

    def get_name(self) -> str:
        return "project_cve"

    def can_handle(self, context: ChatContext) -> bool:
        """
        Requires at least one scan in context.
        """
        return context.has_scan_context()

    def retrieve(self, query: str, context: ChatContext, **kwargs) -> RetrievalResult:
        """
        Execute project-specific CVE search.

        Args:
            query: User's query
            context: Chat context (must have scans)
            **kwargs: Additional parameters:
                - top_k: Number of results to return (default: 5)
                - scan_id: Specific scan to use (if None, uses first from context)
                - dependency_filter: Whether to filter to selected dependencies

        Returns:
            RetrievalResult with CVEs from project search
        """
        if not self.can_handle(context):
            logger.warning("ProjectCVEStrategy: No scan context available")
            return RetrievalResult(
                strategy_name=self.get_name(),
                query=query,
                cves=[],
                metadata={"error": "No scan context"},
            )

        top_k = kwargs.get("top_k", 5)
        scan_id = kwargs.get("scan_id") or context.scans[0]
        dependency_filter = kwargs.get("dependency_filter", context.has_dependency_context())

        # Merge filters
        filters = {**context.filters, **kwargs.get("filters", {})}

        logger.info(
            f"ProjectCVEStrategy: Searching for '{query[:50]}...' "
            f"in scan {scan_id} with dependency_filter={dependency_filter}"
        )

        try:
            # Use RAG retriever for project query
            rag_results = self.rag.query_project(
                query=query,
                scan_id=scan_id,
                dependency_filter=context.dependencies if dependency_filter else None,
                top_k=top_k,
                **filters,
            )

            cves = rag_results.get("cves", [])
            scan_info = rag_results.get("scan_info")

            logger.info(f"ProjectCVEStrategy: Found {len(cves)} CVEs for scan {scan_id}")

            return RetrievalResult(
                strategy_name=self.get_name(),
                query=query,
                cves=cves,
                scan_info=scan_info,
                metadata={
                    "mode": "project",
                    "scan_id": scan_id,
                    "dependency_filter": dependency_filter,
                    "top_k": top_k,
                    "filters_applied": filters,
                    "total_results": len(cves),
                },
            )

        except Exception as e:
            logger.error(f"ProjectCVEStrategy failed: {e}", exc_info=True)
            return RetrievalResult(
                strategy_name=self.get_name(),
                query=query,
                cves=[],
                metadata={"error": str(e), "scan_id": scan_id},
            )

    def get_required_features(self) -> list[str]:
        """No special features required for project search."""
        return []

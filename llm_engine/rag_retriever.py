"""RAG Retriever - Query orchestration for general and project-specific CVE search."""

import logging
from typing import Any

from database.db import get_db_session
from database.models import Dependency, Scan
from llm_engine.embedder import CVEEmbedder
from llm_engine.vector_store import CVEVectorStore

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieval-Augmented Generation (RAG) retriever for CVE queries.

    Supports two query modes:
    1. General Mode: Search all CVEs semantically
    2. Project Mode: Search CVEs relevant to a specific scan/project

    Without LLM integration (Phase 4a), this returns structured JSON results.
    Phase 5 will add LLM to generate conversational responses.
    """

    def __init__(
        self, embedder: CVEEmbedder | None = None, vector_store: CVEVectorStore | None = None
    ):
        """Initialize RAG retriever.

        Args:
            embedder: CVEEmbedder instance (creates new if None)
            vector_store: CVEVectorStore instance (creates new if None)
        """
        self.embedder = embedder or CVEEmbedder()
        self.vector_store = vector_store or CVEVectorStore()

        logger.info(f"RAG Retriever initialized with {self.vector_store.count()} CVEs")

    def query_general(
        self,
        query: str,
        top_k: int = 10,
        severity_filter: list[str] | None = None,
        min_cvss: float | None = None,
        vendor_filter: str | None = None,
        product_filter: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
    ) -> dict[str, Any]:
        """Query CVEs with semantic search (General Mode).

        Use cases:
        - "Tell me about SQL injection vulnerabilities"
        - "Show me critical Apache Log4j CVEs"
        - "What are the most severe authentication bypass issues?"

        Args:
            query: Natural language query
            top_k: Number of results to return
            severity_filter: Filter by severities (e.g., ["CRITICAL", "HIGH"])
            min_cvss: Minimum CVSS score
            vendor_filter: Filter by vendor name
            product_filter: Filter by product name
            date_start: Start date (ISO format)
            date_end: End date (ISO format)

        Returns:
            Dictionary with query results:
            {
                "query": str,
                "mode": "general",
                "results_count": int,
                "cves": List[Dict],
                "filters_applied": Dict
            }
        """
        logger.info(f"General query: '{query}' (top_k={top_k})")

        # Generate query embedding
        query_embedding = self.embedder.embed(query).squeeze()

        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            severity_filter=severity_filter,
            min_cvss=min_cvss,
            vendor_filter=vendor_filter,
            product_filter=product_filter,
            date_start=date_start,
            date_end=date_end,
        )

        # Format response
        cves = []
        for result in results:
            cve_data = {
                "cve_id": result["cve_id"],
                "description": result["description"],
                "severity": result["metadata"].get("severity", "UNKNOWN"),
                "cvss_score": result["metadata"].get("cvss_score", 0.0),
                "vendor": result["metadata"].get("vendor", "unknown"),
                "product": result["metadata"].get("product", "unknown"),
                "published_date": result["metadata"].get("published_date", ""),
                "relevance_score": result["relevance_score"],
            }
            cves.append(cve_data)

        return {
            "query": query,
            "mode": "general",
            "results_count": len(cves),
            "cves": cves,
            "filters_applied": {
                "severity": severity_filter,
                "min_cvss": min_cvss,
                "vendor": vendor_filter,
                "product": product_filter,
                "date_range": f"{date_start} to {date_end}" if date_start or date_end else None,
            },
        }

    def query_project(
        self,
        query: str,
        scan_id: int,
        dependency_filter: list | None = None,
        top_k: int = 10,
        severity_filter: list[str] | None = None,
    ) -> dict[str, Any]:
        """Query CVEs relevant to a specific project/scan (Project Mode).

        Use cases:
        - "Which CVEs should I prioritize in my React app?"
        - "What are the most critical issues in my dependencies?"
        - "Explain the authentication vulnerabilities affecting my project"

        This method:
        1. Retrieves the scan and its vulnerable dependencies
        2. Optionally filters to specific dependencies
        3. Searches for CVEs that affect those dependencies
        4. Ranks results by relevance to the query

        Args:
            query: Natural language query about the project
            scan_id: ID of the scan to analyze
            dependency_filter: Optional list of Dependency objects to focus on
            top_k: Number of results to return
            severity_filter: Optional severity filter

        Returns:
            Dictionary with query results including scan context:
            {
                "query": str,
                "mode": "project",
                "scan_info": Dict,
                "results_count": int,
                "cves": List[Dict with affected_packages],
                "selected_dependency_count": int (if filtered)
            }
        """
        dep_filter_str = (
            f" (filtered to {len(dependency_filter)} deps)" if dependency_filter else ""
        )
        logger.info(f"Project query for scan {scan_id}{dep_filter_str}: '{query}' (top_k={top_k})")

        # Retrieve scan from database
        with get_db_session() as session:
            scan = session.query(Scan).filter(Scan.id == scan_id).first()

            if not scan:
                logger.error(f"Scan {scan_id} not found")
                return {"error": f"Scan {scan_id} not found", "query": query, "mode": "project"}

            # Get scan info
            scan_info = {
                "scan_id": scan.id,
                "file_name": scan.file_name,
                "file_type": scan.file_type,
                "scan_date": scan.scan_date.isoformat() if scan.scan_date else None,
                "total_dependencies": scan.total_dependencies,
                "vulnerable_dependencies": scan.vulnerable_dependencies,
                "total_cves": scan.total_cves,
            }

            # Get vulnerable dependencies (optionally filtered to selected deps)
            if dependency_filter:
                # Use the provided dependency objects
                vulnerable_deps = dependency_filter
                logger.info(f"Using {len(vulnerable_deps)} selected dependencies")
            else:
                # Get all vulnerable dependencies for the scan
                vulnerable_deps = (
                    session.query(Dependency)
                    .filter(Dependency.scan_id == scan_id, Dependency.is_vulnerable == 1)
                    .all()
                )

            # Collect all CVE IDs affecting the dependencies
            scan_cve_ids = set()
            package_cve_map = {}  # Map CVE ID to packages it affects

            for dep in vulnerable_deps:
                for cve in dep.cves:
                    scan_cve_ids.add(cve.cve_id)
                    if cve.cve_id not in package_cve_map:
                        package_cve_map[cve.cve_id] = []
                    package_cve_map[cve.cve_id].append(f"{dep.package_name}@{dep.version}")

        if not scan_cve_ids:
            logger.warning(f"No CVEs found for scan {scan_id}")
            return {
                "query": query,
                "mode": "project",
                "scan_info": scan_info,
                "results_count": 0,
                "cves": [],
                "message": "No vulnerabilities found in this scan",
            }

        # Generate query embedding
        query_embedding = self.embedder.embed(query).squeeze()

        # Search only among CVEs affecting this scan
        # Note: ChromaDB doesn't support $in with large lists well, so we:
        # 1. Search broadly
        # 2. Filter results to scan's CVEs
        # 3. Rank by relevance

        all_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 3,  # Get more results to filter
            severity_filter=severity_filter,
        )

        # Filter to only CVEs in this scan and add package info
        project_cves = []
        for result in all_results:
            cve_id = result["cve_id"]
            if cve_id in scan_cve_ids:
                cve_data = {
                    "cve_id": cve_id,
                    "description": result["description"],
                    "severity": result["metadata"].get("severity", "UNKNOWN"),
                    "cvss_score": result["metadata"].get("cvss_score", 0.0),
                    "vendor": result["metadata"].get("vendor", "unknown"),
                    "product": result["metadata"].get("product", "unknown"),
                    "published_date": result["metadata"].get("published_date", ""),
                    "relevance_score": result["relevance_score"],
                    "affects_packages": package_cve_map.get(cve_id, []),  # NEW: Project-specific
                }
                project_cves.append(cve_data)

            if len(project_cves) >= top_k:
                break

        result = {
            "query": query,
            "mode": "project",
            "scan_info": scan_info,
            "results_count": len(project_cves),
            "cves": project_cves,
        }

        # Add selected dependency count if filtered
        if dependency_filter:
            result["selected_dependency_count"] = len(dependency_filter)

        return result

    def find_similar_cves(
        self, cve_id: str, top_k: int = 5, exclude_self: bool = True
    ) -> dict[str, Any]:
        """Find CVEs similar to a given CVE.

        Use case: "Show me CVEs similar to CVE-2024-1234"

        Args:
            cve_id: Reference CVE ID
            top_k: Number of similar CVEs to return
            exclude_self: Whether to exclude the reference CVE from results

        Returns:
            Dictionary with similar CVEs
        """
        logger.info(f"Finding CVEs similar to {cve_id}")

        # Get the reference CVE
        ref_cve = self.vector_store.get_cve(cve_id)

        if not ref_cve:
            return {"error": f"CVE {cve_id} not found", "cve_id": cve_id}

        # Search using its embedding
        results = self.vector_store.search(
            query_embedding=ref_cve["embedding"], top_k=top_k + 1 if exclude_self else top_k
        )

        # Format results
        similar_cves = []
        for result in results:
            if exclude_self and result["cve_id"] == cve_id:
                continue

            similar_cves.append(
                {
                    "cve_id": result["cve_id"],
                    "description": result["description"],
                    "severity": result["metadata"].get("severity", "UNKNOWN"),
                    "cvss_score": result["metadata"].get("cvss_score", 0.0),
                    "similarity_score": result["relevance_score"],
                }
            )

        return {
            "reference_cve": {
                "cve_id": cve_id,
                "description": ref_cve["description"],
                "severity": ref_cve["metadata"].get("severity", "UNKNOWN"),
            },
            "similar_cves": similar_cves[:top_k],
            "count": len(similar_cves[:top_k]),
        }

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the RAG system.

        Returns:
            Dictionary with system statistics
        """
        return {
            "total_cves": self.vector_store.count(),
            "embedding_dimension": self.embedder.embedding_dim,
            "model": self.embedder.model_name,
            "vector_store": str(self.vector_store),
        }

    def __repr__(self) -> str:
        return f"RAGRetriever(cves={self.vector_store.count()}, model={self.embedder.model_name})"

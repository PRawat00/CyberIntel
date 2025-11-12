"""
Direct dependency CVE retrieval strategy.

Bypasses vector search entirely and retrieves CVEs directly from selected
dependencies using database relationships. This is the fastest and most accurate
strategy when specific dependencies are selected.
"""

import logging

from sqlalchemy.orm import selectinload

from database.db import get_db_session
from database.models import Dependency
from llm_engine.chat_context import ChatContext, RetrievalResult
from llm_engine.strategies.base import RetrievalStrategy

logger = logging.getLogger(__name__)


class DirectDependencyStrategy(RetrievalStrategy):
    """
    Retrieves CVEs directly from selected dependencies.

    This strategy:
    - Requires dependencies in context
    - Bypasses vector search completely
    - Extracts CVEs directly from Dependency.cves relationship
    - Is the FASTEST strategy (no embeddings, no similarity search)
    - Returns 100% accurate results for selected dependencies
    """

    def get_name(self) -> str:
        return "direct_dependency"

    def can_handle(self, context: ChatContext) -> bool:
        """
        Requires at least one dependency in context.
        """
        return context.has_dependency_context()

    def retrieve(self, query: str, context: ChatContext, **kwargs) -> RetrievalResult:
        """
        Execute direct CVE extraction from dependencies.

        Args:
            query: User's query (used for metadata only)
            context: Chat context (must have dependencies)
            **kwargs: Additional parameters (ignored for this strategy)

        Returns:
            RetrievalResult with CVEs directly from dependencies
        """
        if not self.can_handle(context):
            logger.warning("DirectDependencyStrategy: No dependency context available")
            return RetrievalResult(
                strategy_name=self.get_name(),
                query=query,
                cves=[],
                metadata={"error": "No dependency context"},
            )

        dependency_ids = context.dependencies

        # SECURITY: Validate all dependency IDs are integers to prevent SQL injection
        try:
            validated_ids = [int(dep_id) for dep_id in dependency_ids]
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid dependency IDs: {dependency_ids} - {e}")
            return RetrievalResult(
                strategy_name=self.get_name(),
                query=query,
                cves=[],
                metadata={"error": "Invalid dependency IDs provided"},
            )

        logger.info(
            f"DirectDependencyStrategy: Extracting CVEs for {len(validated_ids)} dependencies"
        )

        try:
            cves = []
            dependency_info = []
            seen_cve_ids = set()

            with get_db_session() as session:
                # Fetch dependencies with eager-loaded CVEs
                dependencies = (
                    session.query(Dependency)
                    .options(selectinload(Dependency.cves))
                    .filter(Dependency.id.in_(validated_ids))  # Use validated IDs
                    .all()
                )

                # Extract CVEs from each dependency
                for dep in dependencies:
                    dep_info = {
                        "id": dep.id,
                        "package_name": dep.package_name,
                        "version": dep.version,
                        "ecosystem": dep.ecosystem,
                        "severity": dep.highest_severity,
                        "cve_count": len(dep.cves),
                        "is_vulnerable": dep.is_vulnerable,
                    }
                    dependency_info.append(dep_info)

                    # Log safe packages explicitly
                    if len(dep.cves) == 0:
                        logger.info(
                            f"Package {dep.package_name}@{dep.version} ({dep.ecosystem}) "
                            "is SAFE - no known vulnerabilities"
                        )

                    # Extract CVEs
                    for cve in dep.cves:
                        if cve.cve_id not in seen_cve_ids:
                            cves.append(
                                {
                                    "cve_id": cve.cve_id,
                                    "description": cve.description,
                                    "severity": cve.severity,
                                    "cvss_score": cve.cvss_score,
                                    "cvss_vector": cve.cvss_vector,
                                    "vendor": cve.vendor,
                                    "product": cve.product,
                                    "published_date": (
                                        cve.published_date.isoformat()
                                        if cve.published_date
                                        else None
                                    ),
                                    "last_modified": (
                                        cve.last_modified.isoformat() if cve.last_modified else None
                                    ),
                                    "cwe_ids": cve.cwe_ids,
                                    "references": cve.references,
                                    "affects_packages": [f"{dep.package_name}@{dep.version}"],
                                    "relevance_score": 1.0,  # 100% relevant - directly from selected dependency
                                }
                            )
                            seen_cve_ids.add(cve.cve_id)
                        else:
                            # CVE already added, just append affected package
                            for existing_cve in cves:
                                if existing_cve["cve_id"] == cve.cve_id:
                                    existing_cve["affects_packages"].append(
                                        f"{dep.package_name}@{dep.version}"
                                    )
                                    break

            logger.info(
                f"DirectDependencyStrategy: Found {len(cves)} unique CVEs "
                f"across {len(dependencies)} dependencies"
            )

            return RetrievalResult(
                strategy_name=self.get_name(),
                query=query,
                cves=cves,
                dependency_info=dependency_info,
                metadata={
                    "mode": "direct",
                    "dependency_count": len(dependencies),
                    "cve_count": len(cves),
                    "bypassed_vector_search": True,
                },
            )

        except Exception as e:
            logger.error(f"DirectDependencyStrategy failed: {e}", exc_info=True)
            return RetrievalResult(
                strategy_name=self.get_name(), query=query, cves=[], metadata={"error": str(e)}
            )

    def get_required_features(self) -> list[str]:
        """No special features required for direct retrieval."""
        return []

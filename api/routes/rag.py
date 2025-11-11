"""RAG API endpoints for semantic CVE search."""

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from llm_engine.rag_retriever import RAGRetriever

logger = logging.getLogger(__name__)

# Initialize RAG retriever (singleton pattern)
_rag_retriever = None


def get_rag_retriever() -> RAGRetriever:
    """Get or create RAG retriever instance."""
    global _rag_retriever
    if _rag_retriever is None:
        logger.info("Initializing RAG retriever...")
        _rag_retriever = RAGRetriever()
    return _rag_retriever


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for general CVE query."""

    query: str = Field(..., description="Natural language query", min_length=1, max_length=500)
    top_k: int = Field(10, description="Number of results to return", ge=1, le=50)
    severity_filter: list[str] | None = Field(
        None, description="Filter by severities (CRITICAL, HIGH, MEDIUM, LOW)"
    )
    min_cvss: float | None = Field(None, description="Minimum CVSS score", ge=0.0, le=10.0)
    vendor_filter: str | None = Field(None, description="Filter by vendor name")
    product_filter: str | None = Field(None, description="Filter by product name")
    date_start: str | None = Field(None, description="Start date (ISO format)")
    date_end: str | None = Field(None, description="End date (ISO format)")


class ProjectQueryRequest(BaseModel):
    """Request model for project-specific query."""

    query: str = Field(
        ..., description="Natural language query about the project", min_length=1, max_length=500
    )
    top_k: int = Field(10, description="Number of results to return", ge=1, le=50)
    severity_filter: list[str] | None = Field(None, description="Filter by severities")


class CVEResult(BaseModel):
    """CVE search result."""

    cve_id: str
    description: str
    severity: str
    cvss_score: float
    vendor: str
    product: str
    published_date: str
    relevance_score: float
    affects_packages: list[str] | None = None  # Only for project queries


class QueryResponse(BaseModel):
    """Response model for CVE queries."""

    query: str
    mode: str  # "general" or "project"
    results_count: int
    cves: list[dict]
    filters_applied: dict | None = None
    scan_info: dict | None = None


# Create router
router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.post("/query", response_model=QueryResponse)
async def query_general(request: QueryRequest):
    """Query CVEs with semantic search (General Mode).

    Use cases:
    - "Tell me about SQL injection vulnerabilities"
    - "Show me critical Apache Log4j CVEs"
    - "What are the most severe authentication bypass issues in 2024?"

    Examples:
        ```bash
        curl -X POST http://localhost:8000/api/rag/query \\
          -H "Content-Type: application/json" \\
          -d '{
            "query": "SQL injection vulnerabilities",
            "top_k": 5,
            "severity_filter": ["HIGH", "CRITICAL"]
          }'
        ```
    """
    try:
        retriever = get_rag_retriever()

        result = retriever.query_general(
            query=request.query,
            top_k=request.top_k,
            severity_filter=request.severity_filter,
            min_cvss=request.min_cvss,
            vendor_filter=request.vendor_filter,
            product_filter=request.product_filter,
            date_start=request.date_start,
            date_end=request.date_end,
        )

        return result

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")  # noqa: B904


@router.post("/scan/{scan_id}/query", response_model=QueryResponse)
async def query_project(scan_id: int, request: ProjectQueryRequest):
    """Query CVEs relevant to a specific project/scan (Project Mode).

    Use cases:
    - "Which CVEs should I prioritize in my React app?"
    - "What are the most critical issues in my dependencies?"
    - "Explain the authentication vulnerabilities affecting my project"

    Examples:
        ```bash
        # First, upload your package.json to get scan_id
        curl -X POST http://localhost:8000/api/scans -F "file=@package.json"

        # Then query about your specific vulnerabilities
        curl -X POST http://localhost:8000/api/rag/scan/42/query \\
          -H "Content-Type: application/json" \\
          -d '{
            "query": "Which vulnerabilities should I prioritize?",
            "top_k": 5
          }'
        ```
    """
    try:
        retriever = get_rag_retriever()

        result = retriever.query_project(
            query=request.query,
            scan_id=scan_id,
            top_k=request.top_k,
            severity_filter=request.severity_filter,
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Project query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Project query failed: {str(e)}")  # noqa: B904


@router.get("/similar/{cve_id}")
async def find_similar(
    cve_id: str,
    top_k: int = Query(5, description="Number of similar CVEs to return", ge=1, le=20),
    exclude_self: bool = Query(True, description="Exclude the reference CVE from results"),
):
    """Find CVEs similar to a given CVE.

    Use cases:
    - "Show me CVEs similar to CVE-2024-1234"
    - "Find related vulnerabilities"

    Examples:
        ```bash
        curl http://localhost:8000/api/rag/similar/CVE-2024-12184?top_k=5
        ```
    """
    try:
        retriever = get_rag_retriever()

        result = retriever.find_similar_cves(cve_id=cve_id, top_k=top_k, exclude_self=exclude_self)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similar CVE search failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Similar CVE search failed: {str(e)}"
        )  # noqa: B904


@router.get("/stats")
async def get_stats():
    """Get statistics about the RAG system.

    Returns:
        Dictionary with system statistics including:
        - Total CVEs in vector store
        - Embedding dimension
        - Model name

    Examples:
        ```bash
        curl http://localhost:8000/api/rag/stats
        ```
    """
    try:
        retriever = get_rag_retriever()
        return retriever.get_stats()

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Stats retrieval failed: {str(e)}"
        )  # noqa: B904


@router.get("/health")
async def health_check():
    """Check if RAG system is healthy and ready.

    Returns:
        Health status with CVE count
    """
    try:
        retriever = get_rag_retriever()
        cve_count = retriever.vector_store.count()

        return {"status": "healthy", "cve_count": cve_count, "ready": cve_count > 0}

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "ready": False}

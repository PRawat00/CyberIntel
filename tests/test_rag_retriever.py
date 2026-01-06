"""Tests for RAG Retriever."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import CVE, Base, Dependency, Scan
from llm_engine.embedder import CVEEmbedder
from llm_engine.rag_retriever import RAGRetriever
from llm_engine.vector_store import CVEVectorStore


@pytest.fixture
def temp_rag_system():
    """Create a temporary RAG system for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        embedder = CVEEmbedder()
        vector_store = CVEVectorStore(persist_directory=str(Path(tmpdir) / "chromadb_test"))
        retriever = RAGRetriever(embedder=embedder, vector_store=vector_store)
        yield retriever, embedder, vector_store


@pytest.fixture
def populated_rag_system(temp_rag_system):
    """Create a RAG system with sample data."""
    retriever, embedder, vector_store = temp_rag_system

    # Sample CVE data
    cve_data = [
        {
            "cve_id": "CVE-2024-SQL-001",
            "description": "SQL injection vulnerability in authentication module allows attackers to bypass login",
            "severity": "CRITICAL",
            "cvss_score": 9.8,
            "vendor": "webapp",
            "product": "auth",
            "published_date": datetime(2024, 1, 15),
        },
        {
            "cve_id": "CVE-2024-XSS-002",
            "description": "Cross-site scripting (XSS) vulnerability in comment system allows script injection",
            "severity": "HIGH",
            "cvss_score": 7.5,
            "vendor": "webapp",
            "product": "comments",
            "published_date": datetime(2024, 2, 20),
        },
        {
            "cve_id": "CVE-2024-RCE-003",
            "description": "Remote code execution in image parser allows arbitrary code execution",
            "severity": "CRITICAL",
            "cvss_score": 9.1,
            "vendor": "imagelib",
            "product": "parser",
            "published_date": datetime(2024, 3, 10),
        },
        {
            "cve_id": "CVE-2024-AUTH-004",
            "description": "Authentication bypass in admin panel due to missing permission checks",
            "severity": "HIGH",
            "cvss_score": 8.5,
            "vendor": "adminpanel",
            "product": "admin",
            "published_date": datetime(2024, 4, 5),
        },
        {
            "cve_id": "CVE-2024-PATH-005",
            "description": "Path traversal vulnerability in file upload allows reading arbitrary files",
            "severity": "MEDIUM",
            "cvss_score": 6.5,
            "vendor": "fileupload",
            "product": "uploader",
            "published_date": datetime(2024, 5, 12),
        },
    ]

    # Generate embeddings and add to vector store
    for cve in cve_data:
        embedding = embedder.embed_cve_description(cve["description"])
        vector_store.add_cve(
            cve_id=cve["cve_id"],
            embedding=embedding,
            description=cve["description"],
            severity=cve["severity"],
            cvss_score=cve["cvss_score"],
            vendor=cve["vendor"],
            product=cve["product"],
            published_date=cve["published_date"],
        )

    yield retriever, embedder, vector_store


@pytest.fixture
def test_db_with_scan():
    """Create test database with scan data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Create CVEs
    cves = [
        CVE(
            cve_id="CVE-2024-SQL-001",
            description="SQL injection vulnerability in authentication module",
            severity="CRITICAL",
            cvss_score=9.8,
            vendor="webapp",
            product="auth",
            published_date=datetime(2024, 1, 15),
            last_modified=datetime(2024, 1, 15),
            source="TEST",
        ),
        CVE(
            cve_id="CVE-2024-XSS-002",
            description="Cross-site scripting vulnerability",
            severity="HIGH",
            cvss_score=7.5,
            vendor="webapp",
            product="comments",
            published_date=datetime(2024, 2, 20),
            last_modified=datetime(2024, 2, 20),
            source="TEST",
        ),
    ]

    for cve in cves:
        session.add(cve)
    session.commit()

    # Create scan
    scan = Scan(
        file_name="package.json",
        file_type="npm",
        scan_date=datetime(2024, 6, 1),
        total_dependencies=2,
        vulnerable_dependencies=2,
        total_cves=2,
        critical_count=1,
        high_count=1,
        medium_count=0,
        low_count=0,
    )
    session.add(scan)
    session.commit()

    # Create dependencies
    deps = [
        Dependency(
            scan_id=scan.id,
            package_name="auth-module",
            version="1.0.0",
            ecosystem="npm",
            is_vulnerable=1,
            cve_count=1,
            highest_severity="CRITICAL",
        ),
        Dependency(
            scan_id=scan.id,
            package_name="comment-system",
            version="2.0.0",
            ecosystem="npm",
            is_vulnerable=1,
            cve_count=1,
            highest_severity="HIGH",
        ),
    ]

    for dep in deps:
        session.add(dep)
    session.commit()

    # Link dependencies to CVEs
    deps[0].cves.append(cves[0])
    deps[1].cves.append(cves[1])
    session.commit()

    yield session, scan.id

    session.close()
    engine.dispose()


class TestRAGRetriever:
    """Test suite for RAGRetriever class."""

    def test_initialization(self, temp_rag_system):
        """Test RAG retriever initialization."""
        retriever, embedder, vector_store = temp_rag_system

        assert retriever is not None
        assert retriever.embedder == embedder
        assert retriever.vector_store == vector_store

    def test_query_general(self, populated_rag_system):
        """Test general query mode."""
        retriever, _, _ = populated_rag_system

        result = retriever.query_general(query="SQL injection vulnerabilities", top_k=3)

        assert result["mode"] == "general"
        assert result["query"] == "SQL injection vulnerabilities"
        assert result["results_count"] > 0
        assert len(result["cves"]) > 0

        # Top result should be SQL injection CVE
        top_cve = result["cves"][0]
        assert "SQL" in top_cve["description"] or "sql" in top_cve["description"].lower()

    def test_query_general_with_severity_filter(self, populated_rag_system):
        """Test general query with severity filtering."""
        retriever, _, _ = populated_rag_system

        result = retriever.query_general(
            query="security vulnerabilities", top_k=10, severity_filter=["CRITICAL"]
        )

        assert result["results_count"] > 0

        # All results should be CRITICAL
        for cve in result["cves"]:
            assert cve["severity"] == "CRITICAL"

    def test_query_general_with_cvss_filter(self, populated_rag_system):
        """Test general query with CVSS filtering."""
        retriever, _, _ = populated_rag_system

        result = retriever.query_general(query="vulnerabilities", top_k=10, min_cvss=8.0)

        assert result["results_count"] > 0

        # All results should have CVSS >= 8.0
        for cve in result["cves"]:
            assert cve["cvss_score"] >= 8.0

    def test_query_general_empty_results(self, temp_rag_system):
        """Test general query with no results."""
        retriever, _, _ = temp_rag_system

        # Empty vector store
        result = retriever.query_general(query="test query", top_k=10)

        assert result["results_count"] == 0
        assert len(result["cves"]) == 0

    def test_query_project_not_implemented_yet(self, populated_rag_system):
        """Test project query mode (basic test - requires database integration)."""
        retriever, _, _ = populated_rag_system

        # This will fail with "Scan not found" since we don't have real database
        result = retriever.query_project(
            query="What affects my project?", scan_id=999, top_k=5  # Non-existent scan
        )

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_find_similar_cves(self, populated_rag_system):
        """Test finding similar CVEs."""
        retriever, _, _ = populated_rag_system

        result = retriever.find_similar_cves(cve_id="CVE-2024-SQL-001", top_k=3, exclude_self=True)

        assert "reference_cve" in result
        assert result["reference_cve"]["cve_id"] == "CVE-2024-SQL-001"
        assert "similar_cves" in result
        assert len(result["similar_cves"]) > 0

        # Should not include reference CVE itself
        for cve in result["similar_cves"]:
            assert cve["cve_id"] != "CVE-2024-SQL-001"

    def test_find_similar_cves_nonexistent(self, populated_rag_system):
        """Test finding similar CVEs for non-existent CVE."""
        retriever, _, _ = populated_rag_system

        result = retriever.find_similar_cves(cve_id="CVE-9999-DOESNOTEXIST", top_k=5)

        assert "error" in result

    def test_get_stats(self, populated_rag_system):
        """Test getting RAG system statistics."""
        retriever, _, _ = populated_rag_system

        stats = retriever.get_stats()

        assert "total_cves" in stats
        assert "embedding_dimension" in stats
        assert "model" in stats

        assert stats["total_cves"] == 5
        assert stats["embedding_dimension"] == 384
        assert "MiniLM" in stats["model"]

    def test_repr(self, populated_rag_system):
        """Test string representation."""
        retriever, _, _ = populated_rag_system

        repr_str = repr(retriever)
        assert "RAGRetriever" in repr_str
        assert "cves=5" in repr_str

    def test_query_general_filters_applied(self, populated_rag_system):
        """Test that filters are correctly applied and reported."""
        retriever, _, _ = populated_rag_system

        # Note: ChromaDB has limitations with multiple combined filters
        # Test with single filter to verify filter tracking
        result = retriever.query_general(
            query="vulnerabilities", top_k=5, severity_filter=["HIGH", "CRITICAL"]
        )

        assert "filters_applied" in result
        filters = result["filters_applied"]

        assert filters["severity"] == ["HIGH", "CRITICAL"]

    def test_query_general_top_k_limit(self, populated_rag_system):
        """Test top_k limit is respected."""
        retriever, _, _ = populated_rag_system

        result = retriever.query_general(query="vulnerabilities", top_k=2)

        # Should return at most 2 results
        assert len(result["cves"]) <= 2

    def test_query_general_relevance_scoring(self, populated_rag_system):
        """Test that results include relevance scores."""
        retriever, _, _ = populated_rag_system

        result = retriever.query_general(query="SQL injection", top_k=3)

        for cve in result["cves"]:
            assert "relevance_score" in cve
            assert 0 <= cve["relevance_score"] <= 1

        # Scores should be in descending order
        if len(result["cves"]) > 1:
            for i in range(len(result["cves"]) - 1):
                assert (
                    result["cves"][i]["relevance_score"] >= result["cves"][i + 1]["relevance_score"]
                )

    def test_similar_cves_similarity_scores(self, populated_rag_system):
        """Test that similar CVEs include similarity scores."""
        retriever, _, _ = populated_rag_system

        result = retriever.find_similar_cves(cve_id="CVE-2024-SQL-001", top_k=3)

        for cve in result["similar_cves"]:
            assert "similarity_score" in cve
            assert 0 <= cve["similarity_score"] <= 1

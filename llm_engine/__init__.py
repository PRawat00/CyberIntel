"""LLM Engine - RAG and semantic search components."""

# Lazy imports to avoid loading heavy dependencies (torch) unnecessarily
__all__ = ["CVEEmbedder", "CVEVectorStore", "RAGRetriever"]


def __getattr__(name):
    """Lazy load modules to avoid import-time dependencies."""
    if name == "CVEEmbedder":
        from llm_engine.embedder import CVEEmbedder

        return CVEEmbedder
    elif name == "CVEVectorStore":
        from llm_engine.vector_store import CVEVectorStore

        return CVEVectorStore
    elif name == "RAGRetriever":
        from llm_engine.rag_retriever import RAGRetriever

        return RAGRetriever
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

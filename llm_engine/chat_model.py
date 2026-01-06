"""Chat model with RAG integration for conversational CVE analysis."""

import logging
import os
from collections.abc import Iterator

from llm_engine.prompts import build_error_prompt, build_general_prompt, build_project_prompt
from llm_engine.providers.xai_provider import XAIProvider
from llm_engine.rag_retriever import RAGRetriever

logger = logging.getLogger(__name__)


def stream_text_with_delay(text: str) -> Iterator[str]:
    """
    Stream text word-by-word for natural typing effect.

    Args:
        text: Full text to stream

    Yields:
        Words with spaces as separate chunks

    Note:
        Delay should be handled by the async WebSocket caller to avoid blocking.
    """
    words = text.split(" ")
    for i, word in enumerate(words):
        # Add space after word (except last word)
        chunk = word if i == len(words) - 1 else word + " "
        yield chunk


class ChatModel:
    """High-level chat interface with RAG integration.

    This class orchestrates:
    1. RAG retrieval to find relevant CVEs
    2. Prompt construction with context
    3. LLM API calls (streaming or non-streaming)
    4. Response formatting
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "grok-4-fast-reasoning",
        rag_retriever: RAGRetriever | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        """Initialize chat model.

        Args:
            api_key: xAI API key (defaults to GROQ_API_KEY env var)
            model_name: Grok model to use
            rag_retriever: RAGRetriever instance (creates new if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        # Get API key
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No API key provided. Set GROQ_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize LLM provider
        self.llm = XAIProvider(
            api_key=self.api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Initialize RAG retriever
        self.rag = rag_retriever or RAGRetriever()

        logger.info(f"ChatModel initialized with {model_name}")

    def chat_general(
        self,
        query: str,
        conversation_history: list[dict[str, str]] | None = None,
        top_k: int = 5,
        stream: bool = False,
        **filters,
    ) -> str | Iterator[str]:
        """Chat about CVEs in general (no specific project).

        Args:
            query: User's question
            conversation_history: Previous messages (list of {"role": "...", "content": "..."})
            top_k: Number of relevant CVEs to retrieve
            stream: Whether to stream the response
            **filters: Additional filters (severity_filter, min_cvss, etc.)

        Returns:
            Generated response text (or iterator if stream=True)
        """
        try:
            # Detect intent to determine if RAG lookup is needed
            from llm_engine.intent_detector import detect_intent, get_greeting_response

            intent = detect_intent(query)
            logger.info(f"General query: '{query}' (intent: {intent})")

            # Handle greetings without RAG lookup
            if intent == "greeting":
                greeting = get_greeting_response()
                if stream:
                    # Stream word-by-word (delay handled by WebSocket handler)
                    return stream_text_with_delay(greeting)
                else:
                    return greeting

            # For security queries, do full RAG retrieval
            # For general queries, retrieve but with lower relevance threshold
            rag_results = self.rag.query_general(
                query=query, top_k=top_k if intent == "security_query" else 3, **filters
            )

            relevant_cves = rag_results.get("cves", [])
            logger.debug(f"Retrieved {len(relevant_cves)} relevant CVEs")

            # Build prompt with context
            messages = build_general_prompt(
                query=query,
                relevant_cves=relevant_cves,
                conversation_history=conversation_history,
                intent=intent,
            )

            # Generate response
            if stream:
                try:
                    return self.llm.generate_stream(messages)
                except Exception as stream_init_error:
                    logger.error(
                        f"Stream initialization failed: {stream_init_error}", exc_info=True
                    )
                    return iter([build_error_prompt("api_error")])
            else:
                return self.llm.generate(messages)

        except Exception as e:
            logger.error(f"Chat general failed: {e}", exc_info=True)
            if stream:
                return iter([build_error_prompt("api_error")])
            else:
                return build_error_prompt("api_error")

    def chat_project(
        self,
        query: str,
        scan_id: int,
        selected_dependencies: list | None = None,
        inject_dependencies: bool = True,
        context_injected: bool = False,
        conversation_history: list[dict[str, str]] | None = None,
        top_k: int = 5,
        stream: bool = False,
        **filters,
    ) -> str | Iterator[str]:
        """Chat about vulnerabilities in a specific project.

        Args:
            query: User's question about their project
            scan_id: ID of the scanned project
            selected_dependencies: Optional list of Dependency objects to focus on
            inject_dependencies: Whether to inject dependency context (smart conditional injection)
            context_injected: Whether full dependency context has already been injected
            conversation_history: Previous messages
            top_k: Number of relevant CVEs to retrieve
            stream: Whether to stream the response
            **filters: Additional filters

        Returns:
            Generated response text (or iterator if stream=True)
        """
        try:
            # Retrieve project-specific CVEs (optionally filtered to selected dependencies)
            dep_info = ""
            if selected_dependencies and inject_dependencies:
                dep_info = (
                    f" (injecting context for {len(selected_dependencies)} selected dependencies)"
                )
            elif selected_dependencies and not inject_dependencies:
                dep_info = " (dependencies selected but context NOT injected)"
            logger.info(f"Project query for scan {scan_id}{dep_info}: '{query}'")

            # SMART RETRIEVAL: If dependencies are selected and should be injected,
            # skip vector search and use CVEs directly from dependency objects
            if selected_dependencies and inject_dependencies:
                logger.info(
                    f"Using direct CVE retrieval for {len(selected_dependencies)} selected dependencies (bypassing RAG)"
                )

                # Extract CVEs directly from dependency objects (already loaded with selectinload!)
                relevant_cves = []
                seen_cve_ids = set()

                for dep in selected_dependencies:
                    for cve in dep.cves:
                        if cve.cve_id not in seen_cve_ids:
                            relevant_cves.append(
                                {
                                    "cve_id": cve.cve_id,
                                    "description": cve.description,
                                    "severity": cve.severity,
                                    "cvss_score": cve.cvss_score,
                                    "vendor": cve.vendor,
                                    "product": cve.product,
                                    "published_date": (
                                        cve.published_date.isoformat()
                                        if cve.published_date
                                        else None
                                    ),
                                    "affects_packages": [f"{dep.package_name}@{dep.version}"],
                                }
                            )
                            seen_cve_ids.add(cve.cve_id)

                # Build scan_info structure
                vulnerable_count = sum(1 for d in selected_dependencies if d.is_vulnerable)
                scan_info = {
                    "file_name": f"Selected Dependencies ({len(selected_dependencies)})",
                    "file_type": "selected",
                    "total_dependencies": len(selected_dependencies),
                    "vulnerable_dependencies": vulnerable_count,
                    "total_cves": len(relevant_cves),
                }

                # Build RAG results structure
                rag_results = {"cves": relevant_cves, "scan_info": scan_info}

                logger.info(
                    f"Direct retrieval found {len(relevant_cves)} CVEs for selected dependencies"
                )
            else:
                # Normal RAG retrieval with vector search
                rag_results = self.rag.query_project(
                    query=query,
                    scan_id=scan_id,
                    dependency_filter=selected_dependencies,
                    top_k=top_k,
                    **filters,
                )

            # Handle errors from RAG
            if "error" in rag_results:
                error_msg = build_error_prompt("no_scan")
                if stream:
                    return iter([error_msg])
                else:
                    return error_msg

            relevant_cves = rag_results.get("cves", [])
            scan_info = rag_results.get("scan_info", {})

            logger.debug(f"Retrieved {len(relevant_cves)} relevant CVEs for project")

            # Handle case with no vulnerabilities
            if not relevant_cves:
                error_msg = build_error_prompt("no_cves")
                if stream:
                    return iter([error_msg])
                else:
                    return error_msg

            # Build prompt with project context (and optional dependency focus)
            # Only inject dependency context if inject_dependencies=True (smart conditional injection)
            deps_to_inject = selected_dependencies if inject_dependencies else None

            messages = build_project_prompt(
                query=query,
                scan_info=scan_info,
                relevant_cves=relevant_cves,
                selected_dependencies=deps_to_inject,
                context_injected=context_injected,
                conversation_history=conversation_history,
            )

            # Generate response
            if stream:
                try:
                    return self.llm.generate_stream(messages)
                except Exception as stream_init_error:
                    logger.error(
                        f"Stream initialization failed: {stream_init_error}", exc_info=True
                    )
                    return iter([build_error_prompt("api_error")])
            else:
                return self.llm.generate(messages)

        except Exception as e:
            logger.error(f"Chat project failed: {e}", exc_info=True)
            error_msg = build_error_prompt("api_error")
            if stream:
                return iter([error_msg])
            else:
                return error_msg

    def get_usage_stats(self) -> dict:
        """Get token usage statistics.

        Returns:
            Dictionary with usage stats and estimated cost
        """
        return self.llm.get_usage_stats()

    def reset_usage_stats(self):
        """Reset token usage counters."""
        self.llm.reset_usage_stats()

    def __repr__(self) -> str:
        return f"ChatModel(llm={self.llm}, rag_cves={self.rag.vector_store.count()})"

"""
Unified Chat Model - Single interface for all chat interactions.

Replaces the dual-path architecture (chat_general/chat_project) with a flexible,
context-aware system that automatically selects appropriate retrieval strategies.
"""

import logging
import os
from collections.abc import Iterator
from typing import Any

from llm_engine.chat_context import ChatContext, RetrievalResult
from llm_engine.intent_detector import detect_intent
from llm_engine.llm_router import get_llm_router
from llm_engine.prompts import SYSTEM_PROMPT
from llm_engine.providers.xai_provider import XAIProvider
from llm_engine.strategies.direct_dependency_strategy import DirectDependencyStrategy
from llm_engine.strategies.general_cve_strategy import GeneralCVEStrategy

logger = logging.getLogger(__name__)


class UnifiedChatModel:
    """
    Unified chat interface with dynamic strategy selection.

    This class:
    1. Uses IntentRouter to select appropriate retrieval strategies
    2. Executes strategies to gather CVE context
    3. Builds prompts based on context type
    4. Calls LLM with or without streaming
    5. Returns formatted responses
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "grok-4-fast-reasoning",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize unified chat model.

        Args:
            api_key: xAI API key (defaults to GROQ_API_KEY env var)
            model_name: Grok model to use
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

        # Initialize LLM router (replaces keyword-based intent router)
        self.llm_router = get_llm_router()

        logger.info(f"UnifiedChatModel initialized with {model_name} and LLM routing")

    def chat(
        self, query: str, context: ChatContext, stream: bool = False, **kwargs
    ) -> str | Iterator[str]:
        """
        Main chat interface - handles all query types.

        Args:
            query: User's question
            context: Current chat context
            stream: Whether to stream the response
            **kwargs: Additional parameters:
                - top_k: Number of CVEs to retrieve (default: 5)
                - filters: Additional filters for retrieval

        Returns:
            Response string or iterator of response chunks
        """
        logger.info(f"UnifiedChatModel.chat: '{query[:50]}...'")

        try:
            # 1. Intent Detection (keep for greeting detection)
            intent = detect_intent(query)
            logger.info(f"Detected intent: {intent}")

            # Handle greetings directly (no retrieval needed)
            if intent == "greeting":
                messages = self._build_greeting_prompt(query, context)
                return self._generate(messages, stream)

            # 2. Deterministic routing for selected dependencies
            # If user has selected dependencies, ALWAYS use them (no LLM routing needed)
            if context.has_dependency_context():
                logger.info(
                    f"Selected dependencies detected ({len(context.dependencies)} deps), "
                    f"using DIRECT_DEPENDENCIES strategy (bypassing LLM router)"
                )
                strategies = [DirectDependencyStrategy()]
            else:
                # 3. LLM-Based Strategy Selection (for general queries, attack chains, etc.)
                routing_decision = self.llm_router.route(query, context, **kwargs)
                logger.info(
                    f"LLM Router decision: {routing_decision.strategies} "
                    f"(reasoning: {routing_decision.reasoning[:100]}...)"
                )

                # 4. Map strategy names to strategy instances
                strategy_map = {
                    "DIRECT_DEPENDENCIES": DirectDependencyStrategy(),
                    "VECTOR_SEARCH": GeneralCVEStrategy(),
                }

                strategies = [
                    strategy_map[name]
                    for name in routing_decision.strategies
                    if name in strategy_map
                ]

            # 4. Retrieval
            if strategies:
                retrieval_result = self._execute_strategies(query, context, strategies, **kwargs)
            else:
                # No strategies (e.g., pure conversation)
                retrieval_result = RetrievalResult(strategy_name="none", query=query, cves=[])

            # 4. Prompt Building
            messages = self._build_prompt(query, context, retrieval_result)

            # 5. Generation
            return self._generate(messages, stream)

        except Exception as e:
            logger.error(f"UnifiedChatModel.chat failed: {e}", exc_info=True)
            error_message = f"I encountered an error while processing your question: {str(e)}"
            if stream:
                return iter([error_message])
            return error_message

    def _execute_strategies(
        self, query: str, context: ChatContext, strategies: list, **kwargs
    ) -> RetrievalResult:
        """
        Execute retrieval strategies and merge results.

        Args:
            query: User query
            context: Chat context
            strategies: List of strategy instances
            **kwargs: Parameters for strategies

        Returns:
            Merged RetrievalResult
        """
        if not strategies:
            return RetrievalResult(strategy_name="empty", query=query, cves=[])

        if len(strategies) == 1:
            # Single strategy - execute directly
            return strategies[0].retrieve(query, context, **kwargs)

        # Multiple strategies - execute and merge
        results = []
        for strategy in strategies:
            try:
                result = strategy.retrieve(query, context, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Strategy {strategy.get_name()} failed: {e}", exc_info=True)

        if not results:
            return RetrievalResult(
                strategy_name="failed",
                query=query,
                cves=[],
                metadata={"error": "All strategies failed"},
            )

        # Merge all results
        merged = results[0]
        for result in results[1:]:
            merged = merged.merge_with(result)

        return merged

    def _build_prompt(
        self, query: str, context: ChatContext, retrieval_result: RetrievalResult
    ) -> list[dict[str, str]]:
        """
        Build prompt messages based on query, context, and retrieval results.

        Args:
            query: User query
            context: Chat context
            retrieval_result: Results from retrieval strategies

        Returns:
            List of message dictionaries for LLM
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history
        if context.conversation_history:
            messages.extend(context.conversation_history)

        # Build user message with CVE context if available
        if retrieval_result.cves:
            cve_context = self._format_cve_context(
                retrieval_result.cves, retrieval_result.scan_info, retrieval_result.dependency_info
            )
            user_message = f"""Based on the following information, please answer this question:

{query}

Relevant Information:
{cve_context}

Please provide a helpful, actionable response."""
        else:
            # No CVEs - just the query
            user_message = query

        messages.append({"role": "user", "content": user_message})
        return messages

    def _build_greeting_prompt(self, query: str, context: ChatContext) -> list[dict[str, str]]:
        """Build prompt for greeting (no CVE context)."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history
        if context.conversation_history:
            messages.extend(context.conversation_history)

        messages.append({"role": "user", "content": query})
        return messages

    def _format_cve_context(
        self,
        cves: list[dict[str, Any]],
        scan_info: dict | None = None,
        dependency_info: list[dict] | None = None,
    ) -> str:
        """
        Format CVEs and context into readable text.

        Args:
            cves: List of CVE dictionaries
            scan_info: Optional scan information
            dependency_info: Optional dependency information

        Returns:
            Formatted context string
        """
        lines = []

        # Add scan info if available
        if scan_info:
            lines.append(f"Project: {scan_info.get('file_name', 'Unknown')}")
            lines.append(f"Scan Date: {scan_info.get('created_at', 'Unknown')}")
            lines.append("")

        # Add dependency info if available
        if dependency_info:
            lines.append("Selected Dependencies:")
            for dep in dependency_info:
                lines.append(
                    f"  - {dep['package_name']} @ {dep['version']} "
                    f"({dep.get('severity', 'UNKNOWN')}) - {dep.get('cve_count', 0)} CVEs"
                )
            lines.append("")

        # Add CVEs
        if cves:
            lines.append(f"Vulnerabilities ({len(cves)} total):")
            for i, cve in enumerate(cves[:10], 1):  # Limit to top 10
                severity = cve.get("severity", "UNKNOWN")
                cvss = cve.get("cvss_score", "N/A")
                cve_id = cve.get("cve_id", "Unknown")
                desc = cve.get("description", "No description")[:200]

                lines.append(f"\n{i}. {cve_id} ({severity}, CVSS: {cvss})")
                lines.append(f"   {desc}...")

                if "affects_packages" in cve:
                    lines.append(f"   Affects: {', '.join(cve['affects_packages'])}")

        return "\n".join(lines)

    def _generate(self, messages: list[dict[str, str]], stream: bool) -> str | Iterator[str]:
        """
        Generate response from LLM.

        Args:
            messages: Messages for LLM
            stream: Whether to stream

        Returns:
            Response string or iterator
        """
        if stream:
            return self.llm.generate_stream(messages)
        else:
            return self.llm.generate(messages)


# Singleton instance
_unified_model_instance = None


def get_unified_chat_model() -> UnifiedChatModel:
    """Get the global unified chat model instance."""
    global _unified_model_instance
    if _unified_model_instance is None:
        _unified_model_instance = UnifiedChatModel()
    return _unified_model_instance

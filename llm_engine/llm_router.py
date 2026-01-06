"""
LLM-Based Router for intelligent strategy selection.

Replaces keyword-based intent detection with LLM reasoning to decide
which retrieval strategies to use for each query.
"""

import json
import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

from llm_engine.chat_context import ChatContext
from llm_engine.providers.xai_provider import XAIProvider

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Represents the LLM's routing decision."""

    strategies: list[str]  # List of strategy names to execute
    reasoning: str  # LLM's explanation for the decision
    confidence: float = 1.0  # Confidence in the decision (0-1)


# Routing system prompt
ROUTING_SYSTEM_PROMPT = """You are a routing assistant for a cybersecurity vulnerability analysis system.

Your job is to intelligently decide which data retrieval strategies to use based on the user's query and available context.

AVAILABLE STRATEGIES:

1. DIRECT_DEPENDENCIES - Direct database retrieval from selected dependencies

   WHAT IT DOES:
   - Retrieves ALL CVEs affecting the selected dependencies via database relationships
   - Bypasses vector search entirely - no embeddings, no semantic matching
   - Returns 100% of known vulnerabilities for selected packages

   DATA CHARACTERISTICS:
   - Speed: FASTEST (direct SQL query, no vector operations)
   - Precision: 100% accurate for selected dependencies
   - Coverage: Complete vulnerability list for selected packages
   - No false positives or irrelevant results

   USE WHEN:
   - User refers to selected, chosen, or current dependencies
   - User asks about specific packages that are selected
   - User wants comprehensive vulnerability list for their dependencies
   - User asks questions like "what's wrong with my packages", "tell me about these vulnerabilities"

   EXAMPLES:
   - "tell me about the selected packages"
   - "what vulnerabilities affect my dependencies?"
   - "show me all CVEs for the chosen packages"
   - "are these dependencies safe?"

2. VECTOR_SEARCH - Semantic search across entire CVE database

   WHAT IT DOES:
   - Searches across ALL CVEs in database using semantic similarity
   - Matches query to CVE descriptions using vector embeddings
   - Returns top-K most relevant CVEs regardless of dependency selection

   DATA CHARACTERISTICS:
   - Speed: SLOWER (requires embedding generation + vector similarity search)
   - Precision: Variable (depends on query quality and embedding match)
   - Coverage: Entire CVE database (not limited to selected dependencies)
   - May return irrelevant results if query is vague

   USE WHEN:
   - User asks general security questions or concepts
   - User wants to learn about vulnerability types (XSS, SQL injection, etc.)
   - User searches for specific CVE by ID (CVE-2024-1234)
   - User asks about security topics not related to their dependencies
   - No dependencies are selected

   EXAMPLES:
   - "what is cross-site scripting?"
   - "explain CVE-2024-1234"
   - "what are common web vulnerabilities?"
   - "how does SQL injection work?"

3. BOTH - Combine both strategies and merge results

   WHAT IT DOES:
   - Executes BOTH DIRECT_DEPENDENCIES and VECTOR_SEARCH
   - Merges results (deduplicates CVEs, combines context)
   - Provides comprehensive answer with both specific and general context

   DATA CHARACTERISTICS:
   - Speed: SLOWEST (runs both strategies sequentially)
   - Precision: High for dependencies + semantic match for general info
   - Coverage: Selected dependencies + broader security context

   USE WHEN:
   - User needs context from BOTH their dependencies AND general knowledge
   - User asks comparative questions (comparing their vulnerabilities to industry)
   - User wants to understand if their issues are common/unique
   - Query requires both specific CVE details and general security concepts

   EXAMPLES:
   - "how do these compare to industry standards?"
   - "are these vulnerabilities common?"
   - "what's the difference between my CVEs and typical web app vulnerabilities?"

SEMANTIC REASONING GUIDELINES:

- Focus on USER INTENT, not just keywords
- Consider the conversation context (is this a follow-up question?)
- If user refers to "my", "our", "these", "the", "current", "selected", "chosen" packages/libraries/dependencies → DIRECT_DEPENDENCIES
- If user explicitly mentions "selected" or "chosen" → ALWAYS use DIRECT_DEPENDENCIES
- If user asks "what is", "explain", "define", "tell me about [concept]" → VECTOR_SEARCH
- If user asks "how common", "compare", "industry" → BOTH
- When in doubt: prefer DIRECT_DEPENDENCIES if any dependencies are selected (they likely want info about their selection)

EDGE CASES:

- Dependencies ARE selected + user says "selected/chosen/these dependencies" → ALWAYS DIRECT_DEPENDENCIES (highest priority)
- Dependencies ARE selected + vague question like "tell me about them" → DIRECT_DEPENDENCIES
- No dependencies selected + asks about "my packages" → VECTOR_SEARCH (user is confused, provide general info)
- No dependencies selected + general question → VECTOR_SEARCH
- Dependencies selected but asks unrelated question (e.g., "what is XSS?") → VECTOR_SEARCH
- Follow-up question referring to previous answer → Use same strategy as previous (if unclear, use DIRECT_DEPENDENCIES)

You must respond with ONLY valid JSON in this exact format:
{
  "strategies": ["DIRECT_DEPENDENCIES"],
  "reasoning": "User asking about selected packages with references to 'these vulnerabilities', need direct CVE lookup from dependencies"
}"""


class LLMRouter:
    """
    LLM-based router that uses AI to decide which retrieval strategies to use.

    Replaces keyword-based intent detection with intelligent reasoning.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "grok-4-fast-reasoning",
        temperature: float = 0.0,  # Low temperature for consistent routing
    ):
        """
        Initialize LLM router.

        Args:
            api_key: xAI API key (defaults to GROQ_API_KEY env var)
            model_name: Grok model to use for routing
            temperature: Sampling temperature (0 for deterministic)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("No API key provided for LLM routing")

        self.llm = XAIProvider(
            api_key=self.api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=200,  # Short responses for routing
        )

        # Rate limiting: Track routing calls per session
        self.rate_limiter: dict[int, list[datetime]] = {}
        self.rate_limit_lock = threading.Lock()
        self.max_calls_per_minute = 10  # Maximum routing calls per session per minute

        logger.info(f"LLMRouter initialized with {model_name}")

    def _check_rate_limit(self, session_id: int) -> bool:
        """
        Check if session has exceeded rate limit for routing calls.

        Args:
            session_id: Chat session ID

        Returns:
            True if within rate limit, False if exceeded
        """
        with self.rate_limit_lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(minutes=1)

            # Clean old entries from rate limiter
            self.rate_limiter = {
                sid: [ts for ts in timestamps if ts > cutoff]
                for sid, timestamps in self.rate_limiter.items()
                if any(ts > cutoff for ts in timestamps)
            }

            # Check current session
            if session_id not in self.rate_limiter:
                self.rate_limiter[session_id] = []

            recent_calls = self.rate_limiter[session_id]

            if len(recent_calls) >= self.max_calls_per_minute:
                logger.warning(
                    f"SECURITY: Rate limit exceeded for session {session_id}: "
                    f"{len(recent_calls)} calls in last minute"
                )
                return False

            # Add current call
            self.rate_limiter[session_id].append(now)
            return True

    def route(self, query: str, context: ChatContext, **kwargs) -> RoutingDecision:
        """
        Use LLM to decide which retrieval strategies to execute.

        Args:
            query: User's query
            context: Current chat context
            **kwargs: Additional parameters

        Returns:
            RoutingDecision with strategy names and reasoning
        """
        logger.info(f"LLMRouter: Routing query '{query[:50]}...'")

        # Check rate limit first
        if not self._check_rate_limit(context.session_id):
            logger.warning(f"Rate limit exceeded for session {context.session_id}, using fallback")
            fallback_strategies = (
                ["DIRECT_DEPENDENCIES"] if context.has_dependency_context() else ["VECTOR_SEARCH"]
            )
            return RoutingDecision(
                strategies=fallback_strategies,
                reasoning="Rate limit exceeded, using default strategy",
                confidence=0.5,
            )

        try:
            # Build routing prompt
            prompt = self._build_routing_prompt(query, context)

            # Call LLM for routing decision with short timeout (routing should be fast)
            messages = [
                {"role": "system", "content": ROUTING_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]

            # SECURITY: Use shorter timeout for routing (10s) to prevent DoS
            response = self.llm.generate(messages, timeout=10.0)

            # Parse JSON response
            decision = self._parse_routing_response(response)

            logger.info(
                f"LLMRouter decision: strategies={decision.strategies}, "
                f"reasoning='{decision.reasoning[:50]}...'"
            )

            return decision

        except Exception as e:
            logger.error(f"LLMRouter failed: {e}", exc_info=True)
            # Fallback: use DIRECT_DEPENDENCIES if available, else VECTOR_SEARCH
            fallback_strategies = (
                ["DIRECT_DEPENDENCIES"] if context.has_dependency_context() else ["VECTOR_SEARCH"]
            )

            # SECURITY: Never expose error details that might contain API keys or internal info
            safe_error_message = "Routing service temporarily unavailable, using fallback strategy"

            return RoutingDecision(
                strategies=fallback_strategies, reasoning=safe_error_message, confidence=0.5
            )

    def _sanitize_query_for_prompt(self, query: str) -> str:
        """
        Sanitize user query to prevent prompt injection attacks.

        Args:
            query: Raw user query

        Returns:
            Sanitized query safe for embedding in prompts
        """
        # Limit length to prevent abuse
        sanitized = query[:500]

        # Replace quotes to prevent breaking out of query context
        sanitized = sanitized.replace('"', "'")
        sanitized = sanitized.replace("`", "'")

        # Remove newlines that could inject new instructions
        sanitized = sanitized.replace("\n", " ")
        sanitized = sanitized.replace("\r", " ")

        # Remove common prompt injection patterns
        injection_patterns = [
            "IGNORE ALL PREVIOUS",
            "IGNORE PREVIOUS",
            "DISREGARD ALL",
            "FORGET",
            "NEW INSTRUCTIONS",
            "SYSTEM:",
            "ASSISTANT:",
            "<|im_start|>",
            "<|im_end|>",
        ]

        sanitized_upper = sanitized.upper()
        for pattern in injection_patterns:
            if pattern in sanitized_upper:
                # Replace with safe placeholder
                start_idx = sanitized_upper.find(pattern)
                end_idx = start_idx + len(pattern)
                sanitized = sanitized[:start_idx] + "[FILTERED]" + sanitized[end_idx:]
                sanitized_upper = sanitized.upper()

        return sanitized.strip()

    def _build_routing_prompt(self, query: str, context: ChatContext) -> str:
        """Build the routing prompt with query and context information."""
        # Sanitize query to prevent prompt injection
        sanitized_query = self._sanitize_query_for_prompt(query)
        lines = [f"USER QUERY: {sanitized_query}\n"]

        # Add context information
        lines.append("AVAILABLE CONTEXT:")

        # Selected dependencies - include actual package names for better routing
        if context.has_dependency_context():
            lines.append(
                f"- Selected Dependencies: {len(context.dependencies)} package(s) selected"
            )

            # Fetch actual package names from database WITH USER VALIDATION
            try:
                from database.db import get_db_session
                from database.models import Dependency, Scan

                with get_db_session() as session:
                    # SECURITY: First get user's scan IDs to enforce user isolation
                    user_scans = (
                        session.query(Scan.id).filter(Scan.user_id == context.user_id).all()
                    )
                    user_scan_ids = [s.id for s in user_scans]

                    if not user_scan_ids:
                        logger.warning(f"No scans found for user {context.user_id}")
                    else:
                        # Only fetch dependencies that belong to user's scans
                        deps = (
                            session.query(Dependency)
                            .filter(Dependency.id.in_(context.dependencies))
                            .filter(Dependency.scan_id.in_(user_scan_ids))  # USER ISOLATION!
                            .all()
                        )

                        if deps:
                            lines.append("  Packages:")
                            for dep in deps:
                                lines.append(
                                    f"    • {dep.package_name} ({dep.version}) - {dep.ecosystem}"
                                )
                        elif len(context.dependencies) > 0:
                            # Dependencies exist but don't belong to user - security issue
                            logger.warning(
                                f"SECURITY: User {context.user_id} attempted to access "
                                f"{len(context.dependencies)} dependencies not owned by them"
                            )
            except Exception as e:
                logger.error(f"Failed to fetch dependency names for routing: {e}", exc_info=True)
                # Continue without package names if query fails
        else:
            lines.append("- Selected Dependencies: None")

        # Scan context
        if context.has_scan_context():
            lines.append(f"- Project Scan: {len(context.scans)} scan(s) available")
        else:
            lines.append("- Project Scan: None")

        lines.append("\nDecide which strategies to use and respond with JSON.")

        return "\n".join(lines)

    def _parse_routing_response(self, response: str) -> RoutingDecision:
        """
        Parse LLM's JSON response into RoutingDecision.

        Args:
            response: Raw LLM response (should be JSON)

        Returns:
            RoutingDecision object
        """
        try:
            # Try to extract JSON from response (in case LLM adds extra text)
            response = response.strip()

            # Find JSON object in response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found in response")

            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)

            # Validate required fields
            if "strategies" not in data:
                raise ValueError("Missing 'strategies' field in response")

            strategies = data["strategies"]
            reasoning = data.get("reasoning", "No reasoning provided")

            # Validate strategies
            valid_strategies = {"DIRECT_DEPENDENCIES", "VECTOR_SEARCH", "BOTH"}
            if not isinstance(strategies, list):
                strategies = [strategies]

            # Expand "BOTH" into both strategies
            if "BOTH" in strategies:
                strategies = ["DIRECT_DEPENDENCIES", "VECTOR_SEARCH"]

            # Filter to valid strategies
            strategies = [s for s in strategies if s in valid_strategies]

            if not strategies:
                # Fallback to vector search if no valid strategies
                strategies = ["VECTOR_SEARCH"]
                reasoning += " (fallback to VECTOR_SEARCH due to invalid strategy)"

            return RoutingDecision(strategies=strategies, reasoning=reasoning, confidence=1.0)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse routing response as JSON: {e}")
            logger.error(f"Response was: {response}")
            raise ValueError(f"Invalid JSON in routing response: {e}")  # noqa: B904
        except Exception as e:
            logger.error(f"Error parsing routing response: {e}")
            raise


# Global instance
_llm_router_instance = None


def get_llm_router() -> LLMRouter:
    """Get the global LLM router instance."""
    global _llm_router_instance
    if _llm_router_instance is None:
        _llm_router_instance = LLMRouter()
    return _llm_router_instance

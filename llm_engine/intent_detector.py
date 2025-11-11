"""
Intent detection for chat messages.
Determines whether a message is a greeting, security query, or general question.
Also provides dependency-specific relevance detection for smart context injection.
"""

import logging
import re
from typing import Literal

logger = logging.getLogger(__name__)

IntentType = Literal["greeting", "security_query", "general"]


def detect_intent(message: str) -> IntentType:
    """
    Detect the intent of a user message.

    Args:
        message: The user's message

    Returns:
        "greeting" - Casual greeting or acknowledgment
        "security_query" - Specific security/CVE question
        "general" - General question not requiring deep CVE lookup
    """
    message_lower = message.lower().strip()

    # Greeting patterns
    greeting_patterns = [
        r"^(hi|hello|hey|greetings|good morning|good afternoon|good evening)$",
        r"^(hi|hello|hey|greetings|good morning|good afternoon|good evening)[!.,\s]*$",
        r"^thanks?[!.,\s]*$",
        r"^thank you[!.,\s]*$",
        r"^ok[ay]*[!.,\s]*$",
        r"^cool[!.,\s]*$",
        r"^bye[!.,\s]*$",
        r"^goodbye[!.,\s]*$",
        r"^see you[!.,\s]*$",
    ]

    for pattern in greeting_patterns:
        if re.match(pattern, message_lower):
            return "greeting"

    # Security query keywords
    security_keywords = [
        "cve",
        "vulnerability",
        "vulnerabilities",
        "exploit",
        "security",
        "patch",
        "fix",
        "remediat",
        "attack",
        "threat",
        "risk",
        "dependency",
        "dependencies",
        "package",
        "upgrade",
        "version",
        "critical",
        "severity",
        "cvss",
        "malicious",
    ]

    # Check if message contains security keywords
    for keyword in security_keywords:
        if keyword in message_lower:
            return "security_query"

    # Check for CVE ID pattern (CVE-YYYY-NNNNN)
    if re.search(r"cve-\d{4}-\d{4,7}", message_lower):
        return "security_query"

    # Default to general for other questions
    return "general"


def get_greeting_response() -> str:
    """
    Return a friendly greeting response.

    Returns:
        A natural greeting message
    """
    return (
        "Hi! I'm SecureChat, your AI security assistant. "
        "I can help you understand CVE vulnerabilities, analyze security risks, "
        "and suggest remediation steps. What would you like to know?"
    )


def get_acknowledgment_response() -> str:
    """
    Return an acknowledgment for thanks/bye messages.

    Returns:
        A friendly acknowledgment
    """
    return "You're welcome! Feel free to ask if you have any other security questions."


# ============================================================================
# Dependency-Specific Intent Detection
# ============================================================================


class IntentDetectionResult:
    """Result of dependency-specific intent detection analysis."""

    def __init__(
        self, is_relevant: bool, confidence: float, matched_entities: list[str], reasoning: str
    ):
        self.is_relevant = is_relevant
        self.confidence = confidence  # 0.0 to 1.0
        self.matched_entities = matched_entities  # Package names, CVE IDs, etc.
        self.reasoning = reasoning  # Explanation for logging/debugging

    def __repr__(self):
        return (
            f"IntentDetectionResult(relevant={self.is_relevant}, "
            f"confidence={self.confidence:.2f}, "
            f"entities={self.matched_entities}, "
            f"reasoning='{self.reasoning}')"
        )


class DependencyIntentDetector:
    """
    Detects if a user query is about selected dependencies.

    Uses keyword matching, entity recognition, and pattern analysis
    to determine query relevance with high accuracy and low latency.
    """

    # Keywords indicating dependency-specific queries
    DEPENDENCY_KEYWORDS = {
        "selected",
        "chosen",
        "these",
        "this",
        "current",
        "packages",
        "dependencies",
        "libs",
        "libraries",
        "upgrade",
        "update",
        "fix",
        "patch",
        "remediate",
        "vulnerable",
        "vulnerabilities",
        "issues",
        "problems",
        "affected",
        "impacted",
        "risk",
        "risks",
        "should i",
        "what about",
        "how to fix",
        "recommend",
    }

    # Keywords suggesting general/broad queries (not about specific selection)
    GENERAL_KEYWORDS = {
        "what is",
        "explain",
        "define",
        "tell me about",
        "how does",
        "why does",
        "in general",
        "typically",
    }

    # Security-related terms (higher weight)
    SECURITY_TERMS = {
        "cve",
        "exploit",
        "vulnerability",
        "security",
        "critical",
        "high",
        "severity",
        "cvss",
        "malicious",
        "attack",
        "breach",
        "compromise",
    }

    def __init__(self):
        """Initialize the intent detector."""
        pass

    def detect_intent(
        self,
        query: str,
        selected_dependencies: list | None = None,
        conversation_history: list | None = None,
    ) -> IntentDetectionResult:
        """
        Detect if query is relevant to selected dependencies.

        Args:
            query: User's question/message
            selected_dependencies: List of Dependency objects currently selected
            conversation_history: Previous messages for context

        Returns:
            IntentDetectionResult with relevance determination
        """
        if not query or not query.strip():
            return IntentDetectionResult(
                is_relevant=False, confidence=0.0, matched_entities=[], reasoning="Empty query"
            )

        query_lower = query.lower()

        # If no dependencies selected, query can't be about them
        if not selected_dependencies or len(selected_dependencies) == 0:
            return IntentDetectionResult(
                is_relevant=False,
                confidence=1.0,
                matched_entities=[],
                reasoning="No dependencies selected",
            )

        # Track signals for relevance
        signals = []
        matched_entities = []
        confidence_score = 0.0

        # 1. Check for explicit package name mentions
        package_names = [dep.package_name.lower() for dep in selected_dependencies]
        for pkg_name in package_names:
            if pkg_name in query_lower:
                signals.append(f"Explicit package mention: {pkg_name}")
                matched_entities.append(pkg_name)
                confidence_score += 0.4

        # 2. Check for CVE IDs from selected dependencies
        cve_ids = []
        for dep in selected_dependencies:
            if hasattr(dep, "cves") and dep.cves:
                cve_ids.extend([cve.cve_id for cve in dep.cves])

        for cve_id in cve_ids:
            if cve_id.lower() in query_lower:
                signals.append(f"CVE ID mention: {cve_id}")
                matched_entities.append(cve_id)
                confidence_score += 0.3

        # 3. Check for dependency-specific keywords
        dep_keyword_count = 0
        for keyword in self.DEPENDENCY_KEYWORDS:
            if keyword in query_lower:
                dep_keyword_count += 1
                signals.append(f"Dependency keyword: '{keyword}'")
                confidence_score += 0.15

        # 4. Check for security terms (increases relevance if other signals present)
        security_term_count = 0
        for term in self.SECURITY_TERMS:
            if term in query_lower:
                security_term_count += 1
                confidence_score += 0.1

        if security_term_count > 0:
            signals.append(f"Security terms: {security_term_count}")

        # 5. Check for general query indicators (reduces relevance)
        general_indicator_count = 0
        for keyword in self.GENERAL_KEYWORDS:
            if keyword in query_lower:
                general_indicator_count += 1
                confidence_score -= 0.2

        if general_indicator_count > 0:
            signals.append(f"General query indicators: {general_indicator_count}")

        # 6. Pronoun/demonstrative references ("these", "this", "them")
        pronouns = ["these", "this", "them", "those", "it"]
        pronoun_count = sum(1 for p in pronouns if re.search(rf"\b{p}\b", query_lower))
        if pronoun_count > 0:
            signals.append(f"Demonstrative pronouns: {pronoun_count}")
            confidence_score += 0.2

        # 7. Check conversation context (if available)
        if conversation_history:
            # If recent messages mentioned dependencies, this might be a follow-up
            recent_messages = (
                conversation_history[-3:]
                if len(conversation_history) >= 3
                else conversation_history
            )
            for msg in recent_messages:
                msg_lower = msg.get("content", "").lower()
                if any(pkg in msg_lower for pkg in package_names):
                    signals.append("Context: Recent dependency discussion")
                    confidence_score += 0.15
                    break

        # 8. Question type analysis
        question_patterns = [
            (r"\bshould\s+i\b", 0.25, "Action question (should I)"),
            (r"\bhow\s+to\s+fix\b", 0.3, "Fix request"),
            (r"\bwhat\s+about\b", 0.2, "Inquiry (what about)"),
            (r"\brecommend", 0.25, "Recommendation request"),
            (r"\bpriority\b", 0.2, "Priority question"),
            (r"\bimpact\b", 0.2, "Impact assessment"),
        ]

        for pattern, score, description in question_patterns:
            if re.search(pattern, query_lower):
                signals.append(description)
                confidence_score += score

        # Cap confidence at 1.0
        confidence_score = min(confidence_score, 1.0)

        # Determine relevance based on confidence threshold
        # Threshold: 0.3 (conservative - prefer to include context when uncertain)
        is_relevant = confidence_score >= 0.3

        # Build reasoning
        if signals:
            reasoning = f"Signals: {'; '.join(signals)}"
        else:
            reasoning = "No relevant signals detected"

        result = IntentDetectionResult(
            is_relevant=is_relevant,
            confidence=confidence_score,
            matched_entities=matched_entities,
            reasoning=reasoning,
        )

        logger.info(f"Intent detection for query '{query[:50]}...': {result}")

        return result

    def should_inject_context(
        self,
        query: str,
        selected_dependencies: list | None = None,
        conversation_history: list | None = None,
        confidence_threshold: float = 0.3,
    ) -> bool:
        """
        Convenience method: Returns True if dependency context should be injected.

        Args:
            query: User's message
            selected_dependencies: Selected dependency objects
            conversation_history: Previous messages
            confidence_threshold: Minimum confidence to inject (default 0.3)

        Returns:
            Boolean indicating whether to inject context
        """
        result = self.detect_intent(query, selected_dependencies, conversation_history)
        return result.is_relevant and result.confidence >= confidence_threshold


# Singleton instance
_detector_instance = None


def get_dependency_intent_detector() -> DependencyIntentDetector:
    """Get or create singleton dependency intent detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = DependencyIntentDetector()
    return _detector_instance

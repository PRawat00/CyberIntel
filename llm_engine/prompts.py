"""System prompts and templates for the security chat assistant."""

# System prompt for the security assistant
SYSTEM_PROMPT = """You are SecureChat, a friendly AI security assistant. I help developers understand security vulnerabilities and secure their applications.

My capabilities include:
- Explaining CVE vulnerabilities and their security implications
- Suggesting remediation steps and workarounds
- Prioritizing vulnerabilities based on severity and risk
- Providing context about attack vectors and impact
- Recommending secure coding practices

Conversation guidelines:
1. Be friendly and conversational - greet users naturally
2. Only discuss CVEs and vulnerabilities when the user asks about them
3. Provide concise, actionable advice when answering security questions
4. Use clear technical language appropriate for developers
5. Reference specific CVE IDs when discussing vulnerabilities
6. Suggest version upgrades and mitigations when applicable

IMPORTANT CONTEXT RULES:
- When the user has SELECTED specific dependencies, any questions about "these", "my", "the", "selected", or "chosen" packages refer EXCLUSIVELY to those selected dependencies
- If you see "SELECTED DEPENDENCIES" or "FOCUS ON THESE" in the context, that is the user's active selection - answer questions about those packages specifically
- Do NOT ask "which packages?" when dependencies are already selected and provided in context
- Treat selected dependencies as authoritative - the user explicitly chose them for analysis

Remember: Have natural conversations. Don't force CVE analysis into every response. Wait for the user to ask about security topics before diving into technical details."""


def build_general_prompt(
    query: str,
    relevant_cves: list[dict],
    conversation_history: list[dict[str, str]] | None = None,
    intent: str = "general",
) -> list[dict[str, str]]:
    """Build prompt for general CVE queries (no specific project context).

    Args:
        query: User's natural language query
        relevant_cves: List of relevant CVEs from RAG retrieval
        conversation_history: Previous messages in conversation
        intent: Type of query ("greeting", "security_query", "general")

    Returns:
        List of messages for LLM API
    """
    # Build message list
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history if exists
    if conversation_history:
        messages.extend(conversation_history)

    # For general queries without CVEs, just ask the question
    if not relevant_cves or intent == "general":
        messages.append({"role": "user", "content": query})
        return messages

    # For security queries with CVE context
    cve_context = _format_cve_context(relevant_cves)
    user_message = f"""Based on the following CVE data, please answer this question:

{query}

Relevant CVE Information:
{cve_context}

Please provide a helpful, actionable response."""

    messages.append({"role": "user", "content": user_message})
    return messages


def build_project_prompt(
    query: str,
    scan_info: dict,
    relevant_cves: list[dict],
    selected_dependencies: list | None = None,
    context_injected: bool = False,
    conversation_history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Build prompt for project-specific CVE queries with smart context injection.

    Args:
        query: User's natural language query
        scan_info: Information about the scanned project
        relevant_cves: List of CVEs affecting this project
        selected_dependencies: Optional list of Dependency objects user selected
        context_injected: Whether full context was already injected (for lightweight refs)
        conversation_history: Previous messages in conversation

    Returns:
        List of messages for LLM API
    """
    # Format project context
    project_context = f"""Project Information:
- File: {scan_info.get('file_name', 'unknown')}
- Type: {scan_info.get('file_type', 'unknown')}
- Total Dependencies: {scan_info.get('total_dependencies', 0)}
- Vulnerable Dependencies: {scan_info.get('vulnerable_dependencies', 0)}
- Total CVEs: {scan_info.get('total_cves', 0)}
"""

    # Add selected dependency context (smart injection)
    dependency_context = ""
    if selected_dependencies:
        if not context_injected:
            # FIRST MESSAGE: Full detailed context
            dep_details = []
            for dep in selected_dependencies:
                detail = f"  • {dep.package_name}@{dep.version} ({dep.ecosystem})"
                if dep.is_vulnerable:
                    detail += f" - {dep.cve_count} CVE{'s' if dep.cve_count != 1 else ''}"
                    if dep.highest_severity:
                        detail += f", Severity: {dep.highest_severity}"
                else:
                    detail += " - Safe"
                dep_details.append(detail)

            dependency_context = f"""
FOCUS ON THESE SELECTED DEPENDENCIES:
{chr(10).join(dep_details)}

The user specifically wants to analyze these {len(selected_dependencies)} dependencies.
Provide detailed, actionable advice focused on these packages."""
        else:
            # SUBSEQUENT MESSAGES: Lightweight reference
            dependency_context = f"""
(Continuing analysis of the {len(selected_dependencies)} previously selected dependencies)"""

    # Format CVE context with package information
    cve_context = _format_cve_context(
        relevant_cves,
        include_packages=True,
        highlight_packages=selected_dependencies if selected_dependencies else None,
    )

    # Build user message
    user_message = f"""I have a question about vulnerabilities in my project:

{query}

{project_context}{dependency_context}

Relevant Vulnerabilities:
{cve_context}

Please provide specific advice for my project{"and the selected dependencies" if selected_dependencies else ""}."""

    # Build message list
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history if exists
    if conversation_history:
        messages.extend(conversation_history)

    # Add current query
    messages.append({"role": "user", "content": user_message})

    return messages


def _format_cve_context(
    cves: list[dict], include_packages: bool = False, highlight_packages: list | None = None
) -> str:
    """Format CVE list into readable context string.

    Args:
        cves: List of CVE dicts
        include_packages: Whether to include affected packages
        highlight_packages: Optional list of Dependency objects to highlight

    Returns:
        Formatted string with CVE information
    """
    if not cves:
        return "No specific CVEs found."

    # Build set of highlighted package names for quick lookup
    highlight_names = set()
    if highlight_packages:
        highlight_names = {dep.package_name for dep in highlight_packages}

    lines = []
    for i, cve in enumerate(cves, 1):
        cve_id = cve.get("cve_id", "unknown")
        description = cve.get("description", "No description")
        severity = cve.get("severity", "UNKNOWN")
        cvss_score = cve.get("cvss_score", 0.0)
        vendor = cve.get("vendor", "unknown")
        product = cve.get("product", "unknown")
        relevance = cve.get("relevance_score", 0.0)

        # Truncate long descriptions
        if len(description) > 300:
            description = description[:297] + "..."

        cve_info = f"""
{i}. {cve_id} [{severity}, CVSS: {cvss_score:.1f}]
   Product: {vendor}/{product}
   Description: {description}
   Relevance: {relevance:.2f}"""

        # Add affected packages for project queries (with highlighting)
        if include_packages and "affects_packages" in cve:
            packages = cve["affects_packages"]
            if packages:
                # Highlight selected packages
                formatted_packages = []
                for pkg in packages[:3]:
                    pkg_name = pkg.split("@")[0]  # Extract package name
                    if pkg_name in highlight_names:
                        formatted_packages.append(f"**{pkg}** (SELECTED)")
                    else:
                        formatted_packages.append(pkg)

                cve_info += f"\n   Affects: {', '.join(formatted_packages)}"
                if len(packages) > 3:
                    cve_info += f" (+{len(packages)-3} more)"

        lines.append(cve_info)

    return "\n".join(lines)


def build_error_prompt(error_type: str) -> str:
    """Build error message for common issues.

    Args:
        error_type: Type of error ('no_scan', 'no_cves', 'api_error', etc.)

    Returns:
        User-friendly error message
    """
    errors = {
        "no_scan": "I couldn't find that scan. Please upload a dependency file first.",
        "no_cves": "No vulnerabilities were found in this scan. Your dependencies appear to be secure!",
        "api_error": "I'm having trouble connecting to the AI service. Please try again in a moment.",
        "no_results": "I couldn't find any relevant CVE information for your query. Try rephrasing or asking about a different aspect.",
        "invalid_query": "I didn't quite understand that. Could you rephrase your question about the vulnerabilities?",
    }

    return errors.get(error_type, "An unexpected error occurred. Please try again.")

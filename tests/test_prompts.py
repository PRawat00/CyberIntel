"""Unit tests for prompt building functions.

Tests the prompt construction logic for general and project-specific queries,
CVE context formatting, and error messages.
"""

from llm_engine.prompts import (
    SYSTEM_PROMPT,
    _format_cve_context,
    build_error_prompt,
    build_general_prompt,
    build_project_prompt,
)


class TestBuildGeneralPrompt:
    """Test general CVE query prompt building."""

    def test_greeting_query_without_cves(self):
        """Test prompt for greeting with no CVE context."""
        query = "Hello there"
        relevant_cves = []
        intent = "greeting"

        result = build_general_prompt(query, relevant_cves, intent=intent)

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == SYSTEM_PROMPT
        assert result[1]["role"] == "user"
        assert result[1]["content"] == query

    def test_general_query_without_cves(self):
        """Test general query with no CVE context."""
        query = "What are common security vulnerabilities?"
        relevant_cves = []
        intent = "general"

        result = build_general_prompt(query, relevant_cves, intent=intent)

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[1]["content"] == query

    def test_security_query_with_cves(self):
        """Test security query with CVE context."""
        query = "Tell me about SQL injection vulnerabilities"
        relevant_cves = [
            {
                "cve_id": "CVE-2023-12345",
                "description": "SQL injection in example library",
                "severity": "HIGH",
                "cvss_score": 7.5,
                "vendor": "example",
                "product": "library",
                "relevance_score": 0.95,
            }
        ]
        intent = "security_query"

        result = build_general_prompt(query, relevant_cves, intent=intent)

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"

        # Check that CVE context is included
        user_message = result[1]["content"]
        assert query in user_message
        assert "CVE-2023-12345" in user_message
        assert "SQL injection" in user_message
        assert "Relevant CVE Information:" in user_message

    def test_query_with_conversation_history(self):
        """Test prompt building with conversation history."""
        query = "What about the previous CVE?"
        relevant_cves = []
        conversation_history = [
            {"role": "user", "content": "Tell me about CVE-2023-12345"},
            {"role": "assistant", "content": "CVE-2023-12345 is a SQL injection vulnerability..."},
        ]

        result = build_general_prompt(
            query, relevant_cves, conversation_history=conversation_history
        )

        assert len(result) == 4  # system + 2 history + new query
        assert result[0]["role"] == "system"
        assert result[1] == conversation_history[0]
        assert result[2] == conversation_history[1]
        assert result[3]["role"] == "user"
        assert result[3]["content"] == query

    def test_query_with_multiple_cves(self):
        """Test prompt with multiple CVEs in context."""
        query = "Which vulnerability is most critical?"
        relevant_cves = [
            {
                "cve_id": "CVE-2023-11111",
                "description": "Critical RCE",
                "severity": "CRITICAL",
                "cvss_score": 9.8,
                "vendor": "vendor1",
                "product": "product1",
                "relevance_score": 0.98,
            },
            {
                "cve_id": "CVE-2023-22222",
                "description": "XSS vulnerability",
                "severity": "MEDIUM",
                "cvss_score": 5.4,
                "vendor": "vendor2",
                "product": "product2",
                "relevance_score": 0.85,
            },
        ]

        result = build_general_prompt(query, relevant_cves, intent="security_query")

        user_message = result[1]["content"]
        assert "CVE-2023-11111" in user_message
        assert "CVE-2023-22222" in user_message
        assert "Critical RCE" in user_message
        assert "XSS vulnerability" in user_message

    def test_empty_query(self):
        """Test handling of empty query."""
        query = ""
        relevant_cves = []

        result = build_general_prompt(query, relevant_cves)

        assert len(result) == 2
        assert result[1]["content"] == ""


class TestBuildProjectPrompt:
    """Test project-specific query prompt building."""

    def test_project_prompt_basic(self):
        """Test basic project prompt construction."""
        query = "What are my critical vulnerabilities?"
        scan_info = {
            "file_name": "package.json",
            "file_type": "npm",
            "total_dependencies": 150,
            "vulnerable_dependencies": 5,
            "total_cves": 12,
        }
        relevant_cves = [
            {
                "cve_id": "CVE-2023-99999",
                "description": "Test vulnerability",
                "severity": "HIGH",
                "cvss_score": 8.0,
                "vendor": "test",
                "product": "package",
                "relevance_score": 0.90,
                "affects_packages": ["test-package@1.0.0"],
            }
        ]

        result = build_project_prompt(query, scan_info, relevant_cves)

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"

        user_message = result[1]["content"]
        assert query in user_message
        assert "package.json" in user_message
        assert "npm" in user_message
        assert "150" in user_message  # total deps
        assert "5" in user_message  # vulnerable deps
        assert "12" in user_message  # total CVEs
        assert "CVE-2023-99999" in user_message
        assert "test-package" in user_message  # affected package

    def test_project_prompt_with_conversation_history(self):
        """Test project prompt with conversation history."""
        query = "How do I fix these?"
        scan_info = {
            "file_name": "requirements.txt",
            "file_type": "pip",
            "total_dependencies": 50,
            "vulnerable_dependencies": 2,
            "total_cves": 3,
        }
        relevant_cves = []
        conversation_history = [
            {"role": "user", "content": "Show me critical vulnerabilities"},
            {"role": "assistant", "content": "You have 2 critical vulnerabilities..."},
        ]

        result = build_project_prompt(
            query, scan_info, relevant_cves, conversation_history=conversation_history
        )

        assert len(result) == 4  # system + 2 history + new query
        assert result[1] == conversation_history[0]
        assert result[2] == conversation_history[1]
        assert result[3]["role"] == "user"

    def test_project_prompt_with_no_cves(self):
        """Test project prompt when no CVEs found."""
        query = "Are there any vulnerabilities?"
        scan_info = {
            "file_name": "package.json",
            "file_type": "npm",
            "total_dependencies": 100,
            "vulnerable_dependencies": 0,
            "total_cves": 0,
        }
        relevant_cves = []

        result = build_project_prompt(query, scan_info, relevant_cves)

        user_message = result[1]["content"]
        assert "No specific CVEs found" in user_message
        assert "0" in user_message  # 0 vulnerable deps

    def test_project_prompt_missing_scan_fields(self):
        """Test project prompt with incomplete scan info."""
        query = "Test query"
        scan_info = {}  # Missing all fields
        relevant_cves = []

        result = build_project_prompt(query, scan_info, relevant_cves)

        user_message = result[1]["content"]
        assert "unknown" in user_message  # default values
        assert "0" in user_message  # default counts

    def test_project_prompt_with_many_affected_packages(self):
        """Test CVE affecting multiple packages (should truncate)."""
        query = "Test"
        scan_info = {"file_name": "test.json", "file_type": "npm"}
        relevant_cves = [
            {
                "cve_id": "CVE-2023-00001",
                "description": "Test",
                "severity": "HIGH",
                "cvss_score": 7.0,
                "vendor": "vendor",
                "product": "product",
                "relevance_score": 0.8,
                "affects_packages": ["pkg1", "pkg2", "pkg3", "pkg4", "pkg5"],
            }
        ]

        result = build_project_prompt(query, scan_info, relevant_cves)

        user_message = result[1]["content"]
        assert "pkg1, pkg2, pkg3" in user_message
        assert "+2 more" in user_message  # Shows truncation


class TestFormatCveContext:
    """Test CVE context formatting."""

    def test_empty_cve_list(self):
        """Test formatting empty CVE list."""
        result = _format_cve_context([])
        assert result == "No specific CVEs found."

    def test_single_cve(self):
        """Test formatting single CVE."""
        cves = [
            {
                "cve_id": "CVE-2023-12345",
                "description": "Example SQL injection vulnerability",
                "severity": "HIGH",
                "cvss_score": 7.5,
                "vendor": "example",
                "product": "library",
                "relevance_score": 0.95,
            }
        ]

        result = _format_cve_context(cves)

        assert "1." in result
        assert "CVE-2023-12345" in result
        assert "HIGH" in result
        assert "7.5" in result
        assert "example/library" in result
        assert "SQL injection" in result
        assert "0.95" in result

    def test_multiple_cves(self):
        """Test formatting multiple CVEs."""
        cves = [
            {
                "cve_id": "CVE-2023-11111",
                "description": "First vulnerability",
                "severity": "CRITICAL",
                "cvss_score": 9.0,
                "vendor": "v1",
                "product": "p1",
                "relevance_score": 0.98,
            },
            {
                "cve_id": "CVE-2023-22222",
                "description": "Second vulnerability",
                "severity": "MEDIUM",
                "cvss_score": 5.5,
                "vendor": "v2",
                "product": "p2",
                "relevance_score": 0.85,
            },
        ]

        result = _format_cve_context(cves)

        assert "1." in result
        assert "2." in result
        assert "CVE-2023-11111" in result
        assert "CVE-2023-22222" in result
        assert "CRITICAL" in result
        assert "MEDIUM" in result

    def test_long_description_truncation(self):
        """Test that long descriptions are truncated."""
        long_desc = "A" * 400  # 400 characters
        cves = [
            {
                "cve_id": "CVE-2023-12345",
                "description": long_desc,
                "severity": "HIGH",
                "cvss_score": 7.0,
                "vendor": "test",
                "product": "test",
                "relevance_score": 0.9,
            }
        ]

        result = _format_cve_context(cves)

        # Should be truncated to 297 chars + "..."
        assert long_desc[:297] in result
        assert "..." in result
        assert len(result) < len(long_desc) + 100  # Much shorter than full description

    def test_missing_optional_fields(self):
        """Test CVE with missing optional fields."""
        cves = [
            {
                # Missing description, severity, vendor, product
                "cve_id": "CVE-2023-12345",
            }
        ]

        result = _format_cve_context(cves)

        assert "CVE-2023-12345" in result
        assert "UNKNOWN" in result  # default severity
        assert "0.0" in result  # default cvss_score
        assert "unknown/unknown" in result  # default vendor/product
        assert "No description" in result

    def test_include_packages_without_packages(self):
        """Test include_packages flag when CVE has no packages."""
        cves = [
            {
                "cve_id": "CVE-2023-12345",
                "description": "Test",
                "severity": "HIGH",
                "cvss_score": 7.0,
                "vendor": "test",
                "product": "test",
                "relevance_score": 0.9,
                # No affects_packages field
            }
        ]

        result = _format_cve_context(cves, include_packages=True)

        # Should not crash, just not include package info
        assert "CVE-2023-12345" in result
        assert "Affects:" not in result

    def test_include_packages_with_packages(self):
        """Test include_packages flag with affected packages."""
        cves = [
            {
                "cve_id": "CVE-2023-12345",
                "description": "Test",
                "severity": "HIGH",
                "cvss_score": 7.0,
                "vendor": "test",
                "product": "test",
                "relevance_score": 0.9,
                "affects_packages": ["package1@1.0.0", "package2@2.0.0"],
            }
        ]

        result = _format_cve_context(cves, include_packages=True)

        assert "Affects:" in result
        assert "package1@1.0.0" in result
        assert "package2@2.0.0" in result

    def test_include_packages_truncation(self):
        """Test package list truncation at 3 packages."""
        cves = [
            {
                "cve_id": "CVE-2023-12345",
                "description": "Test",
                "severity": "HIGH",
                "cvss_score": 7.0,
                "vendor": "test",
                "product": "test",
                "relevance_score": 0.9,
                "affects_packages": ["pkg1", "pkg2", "pkg3", "pkg4", "pkg5"],
            }
        ]

        result = _format_cve_context(cves, include_packages=True)

        assert "pkg1, pkg2, pkg3" in result
        assert "+2 more" in result
        assert "pkg4" not in result  # Truncated

    def test_zero_relevance_score(self):
        """Test CVE with zero relevance score."""
        cves = [
            {
                "cve_id": "CVE-2023-12345",
                "description": "Test",
                "severity": "LOW",
                "cvss_score": 2.0,
                "vendor": "test",
                "product": "test",
                "relevance_score": 0.0,
            }
        ]

        result = _format_cve_context(cves)

        assert "0.00" in result  # Should format as 0.00


class TestBuildErrorPrompt:
    """Test error message building."""

    def test_no_scan_error(self):
        """Test 'no_scan' error message."""
        result = build_error_prompt("no_scan")
        assert "couldn't find that scan" in result.lower()
        assert "upload" in result.lower()

    def test_no_cves_error(self):
        """Test 'no_cves' error message."""
        result = build_error_prompt("no_cves")
        assert "no vulnerabilities" in result.lower()
        assert "secure" in result.lower()

    def test_api_error(self):
        """Test 'api_error' error message."""
        result = build_error_prompt("api_error")
        assert "trouble connecting" in result.lower()
        assert "try again" in result.lower()

    def test_no_results_error(self):
        """Test 'no_results' error message."""
        result = build_error_prompt("no_results")
        assert "couldn't find" in result.lower()
        assert "rephras" in result.lower()

    def test_invalid_query_error(self):
        """Test 'invalid_query' error message."""
        result = build_error_prompt("invalid_query")
        assert "didn't quite understand" in result.lower()
        assert "rephrase" in result.lower()

    def test_unknown_error_type(self):
        """Test unknown error type returns generic message."""
        result = build_error_prompt("some_random_error")
        assert "unexpected error" in result.lower()
        assert "try again" in result.lower()

    def test_empty_error_type(self):
        """Test empty error type returns generic message."""
        result = build_error_prompt("")
        assert "unexpected error" in result.lower()


class TestSystemPrompt:
    """Test system prompt constant."""

    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 0

    def test_system_prompt_content(self):
        """Test system prompt contains expected content."""
        assert "SecureChat" in SYSTEM_PROMPT
        assert "security" in SYSTEM_PROMPT.lower()
        assert "CVE" in SYSTEM_PROMPT
        assert "friendly" in SYSTEM_PROMPT.lower()

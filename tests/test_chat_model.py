"""Unit tests for ChatModel with RAG integration.

Tests the high-level chat model orchestration including RAG retrieval,
prompt building, LLM calls, and response formatting.
"""

from unittest.mock import Mock, patch

import pytest

from llm_engine.chat_model import ChatModel, stream_text_with_delay


class TestStreamTextWithDelay:
    """Test text streaming utility function."""

    def test_stream_single_word(self):
        """Test streaming single word."""
        result = list(stream_text_with_delay("Hello"))
        assert result == ["Hello"]

    def test_stream_multiple_words(self):
        """Test streaming multiple words with spaces."""
        result = list(stream_text_with_delay("Hello world test"))
        # Each word except last should have space
        assert result == ["Hello ", "world ", "test"]

    def test_stream_empty_string(self):
        """Test streaming empty string."""
        result = list(stream_text_with_delay(""))
        assert result == [""]

    def test_stream_with_multiple_spaces(self):
        """Test streaming text with multiple spaces."""
        result = list(stream_text_with_delay("Hello  world"))
        # Empty string between double spaces
        assert result == ["Hello ", " ", "world"]


class TestChatModelInitialization:
    """Test ChatModel initialization."""

    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_successful_initialization_with_api_key(self, mock_provider, mock_rag):
        """Test successful initialization with API key."""
        api_key = "xai-test-key"

        model = ChatModel(api_key=api_key)

        assert model.api_key == api_key
        mock_provider.assert_called_once_with(
            api_key=api_key, model_name="grok-4-fast-reasoning", temperature=0.7, max_tokens=1024
        )
        mock_rag.assert_called_once()

    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    @patch.dict("os.environ", {"GROQ_API_KEY": "env-api-key"})
    def test_initialization_with_env_api_key(self, mock_provider, mock_rag):
        """Test initialization using environment variable."""
        model = ChatModel()

        assert model.api_key == "env-api-key"
        mock_provider.assert_called_once()

    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    @patch.dict("os.environ", {}, clear=True)
    def test_initialization_without_api_key_raises(self, mock_provider, mock_rag):
        """Test that missing API key raises ValueError."""
        with pytest.raises(ValueError, match="No API key provided"):
            ChatModel()

    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_initialization_with_custom_parameters(self, mock_provider, mock_rag):
        """Test initialization with custom model parameters."""
        api_key = "test-key"
        model_name = "grok-3"
        temperature = 0.5
        max_tokens = 2048

        ChatModel(
            api_key=api_key, model_name=model_name, temperature=temperature, max_tokens=max_tokens
        )

        mock_provider.assert_called_once_with(
            api_key=api_key, model_name=model_name, temperature=temperature, max_tokens=max_tokens
        )

    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_initialization_with_custom_rag(self, mock_provider, mock_rag_class):
        """Test initialization with custom RAG retriever."""
        api_key = "test-key"
        custom_rag = Mock()

        model = ChatModel(api_key=api_key, rag_retriever=custom_rag)

        assert model.rag == custom_rag
        # Should not create new RAGRetriever
        mock_rag_class.assert_not_called()


class TestChatGeneral:
    """Test general CVE chat (no specific project)."""

    @patch("llm_engine.intent_detector.detect_intent")
    @patch("llm_engine.intent_detector.get_greeting_response")
    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_greeting_query_non_streaming(
        self, mock_provider, mock_rag, mock_greeting_resp, mock_intent
    ):
        """Test greeting query returns greeting without RAG."""
        api_key = "test-key"
        mock_intent.return_value = "greeting"
        mock_greeting_resp.return_value = "Hello! How can I help you?"

        model = ChatModel(api_key=api_key)
        result = model.chat_general("Hello")

        assert result == "Hello! How can I help you?"
        mock_intent.assert_called_once_with("Hello")
        mock_greeting_resp.assert_called_once()
        # Should NOT call RAG for greetings
        model.rag.query_general.assert_not_called()

    @patch("llm_engine.intent_detector.detect_intent")
    @patch("llm_engine.intent_detector.get_greeting_response")
    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_greeting_query_streaming(
        self, mock_provider, mock_rag, mock_greeting_resp, mock_intent
    ):
        """Test streaming greeting query."""
        api_key = "test-key"
        mock_intent.return_value = "greeting"
        mock_greeting_resp.return_value = "Hello there"

        model = ChatModel(api_key=api_key)
        result = list(model.chat_general("Hi", stream=True))

        assert result == ["Hello ", "there"]
        model.rag.query_general.assert_not_called()

    @patch("llm_engine.intent_detector.detect_intent")
    @patch("llm_engine.chat_model.build_general_prompt")
    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_security_query_with_cves(
        self, mock_provider, mock_rag, mock_build_prompt, mock_intent
    ):
        """Test security query retrieves CVEs and generates response."""
        api_key = "test-key"
        mock_intent.return_value = "security_query"

        # Mock RAG results
        mock_rag_instance = Mock()
        mock_rag_instance.query_general.return_value = {
            "cves": [{"cve_id": "CVE-2023-12345", "description": "Test CVE"}]
        }
        mock_rag.return_value = mock_rag_instance

        # Mock prompt building
        mock_build_prompt.return_value = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User query"},
        ]

        # Mock LLM response
        mock_llm = Mock()
        mock_llm.generate.return_value = "Generated response"
        mock_provider.return_value = mock_llm

        model = ChatModel(api_key=api_key)
        result = model.chat_general("Tell me about SQL injection")

        assert result == "Generated response"
        mock_intent.assert_called_once_with("Tell me about SQL injection")
        mock_rag_instance.query_general.assert_called_once()
        mock_build_prompt.assert_called_once()
        mock_llm.generate.assert_called_once()

    @patch("llm_engine.intent_detector.detect_intent")
    @patch("llm_engine.chat_model.build_general_prompt")
    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_security_query_streaming(
        self, mock_provider, mock_rag, mock_build_prompt, mock_intent
    ):
        """Test streaming security query."""
        api_key = "test-key"
        mock_intent.return_value = "security_query"

        mock_rag_instance = Mock()
        mock_rag_instance.query_general.return_value = {"cves": []}
        mock_rag.return_value = mock_rag_instance

        mock_build_prompt.return_value = [{"role": "user", "content": "Test"}]

        # Mock streaming response
        mock_llm = Mock()
        mock_llm.generate_stream.return_value = iter(["Hello ", "world"])
        mock_provider.return_value = mock_llm

        model = ChatModel(api_key=api_key)
        result = list(model.chat_general("Test query", stream=True))

        assert result == ["Hello ", "world"]
        mock_llm.generate_stream.assert_called_once()

    @patch("llm_engine.intent_detector.detect_intent")
    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_general_query_with_conversation_history(self, mock_provider, mock_rag, mock_intent):
        """Test query with conversation history."""
        api_key = "test-key"
        mock_intent.return_value = "general"

        mock_rag_instance = Mock()
        mock_rag_instance.query_general.return_value = {"cves": []}
        mock_rag.return_value = mock_rag_instance

        mock_llm = Mock()
        mock_llm.generate.return_value = "Response"
        mock_provider.return_value = mock_llm

        conversation_history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]

        model = ChatModel(api_key=api_key)

        with patch("llm_engine.chat_model.build_general_prompt") as mock_build:
            mock_build.return_value = [{"role": "user", "content": "Test"}]
            model.chat_general("Follow-up", conversation_history=conversation_history)

            # Verify conversation history passed to prompt builder
            call_args = mock_build.call_args
            assert call_args[1]["conversation_history"] == conversation_history

    @patch("llm_engine.intent_detector.detect_intent")
    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_general_query_api_error_non_streaming(self, mock_provider, mock_rag, mock_intent):
        """Test error handling when LLM API fails."""
        api_key = "test-key"
        mock_intent.return_value = "general"

        mock_rag_instance = Mock()
        mock_rag_instance.query_general.return_value = {"cves": []}
        mock_rag.return_value = mock_rag_instance

        mock_llm = Mock()
        mock_llm.generate.side_effect = Exception("API Error")
        mock_provider.return_value = mock_llm

        model = ChatModel(api_key=api_key)
        result = model.chat_general("Test")

        # Should return error message (contains "AI service" or similar)
        assert (
            "trouble" in result.lower()
            or "error" in result.lower()
            or "service" in result.lower()
            or "try again" in result.lower()
        )

    @patch("llm_engine.intent_detector.detect_intent")
    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_general_query_api_error_streaming(self, mock_provider, mock_rag, mock_intent):
        """Test error handling in streaming mode."""
        api_key = "test-key"
        mock_intent.return_value = "general"

        mock_rag_instance = Mock()
        mock_rag_instance.query_general.return_value = {"cves": []}
        mock_rag.return_value = mock_rag_instance

        mock_llm = Mock()
        mock_llm.generate_stream.side_effect = Exception("Stream Error")
        mock_provider.return_value = mock_llm

        model = ChatModel(api_key=api_key)
        result = list(model.chat_general("Test", stream=True))

        # Should return error message as iterator (contains "AI service" or similar)
        assert len(result) == 1
        assert (
            "trouble" in result[0].lower()
            or "error" in result[0].lower()
            or "service" in result[0].lower()
            or "try again" in result[0].lower()
        )


class TestChatProject:
    """Test project-specific CVE chat."""

    @patch("llm_engine.chat_model.build_project_prompt")
    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_project_query_success(self, mock_provider, mock_rag, mock_build_prompt):
        """Test successful project query."""
        api_key = "test-key"
        scan_id = 123

        # Mock RAG results
        mock_rag_instance = Mock()
        mock_rag_instance.query_project.return_value = {
            "cves": [{"cve_id": "CVE-2023-99999"}],
            "scan_info": {"file_name": "package.json"},
        }
        mock_rag.return_value = mock_rag_instance

        mock_build_prompt.return_value = [{"role": "user", "content": "Test"}]

        mock_llm = Mock()
        mock_llm.generate.return_value = "Project response"
        mock_provider.return_value = mock_llm

        model = ChatModel(api_key=api_key)
        result = model.chat_project("What are my vulnerabilities?", scan_id=scan_id)

        assert result == "Project response"
        mock_rag_instance.query_project.assert_called_once_with(
            query="What are my vulnerabilities?", scan_id=scan_id, top_k=5
        )

    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_project_query_scan_not_found(self, mock_provider, mock_rag):
        """Test project query when scan doesn't exist."""
        api_key = "test-key"
        scan_id = 999

        mock_rag_instance = Mock()
        mock_rag_instance.query_project.return_value = {"error": "Scan not found"}
        mock_rag.return_value = mock_rag_instance

        model = ChatModel(api_key=api_key)
        result = model.chat_project("Test", scan_id=scan_id)

        # Should return "no_scan" error
        assert "couldn't find that scan" in result.lower()

    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_project_query_no_vulnerabilities(self, mock_provider, mock_rag):
        """Test project query when no CVEs found."""
        api_key = "test-key"

        mock_rag_instance = Mock()
        mock_rag_instance.query_project.return_value = {
            "cves": [],  # No vulnerabilities
            "scan_info": {"file_name": "package.json"},
        }
        mock_rag.return_value = mock_rag_instance

        model = ChatModel(api_key=api_key)
        result = model.chat_project("Test", scan_id=1)

        # Should return "no_cves" error
        assert "no vulnerabilities" in result.lower()

    @patch("llm_engine.chat_model.build_project_prompt")
    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_project_query_streaming(self, mock_provider, mock_rag, mock_build_prompt):
        """Test streaming project query."""
        api_key = "test-key"

        mock_rag_instance = Mock()
        mock_rag_instance.query_project.return_value = {
            "cves": [{"cve_id": "CVE-2023-00001"}],
            "scan_info": {},
        }
        mock_rag.return_value = mock_rag_instance

        mock_build_prompt.return_value = [{"role": "user", "content": "Test"}]

        mock_llm = Mock()
        mock_llm.generate_stream.return_value = iter(["Stream ", "response"])
        mock_provider.return_value = mock_llm

        model = ChatModel(api_key=api_key)
        result = list(model.chat_project("Test", scan_id=1, stream=True))

        assert result == ["Stream ", "response"]

    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_project_query_with_filters(self, mock_provider, mock_rag):
        """Test project query with additional filters."""
        api_key = "test-key"

        mock_rag_instance = Mock()
        mock_rag_instance.query_project.return_value = {
            "cves": [{"cve_id": "CVE-2023-00001"}],
            "scan_info": {},
        }
        mock_rag.return_value = mock_rag_instance

        mock_llm = Mock()
        mock_llm.generate.return_value = "Response"
        mock_provider.return_value = mock_llm

        model = ChatModel(api_key=api_key)

        with patch("llm_engine.chat_model.build_project_prompt") as mock_build:
            mock_build.return_value = [{"role": "user", "content": "Test"}]
            model.chat_project("Test", scan_id=1, severity_filter="CRITICAL", min_cvss=7.0)

            # Verify filters passed to RAG
            call_args = mock_rag_instance.query_project.call_args
            assert call_args[1]["severity_filter"] == "CRITICAL"
            assert call_args[1]["min_cvss"] == 7.0

    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_project_query_api_error(self, mock_provider, mock_rag):
        """Test error handling when API fails."""
        api_key = "test-key"

        mock_rag_instance = Mock()
        mock_rag_instance.query_project.return_value = {
            "cves": [{"cve_id": "CVE-2023-00001"}],
            "scan_info": {},
        }
        mock_rag.return_value = mock_rag_instance

        mock_llm = Mock()
        mock_llm.generate.side_effect = Exception("API Error")
        mock_provider.return_value = mock_llm

        model = ChatModel(api_key=api_key)
        result = model.chat_project("Test", scan_id=1)

        # Should return error message (contains "AI service" or similar)
        assert (
            "trouble" in result.lower()
            or "error" in result.lower()
            or "service" in result.lower()
            or "try again" in result.lower()
        )


class TestUsageStats:
    """Test usage statistics methods."""

    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_get_usage_stats(self, mock_provider, mock_rag):
        """Test getting usage statistics."""
        api_key = "test-key"

        mock_llm = Mock()
        mock_llm.get_usage_stats.return_value = {
            "total_input_tokens": 1000,
            "total_output_tokens": 2000,
            "total_tokens": 3000,
            "estimated_cost_usd": 0.50,
        }
        mock_provider.return_value = mock_llm

        model = ChatModel(api_key=api_key)
        stats = model.get_usage_stats()

        assert stats["total_input_tokens"] == 1000
        assert stats["total_output_tokens"] == 2000
        assert stats["estimated_cost_usd"] == 0.50

    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_reset_usage_stats(self, mock_provider, mock_rag):
        """Test resetting usage statistics."""
        api_key = "test-key"

        mock_llm = Mock()
        mock_provider.return_value = mock_llm

        model = ChatModel(api_key=api_key)
        model.reset_usage_stats()

        mock_llm.reset_usage_stats.assert_called_once()


class TestRepr:
    """Test string representation."""

    @patch("llm_engine.chat_model.RAGRetriever")
    @patch("llm_engine.chat_model.XAIProvider")
    def test_repr(self, mock_provider, mock_rag):
        """Test __repr__ method."""
        api_key = "test-key"

        mock_rag_instance = Mock()
        mock_rag_instance.vector_store.count.return_value = 1500
        mock_rag.return_value = mock_rag_instance

        model = ChatModel(api_key=api_key)
        repr_str = repr(model)

        assert "ChatModel" in repr_str
        assert "1500" in repr_str  # CVE count

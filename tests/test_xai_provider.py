"""Unit tests for XAI provider implementation.

Tests the xAI Grok provider which uses the OpenAI-compatible API,
including token counting, streaming, cost estimation, and error handling.
"""

from unittest.mock import Mock, patch

import pytest

from llm_engine.providers.xai_provider import XAIProvider


class TestXAIProviderInitialization:
    """Test XAI provider initialization."""

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_successful_initialization_with_defaults(self, mock_tiktoken, mock_openai):
        """Test successful initialization with default parameters."""
        api_key = "xai-test-key-12345"

        provider = XAIProvider(api_key=api_key)

        assert provider.api_key == api_key
        assert provider.model_name == XAIProvider.DEFAULT_MODEL
        assert provider.temperature == 0.7
        assert provider.max_tokens == 4096
        assert provider.total_input_tokens == 0
        assert provider.total_output_tokens == 0

        # Verify OpenAI client initialized with correct params
        mock_openai.assert_called_once_with(api_key=api_key, base_url=XAIProvider.XAI_BASE_URL)

        # Verify tokenizer was loaded
        mock_tiktoken.assert_called_once_with("gpt-4")

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_initialization_with_custom_model(self, mock_tiktoken, mock_openai):
        """Test initialization with custom model."""
        api_key = "xai-test-key"
        model_name = "grok-3-mini"

        provider = XAIProvider(api_key=api_key, model_name=model_name)

        assert provider.model_name == model_name

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_initialization_with_custom_parameters(self, mock_tiktoken, mock_openai):
        """Test initialization with custom temperature and max_tokens."""
        provider = XAIProvider(
            api_key="test-key",
            model_name="grok-4-fast-non-reasoning",
            temperature=0.5,
            max_tokens=2048,
        )

        assert provider.temperature == 0.5
        assert provider.max_tokens == 2048

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_tokenizer_fallback_on_error(self, mock_tiktoken, mock_openai):
        """Test fallback to cl100k_base when GPT-4 tokenizer fails."""
        mock_tiktoken.side_effect = Exception("Tokenizer not found")

        with patch("llm_engine.providers.xai_provider.tiktoken.get_encoding") as mock_get_encoding:
            XAIProvider(api_key="test-key")

            # Should fallback to cl100k_base
            mock_get_encoding.assert_called_once_with("cl100k_base")


class TestGenerate:
    """Test non-streaming generation."""

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_successful_generation(self, mock_tiktoken, mock_openai):
        """Test successful text generation."""
        # Setup
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Mock API response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response content"))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20)
        mock_client.chat.completions.create.return_value = mock_response

        provider = XAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Hello"}]

        # Execute
        result = provider.generate(messages)

        # Verify
        assert result == "Test response content"
        assert provider.total_input_tokens == 10
        assert provider.total_output_tokens == 20

        # Verify API called with correct parameters
        mock_client.chat.completions.create.assert_called_once_with(
            model=XAIProvider.DEFAULT_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
            timeout=30.0,
        )

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_generation_with_custom_parameters(self, mock_tiktoken, mock_openai):
        """Test generation with overridden temperature and max_tokens."""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_response.usage = Mock(prompt_tokens=5, completion_tokens=10)
        mock_client.chat.completions.create.return_value = mock_response

        provider = XAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        # Override defaults
        provider.generate(messages, temperature=0.3, max_tokens=512)

        # Verify API called with overridden params
        mock_client.chat.completions.create.assert_called_once_with(
            model=XAIProvider.DEFAULT_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=512,
            timeout=30.0,
        )

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_generation_without_usage_stats(self, mock_tiktoken, mock_openai):
        """Test generation when response doesn't have usage stats."""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Mock response without usage attribute
        mock_response = Mock(spec=["choices"])
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response

        provider = XAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        result = provider.generate(messages)

        # Should not crash, tokens should remain at 0
        assert result == "Response"
        assert provider.total_input_tokens == 0
        assert provider.total_output_tokens == 0

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_generation_api_error(self, mock_tiktoken, mock_openai):
        """Test error handling when API call fails."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        provider = XAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        # Should raise exception
        with pytest.raises(Exception, match="API Error"):
            provider.generate(messages)


class TestGenerateStream:
    """Test streaming generation."""

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_successful_streaming(self, mock_tiktoken, mock_openai):
        """Test successful streaming generation."""
        # Setup
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Mock tokenizer
        mock_tokenizer = Mock()
        mock_tokenizer.encode = lambda text: [1] * len(text)  # 1 token per char
        mock_tiktoken.return_value = mock_tokenizer

        # Mock streaming response
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock(delta=Mock(content="Hello"))]
        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock(delta=Mock(content=" world"))]
        mock_chunk3 = Mock()
        mock_chunk3.choices = [Mock(delta=Mock(content=None))]  # End of stream

        mock_client.chat.completions.create.return_value = iter(
            [mock_chunk1, mock_chunk2, mock_chunk3]
        )

        provider = XAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Hi"}]

        # Execute
        chunks = list(provider.generate_stream(messages))

        # Verify
        assert chunks == ["Hello", " world"]
        assert provider.total_input_tokens == 2  # "Hi" = 2 chars = 2 tokens
        assert provider.total_output_tokens == 11  # "Hello world" = 11 chars

        # Verify API called with stream=True
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]["stream"] is True

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_streaming_with_custom_parameters(self, mock_tiktoken, mock_openai):
        """Test streaming with overridden parameters."""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_tokenizer = Mock()
        mock_tokenizer.encode = lambda text: [1]  # Simple mock
        mock_tiktoken.return_value = mock_tokenizer

        mock_chunk = Mock()
        mock_chunk.choices = [Mock(delta=Mock(content="Test"))]
        mock_client.chat.completions.create.return_value = iter([mock_chunk])

        provider = XAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        # Execute with overrides
        list(provider.generate_stream(messages, temperature=0.1, max_tokens=256))

        # Verify API called with overridden params
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]["temperature"] == 0.1
        assert call_args[1]["max_tokens"] == 256

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_streaming_api_error(self, mock_tiktoken, mock_openai):
        """Test error handling during streaming."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Stream Error")

        provider = XAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        # Should raise exception
        with pytest.raises(Exception, match="Stream Error"):
            list(provider.generate_stream(messages))


class TestCountTokens:
    """Test token counting functionality."""

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_count_tokens_success(self, mock_tiktoken, mock_openai):
        """Test successful token counting."""
        mock_tokenizer = Mock()
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_tiktoken.return_value = mock_tokenizer

        provider = XAIProvider(api_key="test-key")

        count = provider.count_tokens("Hello world")

        assert count == 5
        mock_tokenizer.encode.assert_called_once_with("Hello world")

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_count_tokens_empty_string(self, mock_tiktoken, mock_openai):
        """Test token counting with empty string."""
        mock_tokenizer = Mock()
        mock_tokenizer.encode.return_value = []
        mock_tiktoken.return_value = mock_tokenizer

        provider = XAIProvider(api_key="test-key")

        count = provider.count_tokens("")

        assert count == 0

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_count_tokens_fallback_on_error(self, mock_tiktoken, mock_openai):
        """Test fallback to rough estimate when tokenizer fails."""
        mock_tokenizer = Mock()
        mock_tokenizer.encode.side_effect = Exception("Encoding error")
        mock_tiktoken.return_value = mock_tokenizer

        provider = XAIProvider(api_key="test-key")

        # "Hello" = 5 chars, 5 / 4 = 1 token (rough estimate)
        count = provider.count_tokens("Hello")

        assert count == 1  # 5 chars // 4 = 1

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_count_tokens_unicode(self, mock_tiktoken, mock_openai):
        """Test token counting with unicode characters."""
        mock_tokenizer = Mock()
        mock_tokenizer.encode.return_value = [1, 2, 3]
        mock_tiktoken.return_value = mock_tokenizer

        provider = XAIProvider(api_key="test-key")

        count = provider.count_tokens("Hello 世界")

        assert count == 3


class TestGetUsageStats:
    """Test usage statistics and cost estimation."""

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_usage_stats_basic(self, mock_tiktoken, mock_openai):
        """Test basic usage statistics."""
        provider = XAIProvider(api_key="test-key")
        provider.total_input_tokens = 1000
        provider.total_output_tokens = 2000

        stats = provider.get_usage_stats()

        assert stats["total_input_tokens"] == 1000
        assert stats["total_output_tokens"] == 2000
        assert stats["total_tokens"] == 3000

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_usage_stats_with_cost_estimation(self, mock_tiktoken, mock_openai):
        """Test cost estimation for known models."""
        provider = XAIProvider(api_key="test-key", model_name="grok-4-fast-reasoning")
        provider.total_input_tokens = 1_000_000  # 1M tokens
        provider.total_output_tokens = 500_000  # 0.5M tokens

        stats = provider.get_usage_stats()

        # grok-4-fast-reasoning: $0.20 input, $0.50 output per 1M tokens
        # Expected: (1M * 0.20) + (0.5M * 0.50) = 0.20 + 0.25 = 0.45
        assert "estimated_cost_usd" in stats
        assert stats["estimated_cost_usd"] == 0.45
        assert stats["cost_breakdown"]["input_cost"] == 0.20
        assert stats["cost_breakdown"]["output_cost"] == 0.25

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_usage_stats_grok_3_pricing(self, mock_tiktoken, mock_openai):
        """Test cost estimation for expensive grok-3 model."""
        provider = XAIProvider(api_key="test-key", model_name="grok-3")
        provider.total_input_tokens = 100_000  # 0.1M tokens
        provider.total_output_tokens = 50_000  # 0.05M tokens

        stats = provider.get_usage_stats()

        # grok-3: $3.00 input, $15.00 output per 1M tokens
        # Expected: (0.1M * 3.00) + (0.05M * 15.00) = 0.30 + 0.75 = 1.05
        assert stats["estimated_cost_usd"] == 1.05
        assert stats["cost_breakdown"]["input_cost"] == 0.30
        assert stats["cost_breakdown"]["output_cost"] == 0.75

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_usage_stats_unknown_model_no_cost(self, mock_tiktoken, mock_openai):
        """Test that unknown models don't have cost estimation."""
        provider = XAIProvider(api_key="test-key", model_name="unknown-model")
        provider.total_input_tokens = 1000
        provider.total_output_tokens = 2000

        stats = provider.get_usage_stats()

        # Should not have cost fields for unknown model
        assert "estimated_cost_usd" not in stats
        assert "cost_breakdown" not in stats

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_usage_stats_zero_tokens(self, mock_tiktoken, mock_openai):
        """Test usage stats with zero tokens."""
        provider = XAIProvider(api_key="test-key")

        stats = provider.get_usage_stats()

        assert stats["total_input_tokens"] == 0
        assert stats["total_output_tokens"] == 0
        assert stats["total_tokens"] == 0
        assert stats["estimated_cost_usd"] == 0.0

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_reset_usage_stats(self, mock_tiktoken, mock_openai):
        """Test resetting usage statistics."""
        provider = XAIProvider(api_key="test-key")
        provider.total_input_tokens = 1000
        provider.total_output_tokens = 2000

        provider.reset_usage_stats()

        assert provider.total_input_tokens == 0
        assert provider.total_output_tokens == 0


class TestPricingConstants:
    """Test pricing constants are defined correctly."""

    def test_pricing_dict_exists(self):
        """Test that pricing dictionary exists and has expected models."""
        assert hasattr(XAIProvider, "PRICING")
        assert isinstance(XAIProvider.PRICING, dict)

        # Check some expected models
        assert "grok-4-fast-reasoning" in XAIProvider.PRICING
        assert "grok-3" in XAIProvider.PRICING
        assert "grok-3-mini" in XAIProvider.PRICING

    def test_pricing_structure(self):
        """Test that pricing entries have correct structure."""
        for _model, pricing in XAIProvider.PRICING.items():
            assert "input" in pricing
            assert "output" in pricing
            assert isinstance(pricing["input"], (int, float))
            assert isinstance(pricing["output"], (int, float))
            assert pricing["input"] > 0
            assert pricing["output"] > 0

    def test_default_model_constant(self):
        """Test that default model is defined."""
        assert hasattr(XAIProvider, "DEFAULT_MODEL")
        assert XAIProvider.DEFAULT_MODEL == "grok-4-fast-reasoning"

    def test_xai_base_url_constant(self):
        """Test that xAI base URL is defined."""
        assert hasattr(XAIProvider, "XAI_BASE_URL")
        assert XAIProvider.XAI_BASE_URL == "https://api.x.ai/v1"


class TestRepr:
    """Test string representation."""

    @patch("llm_engine.providers.xai_provider.OpenAI")
    @patch("llm_engine.providers.xai_provider.tiktoken.encoding_for_model")
    def test_repr(self, mock_tiktoken, mock_openai):
        """Test __repr__ method."""
        provider = XAIProvider(api_key="test-key", model_name="grok-3-mini")

        repr_str = repr(provider)

        assert "XAIProvider" in repr_str
        assert "grok-3-mini" in repr_str

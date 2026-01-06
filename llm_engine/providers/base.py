"""Base LLM provider interface for abstracting different LLM APIs."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.

    This abstraction allows easy switching between providers:
    - xAI Grok (Phase 5)
    - OpenAI GPT (fallback)
    - Local models (Phase 6)
    - Groq (alternative)
    """

    def __init__(
        self, api_key: str, model_name: str, temperature: float = 0.7, max_tokens: int | None = None
    ):
        """Initialize LLM provider.

        Args:
            api_key: API key for the provider
            model_name: Model identifier (e.g., "grok-4-fast-reasoning")
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate (None = model default)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Token usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> str:
        """Generate a completion from messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
                     [{"role": "system", "content": "..."}, ...]
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Provider-specific parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> Iterator[str]:
        """Generate a streaming completion from messages.

        Args:
            messages: List of message dicts
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Provider-specific parameters

        Yields:
            Text chunks as they are generated
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        pass

    def get_usage_stats(self) -> dict[str, Any]:
        """Get token usage statistics.

        Returns:
            Dictionary with usage stats:
            {
                "total_input_tokens": int,
                "total_output_tokens": int,
                "total_tokens": int,
                "estimated_cost": float (if applicable)
            }
        """
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
        }

    def reset_usage_stats(self):
        """Reset token usage counters."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model_name})"

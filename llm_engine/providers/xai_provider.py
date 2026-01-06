"""xAI Grok provider implementation using OpenAI-compatible API."""

import logging
from collections.abc import Iterator

import tiktoken
from openai import OpenAI

from llm_engine.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class XAIProvider(BaseLLMProvider):
    """xAI Grok provider using OpenAI-compatible API.

    xAI provides an OpenAI-compatible API at https://api.x.ai/v1
    We use the OpenAI Python SDK with a custom base_url.

    Supported models:
    - grok-4-fast-reasoning (recommended)
    - grok-4-fast-non-reasoning
    - grok-3
    - grok-3-mini
    """

    # xAI API endpoint
    XAI_BASE_URL = "https://api.x.ai/v1"

    # Default model
    DEFAULT_MODEL = "grok-4-fast-reasoning"

    # Pricing per 1M tokens (as of 2025)
    PRICING = {
        "grok-4-fast-reasoning": {"input": 0.20, "output": 0.50},
        "grok-4-fast-non-reasoning": {"input": 0.20, "output": 0.50},
        "grok-3-mini": {"input": 0.30, "output": 0.50},
        "grok-3": {"input": 3.00, "output": 15.00},
        "grok-2-1212": {"input": 2.00, "output": 10.00},
    }

    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int | None = 4096,
    ):
        """Initialize xAI provider.

        Args:
            api_key: xAI API key (starts with 'xai-')
            model_name: Grok model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        super().__init__(api_key, model_name, temperature, max_tokens)

        # Initialize OpenAI client with xAI base URL
        self.client = OpenAI(api_key=api_key, base_url=self.XAI_BASE_URL)

        # Initialize tokenizer (use GPT-4 tokenizer as approximation)
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        except Exception as e:
            logger.warning(f"Failed to load GPT-4 tokenizer: {e}, using cl100k_base")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

        logger.info(f"XAI Provider initialized with model {model_name}")

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> str:
        """Generate a completion from messages.

        Args:
            messages: List of message dicts
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional parameters for API

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails
        """
        try:
            # SECURITY: Add timeout to prevent hanging calls (default 30s)
            timeout = kwargs.pop("timeout", 30.0)

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                timeout=timeout,
                **kwargs,
            )

            # Track token usage
            if hasattr(response, "usage"):
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens

                logger.debug(
                    f"Tokens: {response.usage.prompt_tokens} in, "
                    f"{response.usage.completion_tokens} out"
                )

            # Extract response text
            content = response.choices[0].message.content

            return content

        except Exception as e:
            logger.error(f"xAI API call failed: {e}")
            raise

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
            **kwargs: Additional parameters for API

        Yields:
            Text chunks as they are generated

        Raises:
            Exception: If API call fails
        """
        try:
            # SECURITY: Add timeout to prevent hanging streams (default 60s for streaming)
            timeout = kwargs.pop("timeout", 60.0)

            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=True,
                timeout=timeout,
                **kwargs,
            )

            # Track approximate token usage (exact count not available in stream)
            input_tokens = sum(self.count_tokens(msg.get("content", "")) for msg in messages)
            self.total_input_tokens += input_tokens

            output_tokens = 0

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    output_tokens += self.count_tokens(content)
                    yield content

            self.total_output_tokens += output_tokens

            logger.debug(f"Stream tokens: {input_tokens} in, {output_tokens} out")

        except Exception as e:
            logger.error(f"xAI streaming API call failed: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}, using rough estimate")
            # Rough estimate: ~4 chars per token
            return len(text) // 4

    def get_usage_stats(self) -> dict[str, any]:
        """Get token usage statistics with cost estimation.

        Returns:
            Dictionary with usage stats including estimated cost
        """
        stats = super().get_usage_stats()

        # Add cost estimation
        if self.model_name in self.PRICING:
            pricing = self.PRICING[self.model_name]
            input_cost = (self.total_input_tokens / 1_000_000) * pricing["input"]
            output_cost = (self.total_output_tokens / 1_000_000) * pricing["output"]
            stats["estimated_cost_usd"] = round(input_cost + output_cost, 4)
            stats["cost_breakdown"] = {
                "input_cost": round(input_cost, 4),
                "output_cost": round(output_cost, 4),
            }

        return stats

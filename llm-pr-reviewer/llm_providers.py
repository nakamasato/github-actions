from abc import ABC, abstractmethod
import os
from openai import OpenAI
import anthropic


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_review(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 2000
    ) -> str:
        """Generate a code review response."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of LLM provider."""

    def __init__(self):
        self.api_key = os.environ["OPENAI_API_KEY"]
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key)

    def generate_review(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 2000
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert code reviewer with deep knowledge of software engineering principles, design patterns, and language-specific best practices. Analyze code to provide actionable, high-quality improvements that genuinely enhance the codebase. Focus on important issues rather than trivial style concerns.",
                },
                {"role": "user", "content": prompt},
            ],
            # temperature=temperature,
            # max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()


class AnthropicProvider(LLMProvider):
    """Anthropic implementation of LLM provider."""

    def __init__(self):
        self.api_key = os.environ["ANTHROPIC_API_KEY"]
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate_review(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 2000
    ) -> str:
        response = self.client.messages.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            system="You are an expert code reviewer with deep knowledge of software engineering principles, design patterns, and language-specific best practices. Analyze code to provide actionable, high-quality improvements that genuinely enhance the codebase. Focus on important issues rather than trivial style concerns.",
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content[0].text


def create_llm_provider(provider_type: str | None = None) -> LLMProvider:
    """Factory function to create LLM provider instances."""
    if provider_type is None:
        provider_type = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider_type == "openai":
        return OpenAIProvider()
    elif provider_type == "anthropic":
        return AnthropicProvider()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_type}")

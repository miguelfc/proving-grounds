"""
LLM Client Package

Provides a unified interface for interacting with different LLM providers.
"""

from src.llm.base import LLMClient
from src.llm.gemini import GeminiClient
from src.llm.openai import OpenAIClient
from src.llm.huggingface import LocalHuggingFaceClient
from src.llm.claude import ClaudeClient
from src.llm.cached import CachedLLMClient
from src.llm.ratelimit import RateLimitedLLMClient
from src.llm.exceptions import (
    LLMError,
    RateLimitError,
    AuthenticationError,
    ModelNotFoundError,
    APIConnectionError,
    ContextWindowExceededError
)

__all__ = [
    "LLMError",
    "RateLimitError",
    "AuthenticationError",
    "ModelNotFoundError",
    "APIConnectionError",
    "ContextWindowExceededError",
    "LLMClient",
    "GeminiClient",
    "OpenAIClient",
    "LocalHuggingFaceClient",
    "ClaudeClient",
    "CachedLLMClient",
    "RateLimitedLLMClient",
    "create_client"
]


def create_client(provider: str = "gemini", model_name: str = None, use_cache: bool = True, rpm_limit: int = None) -> LLMClient:
    """
    Factory function to create an LLM client based on provider name.
    
    Args:
        provider: Provider name ('gemini', 'openai', 'claude', 'huggingface')
        model_name: Model name (provider-specific). If None, uses provider defaults.
        use_cache: Whether to wrap the client with caching
        rpm_limit: Optional requests per minute (RPM) limit
    
    Returns:
        LLMClient instance (optionally wrapped with CachedLLMClient and RateLimitedLLMClient)
    
    Examples:
        >>> client = create_client("gemini", "gemini-2.0-flash")
        >>> client = create_client("openai", "gpt-4o-mini", use_cache=False, rpm_limit=60)
        >>> client = create_client("claude", "claude-3-5-sonnet-20241022")
    """
    provider = provider.lower()
    
    # Provider-specific defaults
    defaults = {
        "gemini": "gemini-2.0-flash",
        "openai": "gpt-4o-mini",
        "claude": "claude-3-5-sonnet-20241022",
        "huggingface": "meta-llama/Llama-2-7b-chat-hf"
    }
    
    if model_name is None:
        model_name = defaults.get(provider)
        if model_name is None:
            raise ValueError(f"Unknown provider: {provider}")
    
    # Instantiate the appropriate client
    if provider == "gemini":
        client = GeminiClient(model_name=model_name)
    elif provider == "openai":
        client = OpenAIClient(model_name=model_name)
    elif provider == "claude":
        client = ClaudeClient(model_name=model_name)
    elif provider == "huggingface":
        client = LocalHuggingFaceClient(model_path=model_name)
    else:
        raise ValueError(f"Unknown provider: {provider}. Supported: gemini, openai, claude, huggingface")
    
    # Optionally wrap with rate limit
    if rpm_limit:
        client = RateLimitedLLMClient(client, rpm_limit)

    # Optionally wrap with cache
    if use_cache:
        client = CachedLLMClient(client)
    
    return client

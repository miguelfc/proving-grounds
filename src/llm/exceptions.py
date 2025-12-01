class LLMError(Exception):
    """Base exception for all LLM-related errors."""
    pass

class RateLimitError(LLMError):
    """Raised when the API rate limit is exceeded."""
    pass

class AuthenticationError(LLMError):
    """Raised when API key is invalid or missing."""
    pass

class ModelNotFoundError(LLMError):
    """Raised when the specified model is not found."""
    pass

class ContextWindowExceededError(LLMError):
    """Raised when the input is too long for the model's context window."""
    pass

class APIConnectionError(LLMError):
    """Raised when there is a network issue connecting to the API."""
    pass

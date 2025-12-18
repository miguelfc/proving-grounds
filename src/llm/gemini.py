import os
from google import genai
from google.genai import types
from src.llm.base import LLMClient

from google.api_core import exceptions as google_exceptions
from src.llm.exceptions import (
    LLMError,
    RateLimitError,
    AuthenticationError,
    ModelNotFoundError,
    APIConnectionError,
)


class GeminiClient(LLMClient):
    """
    Implementation for Google Gemini models (e.g., gemini-2.0-flash, gemini-1.5-flash).
    Great for high-throughput testing due to lower cost/free tier.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash-lite"):
        # Automatically loads 'GEMINI_API_KEY' from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise AuthenticationError(
                "GEMINI_API_KEY not found in environment variables."
            )

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def generate_response(
        self, system_prompt: str, user_input: str, temperature: float = 0.3
    ) -> str:
        try:
            # The new SDK allows passing system_instruction dynamically in the config
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                ),
            )
            return response.text if response.text else ""
        except google_exceptions.ResourceExhausted:
            raise RateLimitError(f"Rate limit exceeded for model {self.model_name}")
        except google_exceptions.NotFound:
            raise ModelNotFoundError(f"Model {self.model_name} not found")
        except google_exceptions.Unauthenticated:
            raise AuthenticationError("Invalid Gemini API key")
        except google_exceptions.ServiceUnavailable:
            raise APIConnectionError("Gemini service unavailable")
        except Exception as e:
            error_str = str(e)
            if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                raise RateLimitError(f"Rate limit exceeded: {error_str}")
            if (
                "UNAVAILABLE" in error_str
                or "503" in error_str
                or "overloaded" in error_str
            ):
                raise APIConnectionError(f"Service unavailable: {error_str}")
            raise LLMError(f"Gemini Error: {error_str}")

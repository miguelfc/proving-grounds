import os
import openai
from src.llm.exceptions import (
    LLMError,
    RateLimitError,
    AuthenticationError,
    ModelNotFoundError,
    APIConnectionError
)
from src.llm.base import LLMClient

class OpenAIClient(LLMClient):
    """
    Implementation for OpenAI models (GPT-3.5, GPT-4, or Fine-tuned models).
    Ideal for testing 'Jatmo' (if fine-tuned on OpenAI) or base benchmarks.
    """
    def __init__(self, model_name: str = "gpt-4o-mini"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise AuthenticationError("OPENAI_API_KEY not found in environment variables.")
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def generate_response(self, system_prompt: str, user_input: str, temperature: float = 0.7) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content
        except openai.RateLimitError:
            raise RateLimitError(f"Rate limit exceeded for model {self.model_name}")
        except openai.NotFoundError:
            raise ModelNotFoundError(f"Model {self.model_name} not found")
        except openai.AuthenticationError:
            raise AuthenticationError("Invalid OpenAI API key")
        except openai.APIConnectionError:
            raise APIConnectionError("OpenAI service unavailable")
        except Exception as e:
            raise LLMError(f"OpenAI Error: {str(e)}")

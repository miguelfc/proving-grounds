import os
from src.llm.base import LLMClient

class ClaudeClient(LLMClient):
    """
    Implementation for Anthropic Claude models (e.g., claude-3-5-sonnet-20241022).
    """
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022"):
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
        
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model_name = model_name

    def generate_response(self, system_prompt: str, user_input: str, temperature: float = 0.7) -> str:
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_input}
                ],
                temperature=temperature
            )
            return response.content[0].text
        except Exception as e:
            return f"Error: {str(e)}"

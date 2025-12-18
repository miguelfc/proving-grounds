from src.llm.base import LLMClient
import os


class HuggingFaceClient(LLMClient):
    """
    Implementation for Hugging Face Serverless Inference API.
    """

    def __init__(self, model_name: str = "meta-llama/Llama-3.2-3B-Instruct"):
        try:
            from huggingface_hub import InferenceClient
        except ImportError:
            raise ImportError(
                "Please install huggingface_hub: pip install huggingface_hub"
            )

        # Check for API Key
        api_key = (
            os.getenv("HUGGINGFACE_API_KEY")
            or os.getenv("HF_TOKEN")
            or os.getenv("HUGGINGFACE_TOKEN")
        )
        if not api_key:
            print(
                "Warning: HUGGINGFACE_API_KEY, HF_TOKEN, or HUGGINGFACE_TOKEN not found. Rate limits may apply."
            )

        self.client = InferenceClient(token=api_key)
        self.model_name = model_name

    def generate_response(
        self, system_prompt: str, user_input: str, temperature: float = 0.7
    ) -> str:

        # Construct messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]

        try:
            response = self.client.chat_completion(
                model=self.model_name,
                messages=messages,
                max_tokens=512,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

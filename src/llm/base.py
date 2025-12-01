from abc import ABC, abstractmethod

class LLMClient(ABC):
    """
    Abstract Base Class for LLM interaction.
    This ensures all models (OpenAI, Gemini, Claude, HuggingFace) follow the same contract.
    """

    @abstractmethod
    def generate_response(self, system_prompt: str, user_input: str, temperature: float = 0.7) -> str:
        """
        Sends a prompt to the LLM and returns the text response.
        
        Args:
            system_prompt: The developer-defined instruction (the 'Guardrail').
            user_input: The untrusted input (potentially containing the attack).
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative).
        
        Returns:
            str: The model's response.
        """
        pass






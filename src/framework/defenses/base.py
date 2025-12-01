from abc import ABC, abstractmethod

class DefenseStrategy(ABC):
    """
    Abstract Base Class for Prompt Injection Defense Strategies.
    """
    @abstractmethod
    def apply(self, system_prompt: str, user_input: str) -> tuple[str, str]:
        """
        Applies the defense mechanism to the prompt.
        
        Args:
            system_prompt: The original system prompt.
            user_input: The user's input.
            
        Returns:
            tuple[str, str]: Modified (system_prompt, user_input).
        """
        pass

    @abstractmethod
    def evaluate_response(self, response: str) -> bool:
        """
        Optional: Checks if the response indicates a blocked attack (for detection defenses).
        
        Args:
            response: The LLM's response.
            
        Returns:
            bool: True if the defense blocked/detected an attack, False otherwise.
        """
        return False

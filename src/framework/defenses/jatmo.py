from .base import DefenseStrategy

class JatmoDefense(DefenseStrategy):
    """
    Jatmo (Just Another Task-specific Model Optimization):
    This strategy relies on using a fine-tuned model specifically trained
    on legitimate task interactions to be more resistant to prompt injections.
    
    Unlike other defenses, Jatmo doesn't modify prompts - it uses a different model.
    """
    def __init__(self, model_id: str = None):
        """
        Args:
            model_id: The fine-tuned model ID to use (e.g., 'ft:gpt-3.5-turbo:org:banking:abc123')
                     If None, uses the default model (no override)
        """
        self.model_id = model_id
    
    def apply(self, system_prompt: str, user_input: str) -> tuple[str, str]:
        # Jatmo doesn't modify prompts, it uses a different model
        return system_prompt, user_input

    def evaluate_response(self, response: str) -> bool:
        return False
    
    def get_model_override(self) -> str:
        """
        Returns the fine-tuned model ID to use instead of the default model.
        
        Returns:
            str: Fine-tuned model ID, or None if no override
        """
        return self.model_id

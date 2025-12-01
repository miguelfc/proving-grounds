from .base import DefenseStrategy

class NoDefense(DefenseStrategy):
    """
    Baseline: No defense applied.
    """
    def apply(self, system_prompt: str, user_input: str) -> tuple[str, str]:
        return system_prompt, user_input

    def evaluate_response(self, response: str) -> bool:
        return False

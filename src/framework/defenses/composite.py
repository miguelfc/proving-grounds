from typing import List
from .base import DefenseStrategy

class CompositeDefense(DefenseStrategy):
    """
    Composite Defense: Applies multiple defense strategies in sequence.
    """
    def __init__(self, defenses: List[DefenseStrategy]):
        self.defenses = defenses

    def apply(self, system_prompt: str, user_input: str) -> tuple[str, str]:
        for defense in self.defenses:
            system_prompt, user_input = defense.apply(system_prompt, user_input)
        return system_prompt, user_input

    def evaluate_response(self, response: str) -> bool:
        # If any defense detects an attack, return True
        for defense in self.defenses:
            if defense.evaluate_response(response):
                return True
        return False

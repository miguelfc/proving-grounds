from abc import ABC, abstractmethod

class Tool(ABC):
    """
    Abstract Base Class for tools that the Agent can use.
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, *args, **kwargs) -> str:
        pass
    
    def get_definition(self) -> str:
        """Returns a string representation of the tool for the LLM system prompt."""
        return f"{self.name}: {self.description}"

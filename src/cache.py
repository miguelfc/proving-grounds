import json
import hashlib
import os
from typing import Optional

class LLMCache:
    """
    Simple JSON-based cache for LLM responses.
    """
    def __init__(self, cache_file: str = "llm_cache.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Cache file {self.cache_file} is corrupted. Starting fresh.")
                return {}
        return {}

    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def compute_key(self, system_prompt: str, user_input: str, model_name: str, temperature: float = 0.7) -> str:
        """
        Generates a unique hash key for the request.
        """
        content = f"{model_name}|{system_prompt}|{user_input}|{temperature}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def get(self, key: str) -> Optional[str]:
        return self.cache.get(key)

    def set(self, key: str, value: str):
        self.cache[key] = value
        self._save_cache()

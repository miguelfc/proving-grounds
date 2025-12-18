import json
import hashlib
import os
from typing import Optional


class LLMCache:
    """
    Simple JSON-based cache for LLM responses.
    """

    def __init__(self, cache_file: str = "llm_cache.jsonl"):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            cache_data = {}
            try:
                with open(self.cache_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                if "key" in entry and "value" in entry:
                                    cache_data[entry["key"]] = entry["value"]
                            except json.JSONDecodeError:
                                # Skip bad lines
                                continue
                return cache_data
            except Exception as e:
                print(
                    f"Warning: Failed to load cache file {self.cache_file}: {e}. Starting fresh."
                )
                return {}
        return {}

    def _save_cache(self):
        with open(self.cache_file, "w") as f:
            for key, value in self.cache.items():
                record = {"key": key, "value": value}
                f.write(json.dumps(record) + "\n")

    def compute_key(
        self,
        system_prompt: str,
        user_input: str,
        model_name: str,
        temperature: float = 0.7,
    ) -> str:
        """
        Generates a unique hash key for the request.
        """
        content = f"{model_name}|{system_prompt}|{user_input}|{temperature}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[dict]:
        """
        Returns the cached value.
        Can be a string (legacy) or a dict {"response": str, "latency": float}.
        """
        return self.cache.get(key)

    def set(self, key: str, value: str, latency: float = 0.0):
        """
        Stores the response and its latency.
        """
        self.cache[key] = {"response": value, "latency": latency}
        self._save_cache()

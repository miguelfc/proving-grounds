from src.llm.base import LLMClient
import time


class CachedLLMClient(LLMClient):
    """
    Wrapper around an LLMClient that caches responses to avoid redundant API calls.
    """

    def __init__(self, client: LLMClient, cache_path: str = "llm_cache.jsonl"):
        from src.cache import LLMCache

        self.client = client
        self.cache = LLMCache(cache_path)
        # Expose model_name for compatibility
        self.model_name = getattr(client, "model_name", "unknown")
        self.cache_misses = 0
        self.last_cache_key = None
        self.last_latency = 0.0

    def generate_response(
        self, system_prompt: str, user_input: str, temperature: float = None
    ) -> str:
        # We assume the wrapped client has a 'model_name' attribute.
        # If not, we default to 'unknown'.
        model_name = getattr(self.client, "model_name", "unknown")

        key = self.cache.compute_key(system_prompt, user_input, model_name)
        self.last_cache_key = key
        # get() now returns dict or str or None
        cached_data = self.cache.get(key)

        if cached_data:
            print(f"  [CACHE HIT] Returning cached response for model {model_name}")
            if isinstance(cached_data, dict):
                self.last_latency = cached_data.get("latency", 0.0)
                return cached_data["response"]
            else:
                # Legacy cache (string only)
                self.last_latency = 0.0
                return cached_data

        # Cache Miss
        self.cache_misses += 1
        start_time = time.time()
        if temperature is not None:
            response = self.client.generate_response(
                system_prompt, user_input, temperature
            )
        else:
            response = self.client.generate_response(system_prompt, user_input)

        duration = time.time() - start_time
        self.last_latency = duration

        self.cache.set(key, response, latency=duration)
        return response

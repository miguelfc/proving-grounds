from src.llm.base import LLMClient

class CachedLLMClient(LLMClient):
    """
    Wrapper around an LLMClient that caches responses to avoid redundant API calls.
    """
    def __init__(self, client: LLMClient, cache_path: str = "llm_cache.json"):
        from src.cache import LLMCache
        self.client = client
        self.cache = LLMCache(cache_path)
        # Expose model_name for compatibility
        self.model_name = getattr(client, "model_name", "unknown")
        self.cache_misses = 0

    def generate_response(self, system_prompt: str, user_input: str, temperature: float = 0.7) -> str:
        # We assume the wrapped client has a 'model_name' attribute. 
        # If not, we default to 'unknown'.
        model_name = getattr(self.client, "model_name", "unknown")
        
        key = self.cache.compute_key(system_prompt, user_input, model_name)
        cached_response = self.cache.get(key)
        
        if cached_response:
            print(f"  [CACHE HIT] Returning cached response for model {model_name}")
            return cached_response
            
        # Cache Miss
        self.cache_misses += 1
        response = self.client.generate_response(system_prompt, user_input, temperature)
        self.cache.set(key, response)
        return response

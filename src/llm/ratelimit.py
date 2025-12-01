import time
import threading
from src.llm.base import LLMClient
from src.framework.logger import logger

class RateLimitedLLMClient(LLMClient):
    """
    Wraps an LLMClient to enforce a maximum number of requests per minute (RPM).
    Uses a thread-safe token bucket algorithm.
    """
    def __init__(self, client: LLMClient, requests_per_minute: int):
        self.client = client
        self.rpm = requests_per_minute
        self.interval = 60.0 / requests_per_minute
        self.last_request_time = 0
        self.lock = threading.Lock()
        
        # If we are wrapping another client, inherit its model_name
        if hasattr(client, 'model_name'):
            self.model_name = client.model_name

    def generate_response(self, system_prompt: str, user_input: str, temperature: float = 0.7) -> str:
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_request_time
            
            if elapsed < self.interval:
                sleep_time = self.interval - elapsed
                logger.log(f"Rate limit: Sleeping for {sleep_time:.2f}s (Limit: {self.rpm} RPM)")
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
            
        return self.client.generate_response(system_prompt, user_input, temperature)

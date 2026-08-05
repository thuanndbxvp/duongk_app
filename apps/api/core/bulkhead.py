"""
TokenBucket - Rate limiting utility using token bucket algorithm.
"""
import time
import threading
from typing import Optional


class TokenBucket:
    """Token bucket algorithm for rate limiting."""
    
    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: Tokens per second
            capacity: Maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self._lock = threading.Lock()
    
    def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens, blocking if necessary up to timeout.
        
        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait (None = wait forever)
        
        Returns:
            True if tokens acquired, False if timeout
        """
        deadline = time.monotonic() + timeout if timeout else float('inf')
        
        with self._lock:
            while True:
                self._refill()
                
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
                
                wait_time = (tokens - self.tokens) / self.rate
                if time.monotonic() + wait_time > deadline:
                    return False
                
                time.sleep(min(wait_time, 0.1))
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

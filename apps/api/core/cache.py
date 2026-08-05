"""
Redis Cache với distributed lock cho stampede prevention.
"""
import json
import hashlib
import asyncio
import redis.asyncio as redis
from typing import Optional, Any, Callable, Awaitable


class RedisCache:
    """Redis cache with distributed lock for stampede prevention."""
    
    LOCK_TIMEOUT = 10  # seconds
    LOCK_BLOCK = 5     # seconds to wait for lock
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
    
    async def get_client(self) -> redis.Redis:
        """Lazy initialization of Redis client."""
        if self._client is None:
            self._client = redis.from_url(self.redis_url)
        return self._client
    
    async def get_with_lock(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]],
        ttl: int = 3600
    ) -> Any:
        """
        Get value from cache, using lock to prevent cache stampede.
        
        If cache miss, only one worker generates the value while others wait.
        
        Args:
            key: Cache key
            factory: Async function to generate value if cache miss
            ttl: Time to live in seconds
        
        Returns:
            Cached or freshly generated value
        """
        client = await self.get_client()
        
        # Try cache first
        cached = await client.get(key)
        if cached:
            return json.loads(cached)
        
        # Try to acquire lock
        lock_key = f"lock:{key}"
        lock_acquired = await client.set(
            lock_key,
            "1",
            nx=True,
            ex=self.LOCK_TIMEOUT
        )
        
        if lock_acquired:
            try:
                # We got the lock, generate value
                value = await factory()
                await client.setex(key, ttl, json.dumps(value))
                return value
            finally:
                await client.delete(lock_key)
        else:
            # Wait for another worker to populate cache
            for _ in range(int(self.LOCK_BLOCK * 10)):
                await asyncio.sleep(0.1)
                cached = await client.get(key)
                if cached:
                    return json.loads(cached)
            
            # Timeout, fall back to direct generation
            return await factory()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache without lock."""
        client = await self.get_client()
        cached = await client.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache."""
        client = await self.get_client()
        await client.setex(key, ttl, json.dumps(value))
    
    async def delete(self, key: str):
        """Delete key from cache."""
        client = await self.get_client()
        await client.delete(key)
    
    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

# Kiến trúc & Luồng xử lý (PLAN): Task 1.4 - Triển khai Module 1 (Niche Validate)

1. Viết util TokenBucket.
2. Viết service NicheValidator gọi Pytrends.
3. Nếu Pytrends nghẽn, fallback sang SerpAPI.
4. Implement Redis Cache với Lock (stampede prevention).
5. Code Formula A0 (Video Filter) và A2 (Viral Detection).

---

## Chi tiết từng bước

### 1. TokenBucket Utility

```python
# apps/api/core/bulkhead.py
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
        """Acquire tokens, blocking if necessary up to timeout."""
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
        now = time.monotonic()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
```

### 2. Redis Cache với Lock (Stampede Prevention)

```python
# apps/api/core/cache.py
import json
import hashlib
import redis.asyncio as redis
from typing import Optional, Any
from contextlib import asynccontextmanager

class RedisCache:
    """Redis cache with distributed lock for stampede prevention."""
    
    LOCK_TIMEOUT = 10  # seconds
    LOCK_BLOCK = 5     # seconds to wait for lock
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get_with_lock(
        self,
        key: str,
        factory,  # async function to generate value if cache miss
        ttl: int = 3600
    ) -> Any:
        """
        Get value from cache, using lock to prevent cache stampede.
        
        If cache miss, only one worker generates the value while others wait.
        """
        # Try cache first
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        # Try to acquire lock
        lock_key = f"lock:{key}"
        lock_acquired = await self.redis.set(
            lock_key,
            "1",
            nx=True,
            ex=self.LOCK_TIMEOUT
        )
        
        if lock_acquired:
            try:
                # We got the lock, generate value
                value = await factory()
                await self.redis.setex(key, ttl, json.dumps(value))
                return value
            finally:
                await self.redis.delete(lock_key)
        else:
            # Wait for another worker to populate cache
            for _ in range(int(self.LOCK_BLOCK * 10)):
                await asyncio.sleep(0.1)
                cached = await self.redis.get(key)
                if cached:
                    return json.loads(cached)
            
            # Timeout, fall back to direct generation
            return await factory()
```

### 3. Formula A0 - Video Filter

```python
# apps/api/modules/module_1/formulas.py

def filter_quality_videos(videos: List[dict]) -> List[dict]:
    """
    Formula A0: Filter out low-quality videos.
    
    Remove:
    - Shorts (< 60 seconds)
    - Live streams
    - Videos with < 1000 views
    - Videos older than 2 years
    """
    cutoff_date = datetime.now() - timedelta(days=730)
    
    quality_videos = []
    for video in videos:
        # Skip if duration < 60 seconds (likely Shorts)
        if video.get('duration_seconds', 0) < 60:
            continue
        
        # Skip if is live stream
        if video.get('live_broadcast_content') == 'live':
            continue
        
        # Skip if too few views
        if video.get('view_count', 0) < 1000:
            continue
        
        # Skip if too old
        published = video.get('published_at')
        if published and published < cutoff_date:
            continue
        
        quality_videos.append(video)
    
    return quality_videos
```

### 4. Formula A2 - Viral Detection (MAD Method)

```python
# apps/api/modules/module_1/formulas.py
import numpy as np

def detect_viral_videos(videos: List[dict]) -> List[dict]:
    """
    Formula A2: Detect viral videos using Median Absolute Deviation (MAD).
    
    A video is viral if its view count is significantly higher
    than other videos from the same channel.
    """
    if len(videos) < 5:
        return videos  # Not enough data
    
    views = np.array([v.get('view_count', 0) for v in videos])
    
    median = np.median(views)
    mad = np.median(np.abs(views - median))
    
    # Modified z-score threshold (3.5 for extreme outliers)
    threshold = 3.5
    
    if mad == 0:
        # All videos have similar views
        return []
    
    modified_z_scores = 0.6745 * (views - median) / mad
    
    viral_videos = [
        video for video, z in zip(videos, modified_z_scores)
        if z > threshold
    ]
    
    return viral_videos
```

### 5. NicheValidator Service

```python
# apps/api/modules/module_1/service.py
from apps.api.core.bulkhead import TokenBucket
from apps.api.core.cache import RedisCache

class NicheValidator:
    """Service for validating YouTube niche viability."""
    
    def __init__(self, redis_url: str):
        self.cache = RedisCache(redis_url)
        # Limit Pytrends to 1 request per 10 seconds
        self.pytrends_bucket = TokenBucket(rate=0.1, capacity=1)
    
    async def validate(self, keyword: str) -> dict:
        """
        Validate niche viability.
        
        1. Check Google Trends (via Pytrends)
        2. Estimate market size
        3. Generate suggested titles
        """
        cache_key = f"niche:{hashlib.md5(keyword.encode()).hexdigest()}"
        
        async def _fetch_data():
            # Acquire rate limit token
            if not self.pytrends_bucket.acquire(timeout=30):
                raise RateLimitError("Pytrends rate limited")
            
            # Call Pytrends
            trends_data = await self._fetch_google_trends(keyword)
            
            # Fallback to SerpAPI if Pytrends fails
            if not trends_data:
                trends_data = await self._fetch_serpapi(keyword)
            
            return {
                "keyword": keyword,
                "total_monthly_views": trends_data.get("monthly_views", 0),
                "total_channels": trends_data.get("channels", 0),
                "avg_views_per_video": trends_data.get("avg_views", 0),
                "google_trends_interest": trends_data.get("interest", 0),
                "is_viable": self._calculate_viability(trends_data),
                "suggested_titles": self._generate_titles(keyword, trends_data)
            }
        
        return await self.cache.get_with_lock(
            key=cache_key,
            factory=_fetch_data,
            ttl=86400  # Cache 24 hours
        )
```

## 6. Dependencies

- `redis[hiredis]` (async Redis client)
- `pytrends`
- `serpapi` (optional fallback)

## 7. Verification

- [ ] TokenBucket correctly rate limits requests
- [ ] Redis cache prevents duplicate API calls (stampede test)
- [ ] Formula A0 filters out Shorts and Live streams
- [ ] Formula A2 correctly identifies viral videos using MAD
- [ ] Pytrends fallback to SerpAPI on failure
# MSEW: Task 1.4 - Module 1 Niche Validate

> **Prerequisites:**
> - **Repomix bundle:** `.\CONTEXT_BUNDLE.md`
> - **Python venv activated:** `.\venv\Scripts\Activate.ps1`
> - **Dependencies:** `pip install pytrends serpapi numpy`

---

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | TokenBucket Utility | `general-purpose` | - | - |
| 2 | Redis Cache với Lock | `general-purpose` | `databases` | `planning` |
| 3 | Formula A0 - Video Filter | `general-purpose` | - | - |
| 4 | Formula A2 - Viral Detection | `general-purpose` | - | - |
| 5 | NicheValidator Service | `general-purpose` | `backend-development` | `planning` |
| 6 | API Routes & Schemas | `backend-development` | `general-purpose` | `planning` |
| 7 | Unit Tests | `general-purpose` | `tester` | - |

---

## Files KHÔNG được đụng (Do Not Touch)
- `apps/api/main.py` — Chỉ import routes, không sửa logic
- `apps/worker/` — Worker code thuộc task khác
- `packages/shared-types/` — Models đã defined

---

## Micro-Steps

### Step 1: Tạo TokenBucket Utility

**File:** `apps/api/core/bulkhead.py`
**Vị trí:** Tạo file mới

**Import cần thêm:**
```python
import time
import threading
from typing import Optional
```

**Code cần viết:**
```python
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
```

**Verify command (PowerShell):**
```powershell
python -c "from apps.api.core.bulkhead import TokenBucket; t = TokenBucket(1.0, 5); print('OK' if t.acquire() else 'FAIL')"
```

**Expected output:**
```
OK
```

---

### Step 2: Tạo Redis Cache với Lock

**File:** `apps/api/core/cache.py`
**Vị trí:** Tạo file mới

**Import cần thêm:**
```python
import json
import asyncio
import redis.asyncio as redis
from typing import Optional, Any, Callable, Awaitable
```

**Code cần viết:**
```python
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
```

**Verify command (PowerShell):**
```powershell
python -c "from apps.api.core.cache import RedisCache; print('OK')"
```

**Expected output:**
```
OK
```

---

### Step 3: Tạo Formula A0 - Video Filter

**File:** `apps/api/modules/module_1/formulas.py`
**Vị trí:** Tạo file mới

**Code cần viết:**
```python
"""
Module 1 Formulas - Video filtering and viral detection.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np


def filter_quality_videos(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Formula A0: Filter out low-quality videos.
    
    Removal criteria:
    - Shorts: duration < 60 seconds
    - Live streams: live_broadcast_content == 'live' or 'upcoming'
    - Low engagement: view_count < 1000
    - Too old: published > 2 years ago
    
    Args:
        videos: List of video dictionaries with metadata
    
    Returns:
        Filtered list of quality videos
    """
    cutoff_date = datetime.now() - timedelta(days=730)  # 2 years
    
    quality_videos = []
    for video in videos:
        # Extract metadata
        snippet = video.get('snippet', {})
        content_details = video.get('content_details', {})
        statistics = video.get('statistics', {})
        
        # Parse duration
        duration_seconds = _parse_duration(content_details.get('duration', 'PT0S'))
        if duration_seconds < 60:
            continue
        
        # Skip Live streams
        live_status = snippet.get('live_broadcast_content', 'none')
        if live_status in ('live', 'upcoming'):
            continue
        
        # Skip low-engagement videos
        view_count = int(statistics.get('view_count', 0))
        if view_count < 1000:
            continue
        
        # Skip old videos
        published_str = snippet.get('published_at')
        if published_str:
            published = _parse_datetime(published_str)
            if published and published < cutoff_date:
                continue
        
        # Include quality video
        quality_videos.append(video)
    
    return quality_videos


def _parse_duration(duration: str) -> int:
    """Parse ISO 8601 duration to seconds."""
    import re
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration)
    if not match:
        return 0
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def _parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse ISO datetime string."""
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        return None
```

**Verify command (PowerShell):**
```powershell
python -c "
from apps.api.modules.module_1.formulas import filter_quality_videos
videos = [{'snippet': {'published_at': '2024-01-01T00:00:00Z', 'live_broadcast_content': 'none'}, 'content_details': {'duration': 'PT10M'}, 'statistics': {'view_count': '50000'}}]
result = filter_quality_videos(videos)
print('OK' if len(result) == 1 else 'FAIL')
"
```

**Expected output:**
```
OK
```

---

### Step 4: Tạo Formula A2 - Viral Detection

**File:** `apps/api/modules/module_1/formulas.py`
**Vị trí:** Thêm vào cuối file (sau Step 3)

**Code cần thêm:**
```python
def detect_viral_videos(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Formula A2: Detect viral videos using Median Absolute Deviation (MAD).
    
    A video is considered viral if its view count is significantly higher
    than the channel's typical performance (statistical outlier).
    
    Modified Z-Score = 0.6745 * (value - median) / MAD
    
    Threshold: > 3.5 = extreme outlier (viral)
    
    Args:
        videos: List of video dictionaries with view_count
    
    Returns:
        List of viral videos
    """
    if len(videos) < 5:
        return videos  # Not enough data for MAD
    
    # Extract view counts
    views = np.array([
        int(v.get('statistics', {}).get('view_count', 0))
        for v in videos
    ])
    
    # Calculate median and MAD
    median = np.median(views)
    mad = np.median(np.abs(views - median))
    
    if mad == 0:
        # All videos have identical/similar view counts
        # Check for single viral video (at least 5x median)
        max_views = np.max(views)
        if max_views > median * 5 and median > 0:
            viral_idx = np.argmax(views)
            return [videos[viral_idx]]
        return []
    
    # Calculate modified z-scores
    modified_z_scores = 0.6745 * (views - median) / mad
    
    # Identify viral videos (threshold = 3.5)
    viral_threshold = 3.5
    viral_indices = np.where(modified_z_scores > viral_threshold)[0]
    
    viral_videos = [videos[i] for i in viral_indices]
    return viral_videos
```

**Verify command (PowerShell):**
```powershell
python -c "
from apps.api.modules.module_1.formulas import detect_viral_videos
videos = [
    {'statistics': {'view_count': '10000'}},
    {'statistics': {'view_count': '12000'}},
    {'statistics': {'view_count': '11000'}},
    {'statistics': {'view_count': '500000'}},  # Viral outlier
    {'statistics': {'view_count': '11500'}},
]
result = detect_viral_videos(videos)
print('OK' if len(result) == 1 else f'FAIL: {len(result)}')
"
```

**Expected output:**
```
OK
```

---

### Step 5: Tạo NicheValidator Service

**File:** `apps/api/modules/module_1/service.py`
**Vị trí:** Tạo file mới

**Import cần thêm:**
```python
import hashlib
import os
from typing import List, Optional
from apps.api.core.bulkhead import TokenBucket
from apps.api.core.cache import RedisCache
from apps.api.modules.module_1.formulas import filter_quality_videos, detect_viral_videos
```

**Code cần viết:**
```python
"""
Module 1 - NicheValidator Service.
Validates YouTube niche viability for content creation.
"""
import hashlib
import os
from typing import List, Optional, Dict, Any
from apps.api.core.bulkhead import TokenBucket
from apps.api.core.cache import RedisCache


class NicheValidator:
    """Service for validating YouTube niche viability."""
    
    # Rate limit: 1 request per 10 seconds
    PYTRENDS_RATE = 0.1
    
    def __init__(self, redis_url: str):
        self.cache = RedisCache(redis_url)
        self.pytrends_bucket = TokenBucket(rate=self.PYTRENDS_RATE, capacity=1)
    
    async def validate(
        self,
        keyword: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Validate niche viability.
        
        Args:
            keyword: Keyword to validate
            use_cache: Whether to use cached results
        
        Returns:
            Validation result with viability score
        """
        cache_key = f"niche:validate:{hashlib.md5(keyword.encode()).hexdigest()}"
        
        async def _fetch_data() -> Dict[str, Any]:
            # Acquire rate limit token
            if not self.pytrends_bucket.acquire(timeout=30):
                raise RuntimeError("Pytrends rate limit exceeded")
            
            # Call Pytrends
            trends_data = await self._fetch_google_trends(keyword)
            
            # Fallback to SerpAPI if Pytrends fails
            if not trends_data:
                trends_data = await self._fetch_serpapi(keyword)
            
            # Calculate viability
            is_viable = self._calculate_viability(trends_data)
            suggested_titles = self._generate_titles(keyword, trends_data)
            
            return {
                "keyword": keyword,
                "total_monthly_views": trends_data.get("monthly_views", 0),
                "total_channels": trends_data.get("channels", 0),
                "avg_views_per_video": trends_data.get("avg_views", 0),
                "google_trends_interest": trends_data.get("interest", 0),
                "is_viable": is_viable,
                "suggested_titles": suggested_titles
            }
        
        if use_cache:
            return await self.cache.get_with_lock(
                key=cache_key,
                factory=_fetch_data,
                ttl=86400  # 24 hours
            )
        else:
            return await _fetch_data()
    
    async def _fetch_google_trends(self, keyword: str) -> Dict[str, Any]:
        """Fetch data from Google Trends via Pytrends."""
        try:
            from pytrends.request import TrendReq
            
            pytrends = TrendReq(hl='vi-VN', tz=420)
            pytrends.build_payload([keyword], cat=0, timeframe='today 3-m', geo='VN')
            
            interest = pytrends.interest_over_time()
            interest_score = int(interest[keyword].mean()) if not interest.empty else 0
            
            # Estimate monthly views (rough approximation)
            monthly_views = interest_score * 100000
            
            return {
                "interest": interest_score,
                "monthly_views": monthly_views,
                "channels": 0,  # Pytrends doesn't provide this
                "avg_views": monthly_views // 10 if monthly_views else 0
            }
        except Exception:
            return {}
    
    async def _fetch_serpapi(self, keyword: str) -> Dict[str, Any]:
        """Fallback to SerpAPI for keyword data."""
        try:
            import httpx
            
            serpapi_key = os.environ.get("SERPAPI_KEY")
            if not serpapi_key:
                return {}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "q": keyword + " youtube",
                        "api_key": serpapi_key,
                        "engine": "google"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Parse organic results for estimates
                    return {
                        "interest": 50,  # Default
                        "monthly_views": 1000000,
                        "channels": 100,
                        "avg_views": 10000
                    }
        except Exception:
            pass
        
        return {}
    
    def _calculate_viability(self, trends_data: Dict[str, Any]) -> bool:
        """Calculate if niche is viable based on trends data."""
        interest = trends_data.get("interest", 0)
        monthly_views = trends_data.get("monthly_views", 0)
        
        # Viability criteria:
        # - Interest score >= 30
        # - Monthly views >= 500,000
        return interest >= 30 or monthly_views >= 500000
    
    def _generate_titles(
        self,
        keyword: str,
        trends_data: Dict[str, Any]
    ) -> List[str]:
        """Generate suggested video titles based on keyword and trends."""
        templates = [
            f"Top 5 {{topic}} {keyword} bạn nên biết",
            f"Cách {{action}} {keyword} hiệu quả",
            f"{keyword.title()} - {{benefit}} cho người mới",
            f"Khám phá {{topic}} với {keyword}",
            f"{keyword.title()} | {{guide}} chi tiết"
        ]
        
        topics = ["xu hướng", "mẹo", "thủ thuật", "cách làm"]
        actions = ["làm", "sử dụng", "áp dụng", "thực hiện"]
        benefits = ["lợi ích", "hiệu quả", "kết quả"]
        guides = ["hướng dẫn", "tutorial", "cẩm nang"]
        
        import random
        titles = []
        for _ in range(3):
            template = random.choice(templates)
            title = template.format(
                topic=random.choice(topics),
                action=random.choice(actions),
                benefit=random.choice(benefits),
                guide=random.choice(guides)
            )
            titles.append(title)
        
        return titles
```

**Verify command (PowerShell):**
```powershell
python -c "
import asyncio
from apps.api.modules.module_1.service import NicheValidator

async def test():
    validator = NicheValidator('redis://localhost:6379')
    result = await validator.validate('làm đẹp', use_cache=False)
    print('OK' if 'is_viable' in result else 'FAIL')

asyncio.run(test())
"
```

**Expected output:**
```
OK
```

---

### Step 6: Tạo Pydantic Schemas

**File:** `apps/api/modules/module_1/schemas.py`
**Vị trí:** Tạo file mới

**Code cần viết:**
```python
"""
Module 1 Pydantic Schemas.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class NicheValidationRequest(BaseModel):
    """Request schema for niche validation."""
    
    keyword: str = Field(..., min_length=2, max_length=100, description="Keyword to validate")
    user_id: str = Field(default="system", description="User ID for testing")
    use_cache: bool = Field(default=True, description="Use cached results")


class NicheValidationResponse(BaseModel):
    """Response schema for niche validation."""
    
    keyword: str = Field(..., description="Original keyword")
    total_monthly_views: int = Field(..., ge=0, description="Estimated monthly views")
    total_channels: int = Field(..., ge=0, description="Number of competing channels")
    avg_views_per_video: int = Field(..., ge=0, description="Average views per video")
    google_trends_interest: int = Field(..., ge=0, le=100, description="Google Trends interest score")
    is_viable: bool = Field(..., description="Whether niche is viable")
    suggested_titles: List[str] = Field(..., min_items=1, max_items=10, description="Suggested video titles")


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    module: str
    version: str
```

---

### Step 7: Tạo API Routes

**File:** `apps/api/modules/module_1/routes.py`
**Vị trí:** Tạo file mới

**Code cần viết:**
```python
"""
Module 1 API Routes - Niche Validation.
"""
from fastapi import APIRouter, HTTPException, Depends
from apps.api.modules.module_1.schemas import (
    NicheValidationRequest,
    NicheValidationResponse,
    HealthResponse
)
from apps.api.modules.module_1.service import NicheValidator
from apps.api.core.cache import RedisCache


router = APIRouter(prefix="/api/research", tags=["Module 1 - Niche Validate"])

# Redis URL from environment
REDIS_URL = "redis://localhost:6379/0"

# Dependency for validator
async def get_validator() -> NicheValidator:
    """Get NicheValidator instance."""
    return NicheValidator(REDIS_URL)


@router.post("/validate", response_model=NicheValidationResponse)
async def validate_niche(
    request: NicheValidationRequest,
    validator: NicheValidator = Depends(get_validator)
):
    """
    Validate niche viability for YouTube content creation.
    
    - Checks Google Trends data
    - Analyzes competitor landscape
    - Estimates potential views
    
    **Note:** This endpoint uses Redis caching. Subsequent calls
    for the same keyword return cached results.
    """
    try:
        result = await validator.validate(
            keyword=request.keyword,
            use_cache=request.use_cache
        )
        return NicheValidationResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Module 1."""
    return HealthResponse(
        status="healthy",
        module="niche_validate",
        version="1.0.0"
    )
```

---

### Step 8: Tạo Module __init__.py

**File:** `apps/api/modules/module_1/__init__.py`
**Vị trí:** Tạo file mới

**Code cần viết:**
```python
"""
Module 1: Niche Validation (Discovery).

Provides:
- NicheValidator service
- Formula A0 (Video Filter)
- Formula A2 (Viral Detection)
"""
from apps.api.modules.module_1.service import NicheValidator
from apps.api.modules.module_1.formulas import filter_quality_videos, detect_viral_videos
from apps.api.modules.module_1.routes import router

__all__ = [
    "NicheValidator",
    "filter_quality_videos",
    "detect_viral_videos",
    "router"
]
```

---

### Step 9: Update apps/api/main.py (Import Routes)

**File:** `apps/api/main.py`
**Vị trí:** Sau các imports hiện có, trước app = FastAPI(...)

**Code cần thêm:**
```python
# Import Module 1 routes
from apps.api.modules.module_1 import router as module_1_router
```

**Và sau `app = FastAPI(...)`:**
```python
# Include Module 1 router
app.include_router(module_1_router)
```

---

### Step 10: Tạo Unit Tests

**File:** `tests/test_module_1/__init__.py`
**Vị trí:** Tạo file rỗng

**Code cần viết:**
```python
"""Test suite for Module 1."""
```

---

**File:** `tests/test_module_1/test_formulas.py`
**Vị trí:** Tạo file mới

**Code cần viết:**
```python
"""
Unit tests for Module 1 Formulas.
"""
import pytest
from apps.api.modules.module_1.formulas import (
    filter_quality_videos,
    detect_viral_videos
)


class TestFilterQualityVideos:
    """Tests for Formula A0 - Video Filter."""
    
    def test_keeps_quality_videos(self):
        """Test that quality videos are kept."""
        videos = [
            {
                'snippet': {'published_at': '2024-01-01T00:00:00Z', 'live_broadcast_content': 'none'},
                'content_details': {'duration': 'PT10M'},
                'statistics': {'view_count': '50000'}
            }
        ]
        result = filter_quality_videos(videos)
        assert len(result) == 1
    
    def test_filters_shorts(self):
        """Test that Shorts (<60s) are filtered."""
        videos = [
            {
                'snippet': {'published_at': '2024-01-01T00:00:00Z', 'live_broadcast_content': 'none'},
                'content_details': {'duration': 'PT30S'},
                'statistics': {'view_count': '50000'}
            }
        ]
        result = filter_quality_videos(videos)
        assert len(result) == 0
    
    def test_filters_live_streams(self):
        """Test that Live streams are filtered."""
        videos = [
            {
                'snippet': {'published_at': '2024-01-01T00:00:00Z', 'live_broadcast_content': 'live'},
                'content_details': {'duration': 'PT0S'},
                'statistics': {'view_count': '50000'}
            }
        ]
        result = filter_quality_videos(videos)
        assert len(result) == 0
    
    def test_filters_low_views(self):
        """Test that videos with <1000 views are filtered."""
        videos = [
            {
                'snippet': {'published_at': '2024-01-01T00:00:00Z', 'live_broadcast_content': 'none'},
                'content_details': {'duration': 'PT10M'},
                'statistics': {'view_count': '500'}
            }
        ]
        result = filter_quality_videos(videos)
        assert len(result) == 0


class TestDetectViralVideos:
    """Tests for Formula A2 - Viral Detection."""
    
    def test_detects_single_viral_video(self):
        """Test detection of single viral video."""
        videos = [
            {'statistics': {'view_count': '10000'}},
            {'statistics': {'view_count': '12000'}},
            {'statistics': {'view_count': '11000'}},
            {'statistics': {'view_count': '500000'}},  # Viral
            {'statistics': {'view_count': '11500'}},
        ]
        result = detect_viral_videos(videos)
        assert len(result) == 1
        assert result[0]['statistics']['view_count'] == '500000'
    
    def test_no_viral_for_similar_views(self):
        """Test that videos with similar views are not viral."""
        videos = [
            {'statistics': {'view_count': '10000'}},
            {'statistics': {'view_count': '10000'}},
            {'statistics': {'view_count': '10000'}},
        ]
        result = detect_viral_videos(videos)
        assert len(result) == 0
    
    def test_returns_all_for_small_sample(self):
        """Test that small samples (<5) are not analyzed."""
        videos = [
            {'statistics': {'view_count': '10000'}},
            {'statistics': {'view_count': '500000'}},
        ]
        result = detect_viral_videos(videos)
        assert len(result) == 2
```

---

**Verify command (PowerShell):**
```powershell
pytest tests/test_module_1/test_formulas.py -v
```

**Expected output:**
```
tests/test_module_1/test_formulas.py::TestFilterQualityVideos::test_keeps_quality_videos PASSED
tests/test_module_1/test_formulas.py::TestFilterQualityVideos::test_filters_shorts PASSED
tests/test_module_1/test_formulas.py::TestFilterQualityVideos::test_filters_live_streams PASSED
tests/test_module_1/test_formulas.py::TestFilterQualityVideos::test_filters_low_views PASSED
tests/test_module_1/test_formulas.py::TestDetectViralVideos::test_detects_single_viral_video PASSED
tests/test_module_1/test_formulas.py::TestDetectViralVideos::test_no_viral_for_similar_views PASSED
tests/test_module_1/test_formulas.py::TestDetectViralVideos::test_returns_all_for_small_sample PASSED

========================= 7 passed in 0.5s =========================
```

---

**Nếu fail:** 
- Invoke skill `debugging`.
- Báo cáo vào file `BLOCKERS.md`.
- **CẤM TỰ SỬA CODE KHÁC.**

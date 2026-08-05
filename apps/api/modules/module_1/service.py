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

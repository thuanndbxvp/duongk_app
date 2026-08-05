# Quy trình thực thi chi tiết (MSEW): Task 1.4 - Triển khai Module 1 (Niche Validate)

## BƯỚC 1: TokenBucket (utils/bulkhead.py)
```python
import time

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        self.tokens += (now - self.last_update) * self.rate
        if self.tokens > self.capacity: self.tokens = self.capacity
        self.last_update = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
```

## BƯỚC 2: Fallback Service
Trong `apps/api/services/trends.py`:
- Khởi tạo `bucket = TokenBucket(rate=0.1, capacity=5)` (5 req/50s).
- Gọi `if bucket.consume(): try pytrends... else: call SerpAPI`.

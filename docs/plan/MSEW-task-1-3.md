# Quy trình thực thi chi tiết (MSEW): Task 1.3 - Xây dựng YouTube Client & Quota Engine

## BƯỚC 1: YouTubeClient Core
Tạo file `apps/api/services/youtube.py`:
```python
import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

class QuotaExceededError(Exception): pass

class YouTubeClient:
    def __init__(self, api_keys: list[str]):
        self.api_keys = api_keys
        self.current_key_idx = 0
        
    def _get_key(self):
        return self.api_keys[self.current_key_idx]

    def _rotate_key(self):
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)

    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
    async def request(self, endpoint: str, params: dict):
        params['key'] = self._get_key()
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://www.googleapis.com/youtube/v3/{endpoint}", params=params)
            if resp.status_code == 403: # Quota exceeded
                self._rotate_key()
                raise QuotaExceededError("Quota exhausted, rotated key.")
            resp.raise_for_status()
            return resp.json()
```

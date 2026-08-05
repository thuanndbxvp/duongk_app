# Sprint 3 Task Group 5: Integration - Skill Routing

## Allowed Commands
- ✅ Read, Write, StrReplace, Delete
- ✅ ReadLints, self-fix linter
- ✅ pytest, pytest-asyncio

## Not Allowed
- ❌ Không đổi core logic (Task Groups 1-4)
- ❌ Không tạo migrations
- ❌ Không launch subagents

## Patterns
```python
# Integration test
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_full_flow():
    async with AsyncClient(base_url="http://test") as client:
        response = await client.post("/api/scripts/generate", ...)
        assert response.status_code == 201

# Mock Supabase for tests
@pytest.fixture
def mock_supabase():
    ...
```

## Files to Create
- ✅ `tests/integration/test_script_flow.py`
- ✅ `tests/unit/test_api_scripts.py`
- ✅ `apps/api/routers/scripts.py` (update - add GET endpoint)

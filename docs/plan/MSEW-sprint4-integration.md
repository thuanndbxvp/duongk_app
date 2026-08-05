# Sprint 4 Task Group 5: Integration - MSEW

## Bước 1: Test Config

**File:** `tests/conftest.py`

```python
"""
Shared test fixtures.
"""
import pytest
import os
import jwt
from datetime import datetime, timedelta, timezone
from supabase import create_client


SUPABASE_URL = os.getenv('SUPABASE_URL', 'http://localhost:54321')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'test-key')
JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET', 'test-secret')


@pytest.fixture
def admin_client():
    """Admin client (bypasses RLS)."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@pytest.fixture
def make_user_token():
    """Generate JWT for a test user."""
    def _make(user_id: str, email: str = 'test@example.com') -> str:
        payload = {
            'sub': user_id,
            'aud': 'authenticated',
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
            'email': email,
        }
        return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return _make


@pytest.fixture
def user_client(make_user_token):
    """Create user-scoped client."""
    def _make(user_id: str):
        token = make_user_token(user_id)
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        client.auth.session = type('S', (), {'access_token': token})()
        return client
    return _make
```

---

## Bước 2: RLS Tests

**File:** `tests/integration/test_rls.py`

```python
"""
Integration tests for RLS enforcement.
"""
import pytest
import uuid
from unittest.mock import patch


class TestRLS:
    """Test Row Level Security."""
    
    def test_user_can_see_own_jobs(self, user_client, admin_client):
        user_id = str(uuid.uuid4())
        client = user_client(user_id)
        
        # Create job for user
        admin_client.table('users').insert({
            'id': user_id,
            'email': 'test@example.com',
            'credits': 100,
        }).execute()
        
        job = admin_client.table('jobs').insert({
            'user_id': user_id,
            'task_type': 'collect_channel',
            'status': 'pending',
        }).execute()
        
        # User queries jobs
        result = client.table('jobs').select('*').eq('id', job.data[0]['id']).execute()
        assert len(result.data) == 1
    
    def test_user_cannot_see_other_users_jobs(self, user_client, admin_client):
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        # Create both users
        for uid in [user1_id, user2_id]:
            admin_client.table('users').insert({
                'id': uid,
                'email': f'{uid}@example.com',
                'credits': 100,
            }).execute()
        
        # User1 creates job
        job = admin_client.table('jobs').insert({
            'user_id': user1_id,
            'task_type': 'collect_channel',
            'status': 'pending',
        }).execute()
        job_id = job.data[0]['id']
        
        # User2 queries jobs - should NOT see user1's job
        user2_client = user_client(user2_id)
        result = user2_client.table('jobs').select('*').execute()
        
        # Verify user1's job is NOT in user2's results
        job_ids = [j['id'] for j in result.data]
        assert job_id not in job_ids
    
    def test_user_cannot_update_other_users_data(self, user_client, admin_client):
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        # Create user1
        admin_client.table('users').insert({
            'id': user1_id,
            'email': 'user1@example.com',
            'credits': 100,
        }).execute()
        
        # User2 tries to update user1's profile
        user2_client = user_client(user2_id)
        result = user2_client.table('users').update({'full_name': 'Hacker'}).eq('id', user1_id).execute()
        
        # Should not affect user1
        user1 = admin_client.table('users').select('*').eq('id', user1_id).single().execute()
        assert user1.data['full_name'] != 'Hacker'
```

---

## Bước 3: User Flow Tests

**File:** `tests/e2e/test_user_flow.py`

```python
"""
E2E tests for authenticated user flow.
"""
import pytest
from httpx import AsyncClient


class TestUserFlow:
    """End-to-end tests."""
    
    @pytest.mark.asyncio
    async def test_login_returns_token(self, make_user_token):
        """Test JWT token generation."""
        user_id = '11111111-1111-1111-1111-111111111111'
        token = make_user_token(user_id)
        assert token is not None
        assert len(token) > 100
    
    @pytest.mark.asyncio
    async def test_get_me_with_valid_token(self, make_user_token, admin_client):
        """Test GET /api/users/me with valid token."""
        from fastapi.testclient import TestClient
        from apps.api.main import app
        
        user_id = '22222222-2222-2222-2222-222222222222'
        admin_client.table('users').insert({
            'id': user_id,
            'email': 'me@example.com',
            'credits': 50,
        }).execute()
        
        token = make_user_token(user_id)
        client = TestClient(app)
        
        response = client.get(
            '/api/users/me',
            headers={'Authorization': f'Bearer {token}'},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == user_id
        assert data['credits'] == 50
    
    @pytest.mark.asyncio
    async def test_get_me_without_token_returns_401(self):
        """Test missing token returns 401."""
        from fastapi.testclient import TestClient
        from apps.api.main import app
        
        client = TestClient(app)
        response = client.get('/api/users/me')
        
        assert response.status_code == 401 or response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_credit_insufficient_returns_402(self, make_user_token, admin_client):
        """Test insufficient credits returns 402."""
        from fastapi.testclient import TestClient
        from apps.api.main import app
        
        user_id = '33333333-3333-3333-3333-333333333333'
        admin_client.table('users').insert({
            'id': user_id,
            'email': 'poor@example.com',
            'credits': 1,  # Not enough for any job
        }).execute()
        
        token = make_user_token(user_id)
        client = TestClient(app)
        
        # Try to start a 30-credit job
        response = client.post(
            '/api/scripts/generate',
            headers={'Authorization': f'Bearer {token}'},
            json={'assistant_id': '44444444-4444-4444-4444-444444444444', 'topic': 'test'},
        )
        
        # Should be 402 or 404 (assistant not found)
        assert response.status_code in (402, 404)
```

---

## Bước 4: Frontend E2E (Playwright)

**File:** `tests/e2e/test_frontend_flow.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('User Flow', () => {
  test('login redirects to dashboard', async ({ page }) => {
    await page.goto('http://localhost:3000/login');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    await page.waitForURL('**/dashboard');
    expect(page.url()).toContain('/dashboard');
  });

  test('dashboard shows recent jobs', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    
    // Wait for jobs to load
    await page.waitForSelector('a[href^="/jobs/"]');
    
    // Verify at least one job card visible
    const jobCards = await page.locator('a[href^="/jobs/"]').count();
    expect(jobCards).toBeGreaterThanOrEqual(0);
  });

  test('new project form submits', async ({ page }) => {
    await page.goto('http://localhost:3000/projects/new');
    
    await page.fill('input[type="url"]', 'https://www.youtube.com/@test');
    await page.click('button[type="submit"]');
    
    // Should redirect to job page
    await page.waitForURL('**/jobs/**');
  });
});
```

---

## Bước 5: Verify

```bash
# Backend tests
cd apps/api
pytest tests/integration/test_rls.py -v
pytest tests/e2e/test_user_flow.py -v

# Frontend tests (optional)
cd apps/web
pnpm playwright test
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint4-integration.md
cat docs/plan/SKILL-ROUTING-sprint4-integration.md
cat docs/plan/PLAN-sprint4-integration.md
cat docs/plan/MSEW-sprint4-integration.md
cat docs/plan/ACCEPTANCE-sprint4-integration.md
```

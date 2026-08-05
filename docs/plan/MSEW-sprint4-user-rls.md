# Sprint 4 Task Group 1: User & RLS - MSEW

## Checklist

- [ ] Bước 1: Update requirements.txt
- [ ] Bước 2: Update .env.example
- [ ] Bước 3: SQL - Enable RLS + Policies
- [ ] Bước 4: Create JWT auth dependency
- [ ] Bước 5: Create user router
- [ ] Bước 6: Unit tests
- [ ] Bước 7: Verify

---

## Bước 1: Update requirements.txt

**File:** `requirements.txt`

Thêm vào cuối file:

```txt
# Authentication (Sprint 4)
PyJWT>=2.8.0
cryptography>=42.0.0
```

---

## Bước 2: Update .env.example

**File:** `.env.example`

Thêm section:

```bash
# Supabase Auth (Sprint 4)
SUPABASE_JWT_SECRET=your-jwt-secret-here

# Get from: Supabase Dashboard > Settings > API > JWT Secret
```

---

## Bước 3: SQL Migration

**File:** `supabase/migrations/0017_enable_rls_policies.sql`

```sql
-- ============================================================
-- Migration: 0017_enable_rls_policies.sql
-- Purpose: Enable RLS + policies for production users
-- ============================================================

-- 1. Users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_data" ON users;
CREATE POLICY "users_own_data" ON users FOR ALL
  USING (id = auth.uid());

-- 2. Jobs table
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_jobs" ON jobs;
CREATE POLICY "users_own_jobs" ON jobs FOR ALL
  USING (user_id = auth.uid());

-- 3. Credit transactions
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_credit_tx" ON credit_transactions;
CREATE POLICY "users_own_credit_tx" ON credit_transactions FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM users u
      WHERE u.id = credit_transactions.user_id
        AND u.id = auth.uid()
    )
  );

-- 4. Channel assistants
ALTER TABLE channel_assistants ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_assistants" ON channel_assistants;
CREATE POLICY "users_own_assistants" ON channel_assistants FOR ALL
  USING (user_id = auth.uid());

-- 5. Channel deep analysis (via assistant)
ALTER TABLE channel_deep_analysis ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_analysis" ON channel_deep_analysis;
CREATE POLICY "users_own_analysis" ON channel_deep_analysis FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = channel_deep_analysis.assistant_id
        AND ca.user_id = auth.uid()
    )
  );

-- 6. DNA chunks (via assistant)
ALTER TABLE dna_chunks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_chunks" ON dna_chunks;
CREATE POLICY "users_own_chunks" ON dna_chunks FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = dna_chunks.assistant_id
        AND ca.user_id = auth.uid()
    )
  );

-- 7. Generated ideas (via assistant)
ALTER TABLE generated_ideas ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_ideas" ON generated_ideas;
CREATE POLICY "users_own_ideas" ON generated_ideas FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = generated_ideas.assistant_id
        AND ca.user_id = auth.uid()
    )
  );

-- 8. Generated scripts (via assistant)
ALTER TABLE generated_scripts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_scripts" ON generated_scripts;
CREATE POLICY "users_own_scripts" ON generated_scripts FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = generated_scripts.assistant_id
        AND ca.user_id = auth.uid()
    )
  );

-- Note: service_role bypasses RLS by default (for Celery worker)
```

---

## Bước 4: JWT Auth Dependency

**File:** `apps/api/dependencies/auth.py`

```python
"""
JWT authentication dependency for FastAPI.
Uses PyJWT to verify Supabase Auth tokens.
"""
import os
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


security = HTTPBearer()


def get_supabase_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Verify JWT from Supabase Auth and return user_id.
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        user_id (UUID string) from JWT 'sub' claim
        
    Raises:
        HTTPException: 401 if token invalid, 500 if server misconfigured
    """
    token = credentials.credentials
    secret = os.getenv('SUPABASE_JWT_SECRET')
    
    if not secret:
        raise HTTPException(
            status_code=500,
            detail='Server misconfigured: SUPABASE_JWT_SECRET not set',
        )
    
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=['HS256'],
            audience='authenticated',
            options={
                'require': ['exp', 'sub', 'aud'],
                'verify_signature': True,
                'verify_exp': True,
                'verify_aud': True,
            },
        )
        return payload['sub']
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, 'Token expired')
    except jwt.InvalidAudienceError:
        raise HTTPException(401, 'Invalid token audience')
    except jwt.InvalidTokenError as e:
        raise HTTPException(401, f'Invalid token: {str(e)}')
```

---

## Bước 5: User Router

**File:** `apps/api/routers/users.py`

```python
"""
User endpoints - Get/update current user info.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin


router = APIRouter()


class UserUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    avatar_url: str | None
    credits: int
    tier: str
    created_at: str


@router.get('/users/me', response_model=UserResponse)
async def get_me(user_id: str = Depends(get_supabase_user)):
    """Get current user info."""
    admin = get_supabase_admin()
    
    user = (
        admin.table('users')
        .select('*')
        .eq('id', user_id)
        .single()
        .execute()
    )
    
    if not user.data:
        raise HTTPException(404, 'User not found')
    
    return user.data


@router.patch('/users/me', response_model=UserResponse)
async def update_me(
    update: UserUpdate,
    user_id: str = Depends(get_supabase_user),
):
    """Update current user profile."""
    admin = get_supabase_admin()
    
    update_data = update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(400, 'No fields to update')
    
    result = (
        admin.table('users')
        .update(update_data)
        .eq('id', user_id)
        .execute()
    )
    
    if not result.data:
        raise HTTPException(404, 'User not found')
    
    return result.data[0]


@router.get('/users/me/credits')
async def get_my_credits(user_id: str = Depends(get_supabase_user)):
    """Get current user credit balance."""
    admin = get_supabase_admin()
    
    user = (
        admin.table('users')
        .select('credits, tier')
        .eq('id', user_id)
        .single()
        .execute()
    )
    
    if not user.data:
        raise HTTPException(404, 'User not found')
    
    return {
        'credits': user.data['credits'],
        'tier': user.data['tier'],
    }
```

---

## Bước 6: Unit Tests

**File:** `apps/api/dependencies/test_auth.py`

```python
"""
Unit tests for JWT auth dependency.
"""
import os
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient


SECRET = 'test-secret-12345'
USER_ID = '11111111-1111-1111-1111-111111111111'


@pytest.fixture(autouse=True)
def mock_secret():
    """Mock JWT secret."""
    os.environ['SUPABASE_JWT_SECRET'] = SECRET


@pytest.fixture
def valid_token():
    """Generate valid JWT token."""
    payload = {
        'sub': USER_ID,
        'aud': 'authenticated',
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        'email': 'test@example.com',
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')


@pytest.fixture
def expired_token():
    """Generate expired JWT token."""
    payload = {
        'sub': USER_ID,
        'aud': 'authenticated',
        'exp': datetime.now(timezone.utc) - timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')


@pytest.fixture
def wrong_signature_token():
    """Generate token with wrong signature."""
    payload = {
        'sub': USER_ID,
        'aud': 'authenticated',
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, 'wrong-secret', algorithm='HS256')


@pytest.fixture
def wrong_audience_token():
    """Generate token with wrong audience."""
    payload = {
        'sub': USER_ID,
        'aud': 'anon',
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')


@pytest.fixture
def missing_claims_token():
    """Generate token missing required claims."""
    payload = {
        'sub': USER_ID,
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        # Missing 'aud'
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')


class TestGetSupabaseUser:
    """Test JWT verify function."""

    def test_valid_token_returns_user_id(self, valid_token):
        """Test: valid token returns user_id."""
        from apps.api.dependencies.auth import get_supabase_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials=valid_token)
        user_id = get_supabase_user(credentials=creds)
        assert user_id == USER_ID

    def test_expired_token_raises_401(self, expired_token):
        """Test: expired token returns 401."""
        from apps.api.dependencies.auth import get_supabase_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials=expired_token)
        
        with pytest.raises(HTTPException) as exc:
            get_supabase_user(credentials=creds)
        assert exc.value.status_code == 401
        assert 'expired' in exc.value.detail.lower()

    def test_wrong_signature_raises_401(self, wrong_signature_token):
        """Test: forged token (wrong secret) returns 401."""
        from apps.api.dependencies.auth import get_supabase_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials=wrong_signature_token)
        
        with pytest.raises(HTTPException) as exc:
            get_supabase_user(credentials=creds)
        assert exc.value.status_code == 401

    def test_wrong_audience_raises_401(self, wrong_audience_token):
        """Test: wrong audience returns 401."""
        from apps.api.dependencies.auth import get_supabase_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials=wrong_audience_token)
        
        with pytest.raises(HTTPException) as exc:
            get_supabase_user(credentials=creds)
        assert exc.value.status_code == 401

    def test_missing_claims_raises_401(self, missing_claims_token):
        """Test: missing required claims returns 401."""
        from apps.api.dependencies.auth import get_supabase_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials=missing_claims_token)
        
        with pytest.raises(HTTPException) as exc:
            get_supabase_user(credentials=creds)
        assert exc.value.status_code == 401

    def test_no_secret_raises_500(self):
        """Test: missing JWT secret returns 500."""
        from apps.api.dependencies.auth import get_supabase_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        os.environ.pop('SUPABASE_JWT_SECRET', None)
        
        creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials='any-token')
        
        with pytest.raises(HTTPException) as exc:
            get_supabase_user(credentials=creds)
        assert exc.value.status_code == 500
```

---

## Bước 7: Verify

```bash
# Install deps
pip install PyJWT>=2.8.0 cryptography pytest pytest-asyncio

# Apply migration (only on staging/test DB)
supabase db push

# Run tests
cd apps/api
pytest dependencies/test_auth.py -v

# Check coverage
pytest --cov=apps.api.dependencies.auth --cov-report=term-missing
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint4-user-rls.md
cat docs/plan/SKILL-ROUTING-sprint4-user-rls.md
cat docs/plan/PLAN-sprint4-user-rls.md
cat docs/plan/MSEW-sprint4-user-rls.md
cat docs/plan/ACCEPTANCE-sprint4-user-rls.md
```

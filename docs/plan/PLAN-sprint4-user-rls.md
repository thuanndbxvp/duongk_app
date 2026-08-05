# Sprint 4 Task Group 1: User & RLS - Plan

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│  USER AUTHENTICATION FLOW                                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User Browser    Next.js BFF        FastAPI         Supabase     │
│     │                │                  │              │          │
│     │  1. Login ────▶│                  │              │          │
│     │                │ 2. POST /auth ─────────────────▶│          │
│     │                │                  │              │          │
│     │                │ 3. JWT tokens ◀────────────────│          │
│     │                │                  │              │          │
│     │  4. JWT ─────▶│                  │              │          │
│     │                │ 5. API call ───▶│              │          │
│     │                │    + JWT        │ 6. verify JWT (PyJWT)    │
│     │                │                  │              │          │
│     │                │                  │ 7. SQL query với auth.uid()│
│     │                │                  │ 8. RLS enforce ──────────▶│
│     │                │                  │              │ 9. Return rows│
│     │                │                  │ ◀────────────│            │
│     │                │                  │              │          │
│     │                │ 10. Response ───▶│              │          │
│     │  11. Data ────▶│                  │              │          │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Security Flow

```
Request → HTTPBearer Header → JWT Decode (PyJWT) → Extract user_id
                                              ↓
                         Verify signature (HS256 + SUPABASE_JWT_SECRET)
                                              ↓
                         Verify audience = 'authenticated'
                                              ↓
                         Verify exp not expired
                                              ↓
                         Extract payload['sub'] = user_id
                                              ↓
                              Pass to FastAPI endpoint
                                              ↓
                         SQL query auto-filtered by RLS
```

## Files to Create

### 1. SQL Migration

**File:** `supabase/migrations/0017_enable_rls_policies.sql`

- Enable RLS cho 8 tables
- Create policies cho từng table
- Backup policies cho service_role bypass

### 2. Auth Dependency

**File:** `apps/api/dependencies/auth.py`

- `get_supabase_user()` dependency
- Verify JWT với PyJWT
- Handle expired/invalid tokens

### 3. User Router

**File:** `apps/api/routers/users.py`

- `GET /api/users/me` - Get current user info
- `PATCH /api/users/me` - Update profile
- `GET /api/users/me/credits` - Get credit balance

### 4. Unit Tests

**File:** `apps/api/dependencies/test_auth.py`

- Test valid token
- Test invalid signature
- Test expired token
- Test missing claims

---

## Data Flow

### 1. JWT Verify

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os

security = HTTPBearer()

def get_supabase_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Verify JWT and return user_id."""
    token = credentials.credentials
    secret = os.getenv('SUPABASE_JWT_SECRET')
    
    if not secret:
        raise HTTPException(500, 'Server misconfigured')
    
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
    except jwt.InvalidTokenError:
        raise HTTPException(401, 'Invalid token')
```

### 2. RLS Policy

```sql
-- Enable RLS
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Users chỉ thấy jobs của họ
CREATE POLICY "users_own_jobs" ON jobs FOR ALL
  USING (user_id = auth.uid());

-- Service role bypass RLS (cho Celery worker)
-- (Supabase mặc định: service_role bypass RLS)
```

### 3. User Endpoint

```python
@router.get('/users/me')
async def get_me(user_id: str = Depends(get_supabase_user)):
    admin = get_supabase_admin()
    user = admin.table('users').select('*').eq('id', user_id).single().execute()
    
    if not user.data:
        raise HTTPException(404, 'User not found')
    
    return user.data
```

---

## Constraints

1. **JWT secret phải từ env** - không hardcode
2. **Use `audience='authenticated'`** - đúng Supabase convention
3. **Handle all JWT errors** - 401 cho invalid, không 500
4. **Test signature verification** - reject forged tokens
5. **RLS phải apply** khi dùng user-scoped client
6. **Service role bypass RLS** - cho Celery worker (đã default)

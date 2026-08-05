# Sprint 4 Task Group 1: User & RLS - Skill Routing

## Commands ĐƯỢC PHÉP

### File Operations
- ✅ Read, Write, StrReplace, Delete
- ✅ ReadLints, self-fix

### Dependencies
- ✅ Install `PyJWT>=2.8.0` qua pip
- ✅ Add to `requirements.txt`

### Code Patterns
- ✅ PyJWT cho JWT verify
- ✅ Supabase Auth client

---

## Commands KHÔNG ĐƯỢC PHÉP

- ❌ Deploy migration lên production
- ❌ Xóa existing tables
- ❌ Launch subagents
- ❌ Dùng `verify_signature:False` (CRITICAL SECURITY)

---

## Skills BẮT BUỘC

### 1. PyJWT Pattern

```python
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_supabase_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            os.getenv('SUPABASE_JWT_SECRET'),
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

### 2. SQL RLS Pattern

```sql
ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;
CREATE POLICY "policy_name" ON <table> FOR ALL
  USING (user_id = auth.uid());
```

---

## File Paths KHÔNG ĐƯỢC SỬA

- ❌ `apps/api/main.py` (existing imports)
- ❌ `supabase/migrations/0001-0016_*` (đã chạy)
- ❌ `apps/worker/*` (worker dùng service_role, bypass RLS)

---

## Files CÓ THỂ TẠO

- ✅ `supabase/migrations/0017_enable_rls_policies.sql`
- ✅ `apps/api/dependencies/auth.py`
- ✅ `apps/api/dependencies/test_auth.py`
- ✅ `apps/api/routers/users.py`
- ✅ `.env.example` (update)
- ✅ `requirements.txt` (add PyJWT)

---

## Dependencies Cần Cài

```bash
pip install PyJWT>=2.8.0 pytest pytest-asyncio pytest-cov httpx
```

---

## Security Critical Notes

🔴 **KHÔNG BAO GIỜ** dùng:
```python
payload = jwt.decode(token, options={'verify_signature': False})
```

✅ **PHẢI** dùng:
```python
payload = jwt.decode(token, SECRET, algorithms=['HS256'], audience='authenticated')
```

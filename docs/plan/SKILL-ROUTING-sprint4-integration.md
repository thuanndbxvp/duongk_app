# Sprint 4 Task Group 5: Integration - Skill Routing

## Commands ĐƯỢC PHÉP
- ✅ Read, Write, StrReplace
- ✅ pytest, pytest-asyncio
- ✅ Playwright (optional)

## Commands KHÔNG ĐƯỢC PHÉP
- ❌ Đổi Task 1-4 code
- ❌ Launch subagents

## Patterns BẮT BUỘC

### 1. Test Database

```python
@pytest.fixture
def test_db():
    """Use staging/test database, NOT production."""
    return get_supabase_admin()  # with test URL
```

### 2. RLS Test

```python
def test_rls_blocks_other_user():
    user1_client = create_client(...)  # user1 token
    user2_client = create_client(...)  # user2 token
    
    # user1 creates job
    user1.table('jobs').insert(...)
    
    # user2 should NOT see user1's job
    result = user2.table('jobs').select('*').execute()
    assert len(result.data) == 0
```

### 3. Auth Header

```python
def get_auth_header(user_id: str) -> dict:
    token = generate_test_token(user_id)
    return {'Authorization': f'Bearer {token}'}
```

---

## Files CÓ THỂ TẠO
- ✅ `tests/e2e/test_user_flow.py`
- ✅ `tests/e2e/test_frontend_flow.spec.ts`
- ✅ `tests/integration/test_rls.py`
- ✅ `tests/conftest.py`

## Files KHÔNG ĐƯỢC SỬA
- ❌ All Task 1-4 files

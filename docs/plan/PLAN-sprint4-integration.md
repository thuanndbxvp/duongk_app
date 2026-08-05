# Sprint 4 Task Group 5: Integration - Plan

## E2E Test Plan

### 1. Authentication Flow

```python
def test_signup_creates_user():
    # POST /api/auth/signup
    # Verify user created in DB
    # Verify can login
```

### 2. RLS Enforcement

```python
def test_user_cannot_access_other_users_jobs():
    # user1 creates job
    # user2 logs in
    # user2 cannot see user1's job
```

### 3. Credit System

```python
def test_free_user_charged_correctly():
    # Start analysis job
    # Verify credits deducted
    # Verify transaction recorded
```

### 4. Full Pipeline

```python
def test_full_pipeline():
    # Login → Create project → Wait job → Check script
```

## Files to Create

### 1. Backend Tests

- `tests/e2e/test_user_flow.py`
- `tests/integration/test_rls.py`
- `tests/conftest.py`

### 2. Frontend Tests

- `tests/e2e/test_frontend_flow.spec.ts` (Playwright)

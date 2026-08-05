# Sprint 4 Task Group 5: Integration & E2E Tests

## 1. Context & Mục đích

### Mục đích

Sprint 4.5 đảm bảo **End-to-End** flow từ User đến Frontend hoạt động:
1. User đăng ký/đăng nhập
2. Tạo project (URL → Start job)
3. Realtime progress
4. Script editor
5. Credit deduction

### Dependencies

- ✅ Task 1: User/RLS
- ✅ Task 2: Next.js BFF
- ✅ Task 3: Credit System
- ✅ Task 4: Frontend Dashboard

---

## 2. E2E Test Scenarios

| # | Test | Expected |
|---|------|----------|
| E1 | Signup → Login → Dashboard | 200 OK |
| E2 | Free user → Start analysis | 402 (insufficient) |
| E3 | Pro user → Start analysis | 200, credits deducted |
| E4 | Realtime progress updates | UI updates without refresh |
| E5 | RLS blocks cross-user access | 403 |
| E6 | Script editor saves | 200 OK |

---

## 3. Files to Create

| File | Purpose |
|------|---------|
| `tests/e2e/test_user_flow.py` | E2E backend tests |
| `tests/e2e/test_frontend_flow.spec.ts` | Playwright tests |
| `tests/integration/test_rls.py` | RLS enforcement tests |
| `tests/conftest.py` | Fixtures |

---

## 4. Acceptance Summary

| # | Criteria |
|---|----------|
| AC1 | E2E backend tests pass |
| AC2 | RLS enforces isolation |
| AC3 | Credit hold/charge works |
| AC4 | Realtime updates |
| AC5 | Frontend tests pass |

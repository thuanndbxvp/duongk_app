# Sprint 4 Task Group 5: Integration - Acceptance Criteria

## Definition of Done

---

## AC1: Test Setup

- [ ] **AC1.1:** `tests/conftest.py` with fixtures
- [ ] **AC1.2:** `make_user_token` fixture
- [ ] **AC1.3:** `user_client` fixture
- [ ] **AC1.4:** `admin_client` fixture

---

## AC2: RLS Tests

- [ ] **AC2.1:** `test_user_can_see_own_jobs` - positive case
- [ ] **AC2.2:** `test_user_cannot_see_other_users_jobs` - isolation
- [ ] **AC2.3:** `test_user_cannot_update_other_users_data` - UPDATE blocked
- [ ] **AC2.4:** All pass

### Test AC2:

```bash
pytest tests/integration/test_rls.py -v
```

---

## AC3: User Flow Tests

- [ ] **AC3.1:** `test_login_returns_token` works
- [ ] **AC3.2:** `test_get_me_with_valid_token` returns user
- [ ] **AC3.3:** `test_get_me_without_token` returns 401
- [ ] **AC3.4:** `test_credit_insufficient` returns 402

---

## AC4: Frontend E2E

- [ ] **AC4.1:** Login redirects to dashboard
- [ ] **AC4.2:** Dashboard loads jobs
- [ ] **AC4.3:** New project form submits
- [ ] **AC4.4:** Playwright tests pass

---

## AC5: Full Pipeline

- [ ] **AC5.1:** E2E: signup → login → create project → start job
- [ ] **AC5.2:** Realtime progress updates visible
- [ ] **AC5.3:** Script editor saves
- [ ] **AC5.4:** Credits deducted correctly

---

## AC6: Code Quality

- [ ] **AC6.1:** Test coverage ≥ 80% cho Sprint 4 code
- [ ] **AC6.2:** No flaky tests
- [ ] **AC6.3:** CI integration (nếu có)

---

## Self-Check

1. [ ] All AC1-AC6 ✅
2. [ ] `pytest tests/ -v` → PASSED
3. [ ] E2E tests documented

---

## Sign-off

```
✓ Task: Sprint 4 - Integration
✓ Status: COMPLETED
✓ Files Created:
  - tests/conftest.py
  - tests/integration/test_rls.py
  - tests/e2e/test_user_flow.py
  - tests/e2e/test_frontend_flow.spec.ts
✓ All Acceptance Criteria: PASSED
✓ SPRINT 4 COMPLETE
```

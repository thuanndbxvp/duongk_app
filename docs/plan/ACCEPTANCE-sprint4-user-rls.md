# Sprint 4 Task Group 1: User & RLS - Acceptance Criteria

## Definition of Done

---

## AC1: Dependencies

- [ ] **AC1.1:** `PyJWT>=2.8.0` added to `requirements.txt`
- [ ] **AC1.2:** `cryptography>=42.0.0` added
- [ ] **AC1.3:** `SUPABASE_JWT_SECRET` added to `.env.example`

### Test AC1:

```bash
grep -E "PyJWT|cryptography" requirements.txt
grep "SUPABASE_JWT_SECRET" .env.example
```

---

## AC2: SQL Migration

- [ ] **AC2.1:** Migration `0017_enable_rls_policies.sql` exists
- [ ] **AC2.2:** All 8 tables have `ENABLE ROW LEVEL SECURITY`
- [ ] **AC2.3:** Each table has policy matching ownership pattern
- [ ] **AC2.4:** Comments explain service_role bypass

### Test AC2:

```sql
-- Verify all tables RLS enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public'
  AND tablename IN ('users', 'jobs', 'credit_transactions', 'channel_assistants',
                    'channel_deep_analysis', 'dna_chunks', 'generated_ideas', 'generated_scripts');
```

---

## AC3: JWT Verify (CRITICAL SECURITY)

- [ ] **AC3.1:** Function `get_supabase_user()` exists
- [ ] **AC3.2:** Uses PyJWT với `algorithms=['HS256']`
- [ ] **AC3.3:** Uses `SUPABASE_JWT_SECRET` từ env (NOT hardcoded)
- [ ] **AC3.4:** Verifies `audience='authenticated'`
- [ ] **AC3.5:** Verifies `signature=True` (NOT `verify_signature:False`)
- [ ] **AC3.6:** Requires `exp`, `sub`, `aud` claims
- [ ] **AC3.7:** Returns 401 for expired/invalid tokens
- [ ] **AC3.8:** Returns 500 if secret not set

### Test AC3:

```python
# Test invalid token
creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials='forged-token')
with pytest.raises(HTTPException) as exc:
    get_supabase_user(credentials=creds)
assert exc.value.status_code == 401
```

---

## AC4: User Endpoints

- [ ] **AC4.1:** `GET /api/users/me` returns current user
- [ ] **AC4.2:** `PATCH /api/users/me` updates profile
- [ ] **AC4.3:** `GET /api/users/me/credits` returns balance
- [ ] **AC4.4:** All endpoints require valid JWT
- [ ] **AC4.5:** Returns 404 for missing user

### Test AC4:

```bash
# Test GET /api/users/me
curl -H "Authorization: Bearer <valid-token>" http://localhost:8000/api/users/me
# Expect: 200 OK with user JSON

# Test invalid token
curl -H "Authorization: Bearer invalid" http://localhost:8000/api/users/me
# Expect: 401
```

---

## AC5: Unit Tests

- [ ] **AC5.1:** Test file exists: `test_auth.py`
- [ ] **AC5.2:** Test valid token returns user_id
- [ ] **AC5.3:** Test expired token returns 401
- [ ] **AC5.4:** Test forged token (wrong signature) returns 401
- [ ] **AC5.5:** Test wrong audience returns 401
- [ ] **AC5.6:** Test missing claims returns 401
- [ ] **AC5.7:** Test missing JWT secret returns 500
- [ ] **AC5.8:** All tests pass

### Test AC5:

```bash
pytest apps/api/dependencies/test_auth.py -v
```

---

## AC6: Security

- [ ] **AC6.1:** NO `verify_signature:False` anywhere
- [ ] **AC6.2:** JWT secret loaded from env, not hardcoded
- [ ] **AC6.3:** Failed auth returns 401, not 500
- [ ] **AC6.4:** Service role bypasses RLS (worker can access all)

---

## AC7: Code Quality

- [ ] **AC7.1:** Type hints đầy đủ
- [ ] **AC7.2:** Docstrings cho functions
- [ ] **AC7.3:** Test coverage ≥ 90% cho auth.py
- [ ] **AC7.4:** No linter errors

---

## Self-Check

1. [ ] All AC1-AC7 ✅
2. [ ] `pytest test_auth.py -v` → PASSED
3. [ ] `ReadLints` → No errors
4. [ ] NO `verify_signature:False` in code

---

## Sign-off

```
✓ Task: Sprint 4 - User & Database Security
✓ Status: COMPLETED
✓ Files Created:
  - supabase/migrations/0017_enable_rls_policies.sql
  - apps/api/dependencies/auth.py
  - apps/api/dependencies/test_auth.py
  - apps/api/routers/users.py
  - requirements.txt (updated)
  - .env.example (updated)
✓ All Acceptance Criteria: PASSED
✓ Ready for next task group: Next.js BFF
```

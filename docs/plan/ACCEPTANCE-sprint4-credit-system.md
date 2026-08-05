# Sprint 4 Task Group 3: Credit System - Acceptance Criteria

## Definition of Done

---

## AC1: SQL Migration

- [ ] **AC1.1:** `0018_credit_tiers.sql` exists
- [ ] **AC1.2:** `credit_pricing` table has 7 job types
- [ ] **AC1.3:** `hold_credits` RPC exists
- [ ] **AC1.4:** `refund_credits` RPC exists
- [ ] **AC1.5:** Atomic with `FOR UPDATE` lock

### Test AC1:

```sql
SELECT * FROM credit_pricing WHERE job_type = 'script_generation';
-- Expect: credits = 30

SELECT * FROM hold_credits('uuid', 30, 'job-uuid');
-- Expect: returns transaction_id, balance_after
```

---

## AC2: Credit Manager

- [ ] **AC2.1:** `CreditManager` class exists
- [ ] **AC2.2:** `get_pricing()` returns correct cost
- [ ] **AC2.3:** `get_balance()` returns user credits
- [ ] **AC2.4:** `hold()` calls RPC correctly
- [ ] **AC2.5:** `adjust()` calls partial_commit
- [ ] **AC2.6:** `refund()` calls refund_credits

### Test AC2:

```python
manager = CreditManager()
assert manager.get_pricing('script_generation') == 30
```

---

## AC3: Credit Dependency

- [ ] **AC3.1:** `credit_required()` dependency exists
- [ ] **AC3.2:** Checks balance before processing
- [ ] **AC3.3:** Returns 402 if insufficient
- [ ] **AC3.4:** Returns OK if sufficient

### Test AC3:

```python
# Mock user with 10 credits, job costs 30
with pytest.raises(HTTPException) as exc:
    credit_required('script_generation', user_id='user-1')
assert exc.value.status_code == 402
```

---

## AC4: Credits Router

- [ ] **AC4.1:** `GET /api/credits/balance` returns balance
- [ ] **AC4.2:** `GET /api/credits/transactions` returns history
- [ ] **AC4.3:** Both require JWT
- [ ] **AC4.4:** Limited to 50 transactions

### Test AC4:

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/credits/balance
# Expect: {"credits": 100, "tier": "free"}
```

---

## AC5: Hold-Adjust-Commit

- [ ] **AC5.1:** HOLD deducts credits atomically
- [ ] **AC5.2:** ADJUST refunds difference
- [ ] **AC5.3:** COMMIT marks transaction as done
- [ ] **AC5.4:** REFUND returns credits on failure
- [ ] **AC5.5:** Race conditions handled (FOR UPDATE)

---

## AC6: Unit Tests

- [ ] **AC6.1:** Test pricing lookup
- [ ] **AC6.2:** Test balance retrieval
- [ ] **AC6.3:** Test hold success
- [ ] **AC6.4:** Test hold failure
- [ ] **AC6.5:** All tests pass

---

## Self-Check

1. [ ] All AC1-AC6 ✅
2. [ ] `pytest test_credit_manager.py -v` → PASSED
3. [ ] `ReadLints` → No errors

---

## Sign-off

```
✓ Task: Sprint 4 - Credit System
✓ Status: COMPLETED
✓ Files Created:
  - supabase/migrations/0018_credit_tiers.sql
  - apps/api/services/credit_manager.py
  - apps/api/dependencies/credit_required.py
  - apps/api/routers/credits.py
  - apps/api/test_credit_manager.py
✓ All Acceptance Criteria: PASSED
✓ Ready for next task group: Frontend Dashboard
```

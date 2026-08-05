# Sprint 4 Task Group 3: Credit System - Plan

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  CREDIT SYSTEM FLOW                                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User → API Request → Check Credits → HOLD → Process → COMMIT     │
│                              │                                    │
│                              ↓ (insufficient)                     │
│                          402 Payment Required                     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Hold-Adjust-Commit Pattern

### Step 1: HOLD (At job start)

```sql
-- New RPC: hold_credits
SELECT * FROM hold_credits(
  p_user_id := 'uuid',
  p_amount := 30,  -- estimated
  p_job_id := 'job-uuid'
);
-- Returns: {transaction_id, balance_after}
```

### Step 2: ADJUST (After actual cost known)

```sql
-- Update partial_commit_credits call
SELECT * FROM partial_commit_credits(
  p_user_id := 'uuid',
  p_job_id := 'job-uuid',
  p_final_amount := 25  -- actual (less than estimated)
);
-- Returns: {refund_amount, final_balance}
```

### Step 3: COMMIT (On success) or REFUND (On failure)

```sql
-- Success: nothing more (already committed)
-- Failure: revert hold
SELECT * FROM refund_credits(
  p_job_id := 'job-uuid'
);
```

## Files to Create

### 1. Credit Manager

**File:** `apps/api/services/credit_manager.py`

```python
class CreditManager:
    def hold(self, user_id, job_id, amount)
    def adjust(self, job_id, final_amount)
    def commit(self, job_id)
    def refund(self, job_id)
    def get_balance(self, user_id)
```

### 2. Dependency

**File:** `apps/api/dependencies/credit_required.py`

```python
def credit_required(job_type: str, user_id: str)
```

### 3. Router

**File:** `apps/api/routers/credits.py`

```python
GET /api/credits/balance
GET /api/credits/transactions
POST /api/credits/purchase (mock)
```

### 4. Migration

**File:** `supabase/migrations/0018_credit_tiers.sql`

- Add tier column defaults
- Add credit_packages table (optional)

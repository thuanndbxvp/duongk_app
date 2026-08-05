# Sprint 4 Task Group 3: Credit System (E1 Production)

## 1. Context & Mục đích

### Bối cảnh

User đã có (Task 1: RLS). Sprint 4.3 bật **Credit System** production:
- Hold-Adjust-Commit pattern (đã có RPC `partial_commit_credits` từ Sprint 1)
- Áp dụng cho: Validate Niche, Collect Channel, RAG, Script Generation
- Track usage qua `credit_transactions` table

### Mục đích

- **Real users** charge credits theo tier
- **Atomic transactions** (no race conditions)
- **Tier-based pricing** (free/pro/enterprise)

### Dependencies

- ✅ Task 1: User & RLS (user_id từ JWT)
- ✅ Task 2: BFF (gửi JWT)
- ✅ Sprint 1: `partial_commit_credits` RPC (đã tạo)

---

## 2. Database Schema (existing)

```sql
-- credit_transactions (Sprint 1)
CREATE TABLE credit_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  amount INT NOT NULL,  -- negative = charge, positive = refund
  job_id UUID REFERENCES jobs(id),
  job_type TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- partial_commit_credits RPC (Sprint 1)
-- Args: p_user_id, p_job_id, p_job_type, p_initial_hold, p_final_amount
-- Logic: HOLD initial → ADJUST to final → COMMIT
```

## 3. Pricing Tiers

| Operation | Free | Pro | Enterprise |
|-----------|------|-----|------------|
| Niche Validate | 5 | 5 | 5 |
| Collect Channel | 10 | 10 | 10 |
| Deep Analysis | 50 | 50 | 50 |
| Script Generation | 30 | 30 | 30 |
| Scene Breakdown | 10 | 10 | 10 |
| **Monthly credits** | 100 | 500 | Custom |

(Tier này sẽ tính lại dựa trên cost thực tế)

## 4. Files to Create

| File | Purpose |
|------|---------|
| `apps/api/services/credit_manager.py` | API service |
| `apps/api/dependencies/credit_required.py` | Dependency |
| `apps/api/routers/credits.py` | Credit endpoints |
| `apps/api/migrations/0018_credit_tiers.sql` | User tier column update |
| `apps/api/test_credit_manager.py` | Unit tests |

---

## 5. Acceptance Summary

| # | Criteria |
|---|----------|
| AC1 | Credit manager hold/adjust/commit works |
| AC2 | Tier-based pricing |
| AC3 | Insufficient credits → 402 |
| AC4 | Race conditions handled |
| AC5 | Refund on failure |
| AC6 | Tests pass |

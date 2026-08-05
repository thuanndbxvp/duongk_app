# Sprint 4 Task Group 3: Credit System - Skill Routing

## Commands ĐƯỢC PHÉP
- ✅ Read, Write, StrReplace
- ✅ ReadLints, self-fix

## Commands KHÔNG ĐƯỢC PHÉP
- ❌ Đổi existing partial_commit_credits RPC
- ❌ Launch subagents

## Patterns BẮT BUỘC

### 1. Hold-Adjust-Commit Pattern

```python
# HOLD: Trừ credits upfront
await credit_manager.hold(user_id, job_id, estimated_cost)

# ADJUST: Update với cost thực tế
await credit_manager.adjust(job_id, actual_cost)

# COMMIT: Hoặc refund nếu failure
await credit_manager.commit(job_id)  # hoặc refund(job_id)
```

### 2. Pricing Lookup

```python
PRICING = {
    'niche_validate': 5,
    'collect_channel': 10,
    'deep_analysis': 50,
    'script_generation': 30,
}
```

### 3. Dependency Pattern

```python
from fastapi import Depends

async def credit_required(
    job_type: str,
    user_id: str = Depends(get_supabase_user),
):
    """Charge credits before processing."""
    cost = PRICING.get(job_type, 0)
    if cost == 0:
        return
    
    await credit_manager.hold(user_id, job_id, cost)
    
    if user_credits < cost:
        raise HTTPException(402, 'Insufficient credits')
```

---

## Files CÓ THỂ TẠO
- ✅ `apps/api/services/credit_manager.py`
- ✅ `apps/api/dependencies/credit_required.py`
- ✅ `apps/api/routers/credits.py`
- ✅ `apps/api/test_credit_manager.py`
- ✅ `supabase/migrations/0018_credit_tiers.sql`

## Files KHÔNG ĐƯỢC SỬA
- ❌ `supabase/migrations/0011_partial_commit_credits.sql` (RPC đã có)
- ❌ `apps/api/dependencies/auth.py` (Task 1)

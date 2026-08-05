# Sprint 4 - Task Group Index

## Overview

Sprint 4: User, Auth, Credit & UI gồm **5 Task Groups**, mỗi group có **5 files** theo chuẩn TIER1_PROMPT.md.

---

## Task Groups

| # | Task Group | Files | Dependencies | Status |
|---|------------|-------|--------------|--------|
| 1 | User & RLS | 5 files | Sprint 1-3 ✅ | ⏳ Pending |
| 2 | Next.js BFF | 5 files | Task 1 | ⏳ Pending |
| 3 | Credit System | 5 files | Task 1, 2 | ⏳ Pending |
| 4 | Frontend Dashboard | 5 files | Task 1, 2, 3 | ⏳ Pending |
| 5 | Integration & E2E | 5 files | Tasks 1-4 | ⏳ Pending |

---

## Files per Task Group

### Task Group 1: User & Database Security (RLS)
```
docs/plan/CONTEXT-sprint4-user-rls.md
docs/plan/SKILL-ROUTING-sprint4-user-rls.md
docs/plan/PLAN-sprint4-user-rls.md
docs/plan/MSEW-sprint4-user-rls.md
docs/plan/ACCEPTANCE-sprint4-user-rls.md
```

### Task Group 2: Next.js BFF
```
docs/plan/CONTEXT-sprint4-nextjs-bff.md
docs/plan/SKILL-ROUTING-sprint4-nextjs-bff.md
docs/plan/PLAN-sprint4-nextjs-bff.md
docs/plan/MSEW-sprint4-nextjs-bff.md
docs/plan/ACCEPTANCE-sprint4-nextjs-bff.md
```

### Task Group 3: Credit System
```
docs/plan/CONTEXT-sprint4-credit-system.md
docs/plan/SKILL-ROUTING-sprint4-credit-system.md
docs/plan/PLAN-sprint4-credit-system.md
docs/plan/MSEW-sprint4-credit-system.md
docs/plan/ACCEPTANCE-sprint4-credit-system.md
```

### Task Group 4: Frontend Dashboard
```
docs/plan/CONTEXT-sprint4-frontend-dashboard.md
docs/plan/SKILL-ROUTING-sprint4-frontend-dashboard.md
docs/plan/PLAN-sprint4-frontend-dashboard.md
docs/plan/MSEW-sprint4-frontend-dashboard.md
docs/plan/ACCEPTANCE-sprint4-frontend-dashboard.md
```

### Task Group 5: Integration & E2E
```
docs/plan/CONTEXT-sprint4-integration.md
docs/plan/SKILL-ROUTING-sprint4-integration.md
docs/plan/PLAN-sprint4-integration.md
docs/plan/MSEW-sprint4-integration.md
docs/plan/ACCEPTANCE-sprint4-integration.md
```

---

## SQL Migrations Required

| Migration | Purpose | Task Group |
|-----------|---------|------------|
| `0017_enable_rls_policies.sql` | Enable RLS + policies | 1 |
| `0018_credit_tiers.sql` | Credit pricing + hold/refund RPCs | 3 |

---

## Output Files Summary

### Backend (Python)
- `apps/api/dependencies/auth.py` - JWT verify
- `apps/api/dependencies/credit_required.py` - Credit check
- `apps/api/routers/users.py` - User endpoints
- `apps/api/routers/credits.py` - Credit endpoints
- `apps/api/services/credit_manager.py` - Hold/Adjust/Commit

### Frontend (Next.js)
- `apps/web/lib/auth.ts` - Auth helpers
- `apps/web/lib/api-client.ts` - FastAPI client
- `apps/web/app/api/auth/login/route.ts`
- `apps/web/app/api/auth/logout/route.ts`
- `apps/web/app/api/scripts/generate/route.ts`
- `apps/web/app/api/jobs/[id]/route.ts`
- `apps/web/app/dashboard/page.tsx`
- `apps/web/app/projects/new/page.tsx`
- `apps/web/app/jobs/[id]/page.tsx`
- `apps/web/app/scripts/[id]/page.tsx`

### Components
- `apps/web/components/job-card.tsx`
- `apps/web/components/sub-progress-list.tsx`
- `apps/web/components/scene-timeline.tsx`

### Tests
- `tests/conftest.py`
- `tests/integration/test_rls.py`
- `tests/e2e/test_user_flow.py`
- `tests/e2e/test_frontend_flow.spec.ts`

---

## Estimated Timeline

| Task Group | Effort | Recommended |
|------------|--------|-------------|
| 1: User & RLS | 8h | Tier 2 |
| 2: Next.js BFF | 10h | Tier 2 |
| 3: Credit System | 8h | Tier 2 |
| 4: Frontend Dashboard | 12h | Tier 2 |
| 5: Integration | 4h | Tier 2 |
| **Total** | **~42h** | |

---

## Security Checklist

🔴 Critical:
- [x] NO `verify_signature:False` (D11 FIX)
- [x] RLS enabled on all tables
- [x] JWT audience check
- [x] Service role bypass for worker

🟡 High:
- [x] HttpOnly cookies (NOT localStorage)
- [x] SameSite=Lax for CSRF
- [x] Atomic credit operations (FOR UPDATE)

---

## Next Steps

1. Tier 2 đọc từng Task Group theo thứ tự
2. Implement theo MSEW checklist
3. Self-verify với ACCEPTANCE criteria
4. Báo cáo khi hoàn thành từng Task Group

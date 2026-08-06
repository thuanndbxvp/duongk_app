# MSEW: phase6-admin-user-credit

## Prerequisites (Điều kiện tiên quyết)
- **Đọc CONTEXT:** `docs/plan/CONTEXT-phase6-admin-user-credit.md`
- **Đọc PLAN:** `docs/plan/PLAN-phase6-admin-user-credit.md`
- **Phase 5 đã xong:** `require_admin` (apps/api/dependencies/admin.py:15), `audit.py:log_admin_action`, migration 0022, AdminShell layout, Dashboard `/admin` stub.
- **Branch:** main
- **Working dir:** `d:\appDK`
- **Line Ending:** CRLF
- **Quy tắc:** Mọi endpoint admin PHẢI có `Depends(require_admin)` + mutation PHẢI gọi `log_admin_action()`.

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | Tạo `admin_users.py` | `backend-development` | `better-auth` | `database-admin` |
| 2 | Tạo `admin_credit.py` | `backend-development` | `database-admin` | `debugging` |
| 3 | Tạo `admin_pricing.py` | `backend-development` | `database-admin` | `debugging` |
| 4 | UPDATE `main.py` mount 3 routers | `backend-development` | `debugging` | `code-review` |
| 5 | Tạo `api/admin/users/route.ts` | `frontend-development` | `better-auth` | `debugging` |
| 6 | Tạo 3 web proxy routes | `frontend-development` | `better-auth` | `debugging` |
| 7 | Tạo `admin/users/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` |
| 8 | Tạo `admin/users/[id]/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` |
| 9 | Tạo `admin/credits/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` |
| 10 | UPDATE `layout.tsx` enable Users + Credits | `frontend-development` | `ui-styling` | `debugging` |
| 11 | Self-verify toàn bộ | `debugging` | `code-review` | `backend-development` |

## Files KHÔNG được đụng (Do Not Touch)
- `apps/api/dependencies/admin.py` (Phase 5 đã có require_admin).
- `apps/api/services/audit.py` (Phase 5 đã có log_admin_action).
- `supabase/migrations/0022_admin_panel_foundation.sql`.
- `apps/api/services/credit_manager.py`.
- User-facing routes: `routers/{projects,users,credits}.py`, `modules/*`.
- Tất cả worker tasks.

---

## Micro-Steps

### Step 1: Tạo `apps/api/routers/admin_users.py`
**File:** `apps/api/routers/admin_users.py` (NEW)
**Vai trò:** 9 endpoints user management (CRUD + restore + ban + impersonate + adjust-credit).
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `database-admin`.

**Pre-check (CodeGraph):**
- `require_admin` at `apps/api/dependencies/admin.py:15`.
- `log_admin_action` at `apps/api/services/audit.py:27`.
- `get_supabase_admin` at `apps/api/dependencies/supabase.py`.

**Import cần thêm:** (đã có sẵn module)

**Code cần viết:**
```python
"""
Admin User Management — 9 endpoints.
Mounted dưới /api/admin/users.
Tất cả PHẢI có Depends(require_admin) và mutation PHẢI gọi log_admin_action().
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from apps.api.dependencies.admin import require_admin
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.audit import log_admin_action


router = APIRouter(prefix="/api/admin/users", tags=["Admin Users"])


# --- Schemas ---

class UserUpdate(BaseModel):
    tier: Optional[str] = None
    full_name: Optional[str] = None
    max_assistants: Optional[int] = None
    role: Optional[str] = Field(None, pattern='^(user|admin|super_admin)$')


class BanRequest(BaseModel):
    reason: str = Field(..., min_length=10)
    until: Optional[str] = None  # ISO timestamp


class AdjustCreditRequest(BaseModel):
    delta: int = Field(..., ge=-10000, le=10000)
    reason: str = Field(..., min_length=10)


class ImpersonateRequest(BaseModel):
    ttl_minutes: int = Field(default=15, ge=1, le=60)


# --- Endpoints ---

@router.get("")
async def list_users(
    admin_id: str = Depends(require_admin),
    q: Optional[str] = None,
    tier: Optional[str] = None,
    status: Optional[str] = None,  # 'active' | 'banned' | 'deleted'
    role: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    """List users với filter + pagination."""
    db = get_supabase_admin()
    query = db.table('users').select('*', count='exact')
    
    if q:
        query = query.or_(f'email.ilike.%{q}%,full_name.ilike.%{q}%')
    if tier:
        query = query.eq('tier', tier)
    if role:
        query = query.eq('role', role)
    if status == 'banned':
        query = query.not_.is_('banned_at', 'null')
    elif status == 'deleted':
        query = query.not_.is_('deleted_at', 'null')
    elif status == 'active':
        query = query.is_('banned_at', 'null').is_('deleted_at', 'null')
    
    if from_date:
        query = query.gte('created_at', from_date)
    if to_date:
        query = query.lte('created_at', to_date)
    
    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1).order('created_at', desc=True)
    
    result = query.execute()
    return {
        'users': result.data or [],
        'total': result.count or 0,
        'page': page,
        'limit': limit,
    }


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    admin_id: str = Depends(require_admin),
):
    """User detail + counts inline."""
    db = get_supabase_admin()
    
    user = db.table('users').select('*').eq('id', user_id).single().execute()
    if not user.data:
        raise HTTPException(404, 'User not found')
    
    # Counts inline
    jobs_count = db.table('jobs').select('id', count='exact').eq('user_id', user_id).execute()
    assistants_count = db.table('channel_assistants').select('id', count='exact').eq('user_id', user_id).execute()
    scripts_count = db.table('generated_scripts').select('id', count='exact').eq('assistant_id', user_id).execute()
    
    user.data['counts'] = {
        'jobs': jobs_count.count or 0,
        'assistants': assistants_count.count or 0,
        'scripts': scripts_count.count or 0,
    }
    return user.data


@router.post("")
async def create_user(
    payload: dict,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Tạo user thủ công (invite). Body: {email, full_name, tier, credits, max_assistants}."""
    email = payload.get('email')
    if not email:
        raise HTTPException(400, 'email required')
    
    db = get_supabase_admin()
    
    # 1) Create in auth.users via admin API
    auth_result = db.auth.admin.create_user({
        'email': email,
        'email_confirm': True,
        'user_metadata': {'full_name': payload.get('full_name', '')},
    })
    if not auth_result.user:
        raise HTTPException(500, 'Failed to create auth user')
    
    new_user_id = auth_result.user.id
    
    # 2) Insert into public.users
    db.table('users').insert({
        'id': new_user_id,
        'email': email,
        'full_name': payload.get('full_name'),
        'tier': payload.get('tier', 'free'),
        'credits': payload.get('credits', 0),
        'max_assistants': payload.get('max_assistants', 5),
    }).execute()
    
    # 3) Audit log
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='user.create',
        target_type='user',
        target_id=new_user_id,
        after={'email': email, 'tier': payload.get('tier', 'free')},
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent'),
    )
    
    return {'id': new_user_id, 'email': email}


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    update: UserUpdate,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Update user (tier/full_name/max_assistants/role). Audit log before/after."""
    db = get_supabase_admin()
    
    before = db.table('users').select('*').eq('id', user_id).single().execute().data
    if not before:
        raise HTTPException(404, 'User not found')
    
    update_data = update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(400, 'No fields to update')
    
    update_data['updated_at'] = 'now()'
    db.table('users').update(update_data).eq('id', user_id).execute()
    
    after = db.table('users').select('*').eq('id', user_id).single().execute().data
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='user.update',
        target_type='user',
        target_id=user_id,
        before=before,
        after=after,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent'),
    )
    
    return after


@router.delete("/{user_id}")
async def soft_delete_user(
    user_id: str,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Soft delete — set deleted_at. Recovery window 7 ngày (cron Phase 7+)."""
    db = get_supabase_admin()
    
    before = db.table('users').select('*').eq('id', user_id).single().execute().data
    if not before:
        raise HTTPException(404, 'User not found')
    
    db.rpc('soft_delete_user', {'p_user_id': user_id}).execute()
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='user.soft_delete',
        target_type='user',
        target_id=user_id,
        before={'deleted_at': before.get('deleted_at')},
        after={'deleted_at': 'now()'},
        ip=request.client.host if request.client else None,
    )
    return None  # 204


@router.post("/{user_id}/restore")
async def restore_user(
    user_id: str,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Restore user từ soft-delete (trong 7 ngày)."""
    db = get_supabase_admin()
    
    before = db.table('users').select('*').eq('id', user_id).single().execute().data
    if not before:
        raise HTTPException(404, 'User not found')
    
    db.table('users').update({'deleted_at': None, 'updated_at': 'now()'}).eq('id', user_id).execute()
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='user.restore',
        target_type='user',
        target_id=user_id,
        before={'deleted_at': before.get('deleted_at')},
        after={'deleted_at': None},
        ip=request.client.host if request.client else None,
    )
    return {'id': user_id, 'deleted_at': None}


@router.post("/{user_id}/ban")
async def ban_user(
    user_id: str,
    payload: BanRequest,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Ban user — set banned_at + banned_reason."""
    db = get_supabase_admin()
    
    db.table('users').update({
        'banned_at': 'now()',
        'banned_reason': payload.reason,
        'updated_at': 'now()',
    }).eq('id', user_id).execute()
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='user.ban',
        target_type='user',
        target_id=user_id,
        after={'banned_at': 'now()', 'banned_reason': payload.reason},
        reason=payload.reason,
        ip=request.client.host if request.client else None,
    )
    return {'id': user_id, 'banned_at': 'now()'}


@router.post("/{user_id}/unban")
async def unban_user(
    user_id: str,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Unban user — clear banned_at."""
    db = get_supabase_admin()
    
    db.table('users').update({
        'banned_at': None,
        'banned_reason': None,
        'updated_at': 'now()',
    }).eq('id', user_id).execute()
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='user.unban',
        target_type='user',
        target_id=user_id,
        ip=request.client.host if request.client else None,
    )
    return {'id': user_id, 'banned_at': None}


@router.post("/{user_id}/impersonate")
async def impersonate_user(
    user_id: str,
    payload: ImpersonateRequest,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """
    Phát short-lived token. PHASE 6 STUB: return mock token.
    Phase 7+ sẽ full impl với Supabase Auth admin API.
    """
    db = get_supabase_admin()
    
    target = db.table('users').select('email').eq('id', user_id).single().execute()
    if not target.data:
        raise HTTPException(404, 'User not found')
    
    # Audit log MUST ghi rõ impersonate
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='user.impersonate',
        target_type='user',
        target_id=user_id,
        after={'impersonated_email': target.data.get('email'), 'ttl_minutes': payload.ttl_minutes},
        reason=f'Impersonate {target.data.get("email")} for {payload.ttl_minutes}min',
        ip=request.client.host if request.client else None,
    )
    
    # STUB: Phase 7+ sẽ trả real JWT signed bởi Supabase
    from datetime import datetime, timezone, timedelta
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=payload.ttl_minutes)).isoformat()
    return {
        'token': f'mock-impersonate-{user_id[:8]}-{payload.ttl_minutes}m',
        'expires_at': expires_at,
        'impersonated_by': admin_id,
        'impersonated_email': target.data.get('email'),
    }


@router.post("/{user_id}/adjust-credit")
async def adjust_credit(
    user_id: str,
    payload: AdjustCreditRequest,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Adjust credits via RPC admin_adjust_credits."""
    db = get_supabase_admin()
    
    before_balance = db.table('users').select('credits').eq('id', user_id).single().execute().data.get('credits', 0)
    
    # Call RPC
    result = db.rpc('admin_adjust_credits', {
        'p_admin_id': admin_id,
        'p_user_id': user_id,
        'p_delta': payload.delta,
        'p_reason': payload.reason,
    }).execute()
    
    if not result.data:
        raise HTTPException(500, 'RPC failed')
    
    new_balance, tx_id = result.data[0]['new_balance'], result.data[0]['tx_id']
    
    # Audit log
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='credit.adjust',
        target_type='user',
        target_id=user_id,
        before={'credits': before_balance},
        after={'credits': new_balance, 'delta': payload.delta, 'tx_id': tx_id},
        reason=payload.reason,
        ip=request.client.host if request.client else None,
    )
    
    return {'new_balance': new_balance, 'tx_id': tx_id}
```

**KHÔNG được sửa:**
- Imports khác ngoài audit, admin, supabase.
- Schema definitions (giữ nguyên Pydantic).

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.routers.admin_users import router; print('OK')"
```

**Expected output:** `OK`.

---

### Step 2: Tạo `apps/api/routers/admin_credit.py`
**File:** `apps/api/routers/admin_credit.py` (NEW)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `database-admin`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
"""
Admin Credit Management — 4 endpoints.
Mounted dưới /api/admin/credit.
"""
import csv
import io
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Optional
from apps.api.dependencies.admin import require_admin


router = APIRouter(prefix="/api/admin/credit", tags=["Admin Credit"])


@router.get("/ledger")
async def get_ledger(
    admin_id: str = Depends(require_admin),
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    limit: int = 100,
):
    """
    Credit ledger toàn hệ thống. Filter + paginate.
    """
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    
    query = db.table('credit_transactions').select('*, users!inner(email), jobs(task_type)', count='exact')
    
    if user_id:
        query = query.eq('user_id', user_id)
    if action:
        query = query.eq('action', action)
    if from_date:
        query = query.gte('created_at', from_date)
    if to_date:
        query = query.lte('created_at', to_date)
    
    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1).order('created_at', desc=True)
    
    result = query.execute()
    return {
        'transactions': result.data or [],
        'total': result.count or 0,
        'page': page,
        'limit': limit,
    }


@router.get("/stats")
async def get_stats(
    admin_id: str = Depends(require_admin),
):
    """
    4 stat metrics + sparkline 7 ngày.
    """
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    
    # Total issued (amount > 0)
    issued = db.rpc('exec_sql', {
        'sql': "SELECT COALESCE(SUM(amount), 0) FROM credit_transactions WHERE amount > 0"
    }).execute() if False else {'data': [{'sum': 0}]}  # fallback nếu exec_sql RPC không có
    
    # Stats đơn giản (dùng table query thay vì RPC)
    all_tx = db.table('credit_transactions').select('amount, action, created_at').gte('created_at', 'now()-interval \'90 days\'').execute()
    total_issued = sum(t['amount'] for t in (all_tx.data or []) if t['amount'] > 0 and t['action'] != 'refund')
    total_spent = sum(-t['amount'] for t in (all_tx.data or []) if t['amount'] < 0 and t['action'] != 'refund')
    total_refunded = sum(t['amount'] for t in (all_tx.data or []) if t['action'] == 'refund')
    
    # Total hold (running jobs)
    hold_jobs = db.table('jobs').select('credits_held').eq('status', 'running').execute()
    total_hold = sum(j['credits_held'] or 0 for j in (hold_jobs.data or []))
    
    # Sparkline 7 ngày: group by day
    sparkline = []
    for i in range(7):
        day = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_tx = db.table('credit_transactions').select('amount').gte('created_at', f'{day}T00:00:00').lte('created_at', f'{day}T23:59:59').execute()
        day_spent = sum(-t['amount'] for t in (day_tx.data or []) if t['amount'] < 0)
        sparkline.append({'date': day, 'spent': day_spent})
    
    return {
        'total_issued': total_issued,
        'total_spent': total_spent,
        'total_hold': total_hold,
        'total_refunded': total_refunded,
        'sparkline': list(reversed(sparkline)),
    }


@router.get("/export")
async def export_csv(
    admin_id: str = Depends(require_admin),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    """
    Export CSV — max 1 năm range.
    """
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    
    query = db.table('credit_transactions').select('id, user_id, action, amount, balance_after, reason, created_at, users!inner(email)')
    if from_date:
        query = query.gte('created_at', from_date)
    if to_date:
        query = query.lte('created_at', to_date)
    query = query.order('created_at', desc=True).limit(50000)  # safety cap
    
    result = query.execute()
    
    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['tx_id', 'user_email', 'action', 'amount', 'balance_after', 'reason', 'created_at'])
    for tx in (result.data or []):
        writer.writerow([
            tx['id'],
            tx.get('users', {}).get('email', ''),
            tx['action'],
            tx['amount'],
            tx['balance_after'],
            tx.get('reason', ''),
            tx['created_at'],
        ])
    
    return Response(
        content=output.getvalue(),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="credit-ledger.csv"'},
    )


@router.get("/pricing")
async def list_pricing(
    admin_id: str = Depends(require_admin),
):
    """List credit_pricing rows (admin view — không filter enabled)."""
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    result = db.table('credit_pricing').select('*').order('credits').execute()
    return result.data or []
```

**Verify command:**
```powershell
python -c "from apps.api.routers.admin_credit import router; print('OK')"
```

**Expected output:** `OK`.

---

### Step 3: Tạo `apps/api/routers/admin_pricing.py`
**File:** `apps/api/routers/admin_pricing.py` (NEW)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `database-admin`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
"""
Admin Pricing Config — 2 endpoints.
Mounted dưới /api/admin/pricing.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from apps.api.dependencies.admin import require_admin
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.audit import log_admin_action


router = APIRouter(prefix="/api/admin/pricing", tags=["Admin Pricing"])


class PricingUpdate(BaseModel):
    credits: Optional[int] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None


@router.patch("/{job_type}")
async def update_pricing(
    job_type: str,
    update: PricingUpdate,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Update credit_pricing row + audit log."""
    db = get_supabase_admin()
    
    before = db.table('credit_pricing').select('*').eq('job_type', job_type).single().execute().data
    if not before:
        raise HTTPException(404, 'Job type not found')
    
    update_data = update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(400, 'No fields to update')
    update_data['updated_by'] = admin_id
    update_data['updated_at'] = 'now()'
    
    db.table('credit_pricing').update(update_data).eq('job_type', job_type).execute()
    after = db.table('credit_pricing').select('*').eq('job_type', job_type).single().execute().data
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='pricing.update',
        target_type='pricing',
        target_id=job_type,
        before=before,
        after=after,
        ip=request.client.host if request.client else None,
    )
    
    return after


@router.post("/reload")
async def reload_pricing(
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """
    Publish Redis channel để worker reload cache.
    Phase 6 STUB: chỉ ghi log. Phase 7+ sẽ impl Redis pub/sub thật.
    """
    admin_email = get_supabase_admin().table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='pricing.reload',
        target_type='pricing',
        reason='Manual reload pricing cache',
        ip=request.client.host if request.client else None,
    )
    return {'status': 'reload_queued', 'note': 'Phase 6 stub — Redis pub/sub Phase 7+'}
```

**Verify command:**
```powershell
python -c "from apps.api.routers.admin_pricing import router; print('OK')"
```

**Expected output:** `OK`.

---

### Step 4: UPDATE `apps/api/main.py` mount 3 routers admin
**File:** `apps/api/main.py` (UPDATE — append)
**Vị trí:** Sau line 25 (sau voice_router import) + sau line 42 (sau include voice_router).
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `debugging`.
  - **Fallback:** `code-review`.

**Code cần viết:**

**SAU** `from apps.api.routers.channels import router as channels_router` (Step 1 Phase 1), **THÊM**:
```python
from apps.api.routers.admin_users import router as admin_users_router
from apps.api.routers.admin_credit import router as admin_credit_router
from apps.api.routers.admin_pricing import router as admin_pricing_router
```

**SAU** `app.include_router(channels_router)` (Phase 1), **THÊM**:
```python
app.include_router(admin_users_router)
app.include_router(admin_credit_router)
app.include_router(admin_pricing_router)
```

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path]; print('\n'.join(sorted(routes)))"
```

**Expected output:** Danh sách ≥ 15 admin routes:
- `/api/admin/users`, `/api/admin/users/{user_id}` (+ 7 subroutes)
- `/api/admin/credit/ledger`, `/credit/stats`, `/credit/export`, `/credit/pricing`
- `/api/admin/pricing/{job_type}`, `/api/admin/pricing/reload`

---

### Step 5: Tạo `apps/web/app/api/admin/users/route.ts`
**File:** `apps/web/app/api/admin/users/route.ts` (NEW)
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const params = req.nextUrl.searchParams.toString();
  try {
    const response = await apiFetch(`/api/admin/users${params ? `?${params}` : ''}`, {}, token);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const body = await req.json();
  try {
    const response = await apiFetch('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify(body),
    }, token);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**Verify command:**
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit app/api/admin/users/route.ts 2>&1 | Select-String "error TS"
```

**Expected output:** No output (no errors).

---

### Step 6: Tạo 3 web proxy routes còn lại
**Files (3 NEW):**
- `apps/web/app/api/admin/users/[id]/route.ts`
- `apps/web/app/api/admin/users/[id]/adjust-credit/route.ts`
- `apps/web/app/api/admin/credits/ledger/route.ts`

**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `debugging`.

**Code cho 3 file:**

**`apps/web/app/api/admin/users/[id]/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const { id } = await params;
  try {
    const response = await apiFetch(`/api/admin/users/${id}`, {}, token);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const { id } = await params;
  const body = await req.json();
  try {
    const response = await apiFetch(`/api/admin/users/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }, token);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/admin/users/[id]/adjust-credit/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const { id } = await params;
  const body = await req.json();
  try {
    const response = await apiFetch(`/api/admin/users/${id}/adjust-credit`, {
      method: 'POST',
      body: JSON.stringify(body),
    }, token);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/admin/credits/ledger/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const params = req.nextUrl.searchParams.toString();
  try {
    const response = await apiFetch(`/api/admin/credit/ledger${params ? `?${params}` : ''}`, {}, token);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**Verify command:**
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"
```

**Expected output:** No errors.

---

### Step 7: Tạo `apps/web/app/(admin)/admin/users/page.tsx`
**File:** `apps/web/app/(admin)/admin/users/page.tsx` (NEW)
**Vai trò:** Admin user list với filter, search, pagination.
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `aesthetic`.

**Code cần viết:**
```tsx
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface User {
  id: string;
  email: string;
  full_name: string | null;
  credits: number;
  tier: string;
  role: string;
  banned_at: string | null;
  deleted_at: string | null;
  created_at: string;
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({
      page: String(page),
      limit: '50',
    });
    if (search) params.set('q', search);
    if (tierFilter) params.set('tier', tierFilter);
    if (statusFilter) params.set('status', statusFilter);

    fetch(`/api/admin/users?${params}`)
      .then((r) => r.json())
      .then((data) => {
        setUsers(data.users || []);
        setTotal(data.total || 0);
      })
      .finally(() => setLoading(false));
  }, [page, search, tierFilter, statusFilter]);

  const totalPages = Math.ceil(total / 50);

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Users</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">{total} users total</p>
      </div>

      {/* Filters */}
      <div className="glass rounded-2xl p-4 flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Search email..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="flex-1 min-w-[200px] px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)]"
        />
        <select
          value={tierFilter}
          onChange={(e) => { setTierFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white"
        >
          <option value="">All tiers</option>
          <option value="free">Free</option>
          <option value="pro">Pro</option>
          <option value="enterprise">Enterprise</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white"
        >
          <option value="">All status</option>
          <option value="active">Active</option>
          <option value="banned">Banned</option>
          <option value="deleted">Deleted</option>
        </select>
      </div>

      {/* Table */}
      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--surface)] border-b border-[var(--glass-border)]">
            <tr>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Email</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Name</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Tier</th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Credits</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Role</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Status</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Joined</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="px-4 py-12 text-center text-[var(--fg-tertiary)]">Loading…</td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-12 text-center text-[var(--fg-tertiary)]">No users</td></tr>
            ) : users.map((u) => (
              <tr key={u.id} className="border-b border-[var(--glass-border)] hover:bg-[var(--surface-hover)]">
                <td className="px-4 py-3">
                  <Link href={`/admin/users/${u.id}`} className="text-[var(--brand-300)] hover:text-[var(--brand-400)]">
                    {u.email}
                  </Link>
                </td>
                <td className="px-4 py-3 text-[var(--fg-secondary)]">{u.full_name || '—'}</td>
                <td className="px-4 py-3 capitalize text-[var(--fg-secondary)]">{u.tier}</td>
                <td className="px-4 py-3 text-right tabular-nums">{u.credits}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-[var(--brand-500)]/20 text-[var(--brand-300)]">
                    {u.role}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {u.deleted_at ? (
                    <span className="text-red-400 text-xs">deleted</span>
                  ) : u.banned_at ? (
                    <span className="text-orange-400 text-xs">banned</span>
                  ) : (
                    <span className="text-green-400 text-xs">active</span>
                  )}
                </td>
                <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)]">
                  {new Date(u.created_at).toLocaleDateString('vi-VN')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <button
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
            className="px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white disabled:opacity-30"
          >
            ← Previous
          </button>
          <span className="text-sm text-[var(--fg-tertiary)]">
            Page {page} / {totalPages}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage(page + 1)}
            className="px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white disabled:opacity-30"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
```

**Verify command:**
```powershell
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"
```

**Expected output:** No errors.

---

### Step 8: Tạo `apps/web/app/(admin)/admin/users/[id]/page.tsx`
**File:** `apps/web/app/(admin)/admin/users/[id]/page.tsx` (NEW)
**Vai trò:** User detail với profile + tabs.
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `aesthetic`.

**Code cần viết:**
```tsx
'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';

interface UserDetail {
  id: string;
  email: string;
  full_name: string | null;
  credits: number;
  tier: string;
  role: string;
  banned_at: string | null;
  banned_reason: string | null;
  deleted_at: string | null;
  max_assistants: number;
  created_at: string;
  last_sign_in_at: string | null;
  counts?: { jobs: number; assistants: number; scripts: number };
}

export default function UserDetailPage() {
  const params = useParams();
  const router = useRouter();
  const userId = params.id as string;
  
  const [user, setUser] = useState<UserDetail | null>(null);
  const [delta, setDelta] = useState(0);
  const [reason, setReason] = useState('');
  const [adjusting, setAdjusting] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch(`/api/admin/users/${userId}`)
      .then((r) => r.json())
      .then(setUser);
  }, [userId]);

  async function handleAdjust() {
    if (reason.length < 10) {
      setMessage('Lý do phải ≥ 10 ký tự');
      return;
    }
    setAdjusting(true);
    const res = await fetch(`/api/admin/users/${userId}/adjust-credit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ delta, reason }),
    });
    const data = await res.json();
    if (res.ok) {
      setMessage(`OK — New balance: ${data.new_balance}`);
      // Refresh
      const updated = await fetch(`/api/admin/users/${userId}`).then(r => r.json());
      setUser(updated);
    } else {
      setMessage(`Error: ${data.detail}`);
    }
    setAdjusting(false);
  }

  async function handleBan() {
    const banReason = prompt('Lý do ban (≥ 10 ký tự):');
    if (!banReason || banReason.length < 10) return;
    const res = await fetch(`/api/admin/users/${userId}/ban`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: banReason }),
    });
    if (res.ok) {
      const updated = await fetch(`/api/admin/users/${userId}`).then(r => r.json());
      setUser(updated);
      setMessage('User banned');
    }
  }

  if (!user) return <div className="p-8 text-center text-[var(--fg-tertiary)]">Loading…</div>;

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <button onClick={() => router.back()} className="text-[var(--brand-300)] hover:text-[var(--brand-400)]">
        ← Back to Users
      </button>

      <div className="space-y-2">
        <h1 className="text-3xl font-bold">{user.email}</h1>
        <p className="text-sm text-[var(--fg-tertiary)]">
          {user.role} · {user.tier} · Joined {new Date(user.created_at).toLocaleDateString('vi-VN')}
        </p>
      </div>

      {message && (
        <div className="glass rounded-xl p-3 text-sm">{message}</div>
      )}

      <div className="grid md:grid-cols-3 gap-4">
        {/* Profile */}
        <div className="glass rounded-2xl p-5 space-y-3">
          <h2 className="text-lg font-semibold">Profile</h2>
          <div className="space-y-2 text-sm">
            <div><span className="text-[var(--fg-tertiary)]">Email:</span> {user.email}</div>
            <div><span className="text-[var(--fg-tertiary)]">Name:</span> {user.full_name || '—'}</div>
            <div><span className="text-[var(--fg-tertiary)]">Tier:</span> <span className="capitalize">{user.tier}</span></div>
            <div><span className="text-[var(--fg-tertiary)]">Role:</span> {user.role}</div>
            <div><span className="text-[var(--fg-tertiary)]">Max assistants:</span> {user.max_assistants}</div>
            <div><span className="text-[var(--fg-tertiary)]">Last sign in:</span> {user.last_sign_in_at ? new Date(user.last_sign_in_at).toLocaleString('vi-VN') : '—'}</div>
          </div>
        </div>

        {/* Stats */}
        <div className="glass rounded-2xl p-5 space-y-3">
          <h2 className="text-lg font-semibold">Stats</h2>
          <div className="space-y-2 text-sm">
            <div><span className="text-[var(--fg-tertiary)]">Credits:</span> <span className="text-2xl font-bold tabular-nums">{user.credits}</span></div>
            <div><span className="text-[var(--fg-tertiary)]">Jobs:</span> {user.counts?.jobs ?? 0}</div>
            <div><span className="text-[var(--fg-tertiary)]">Assistants:</span> {user.counts?.assistants ?? 0}</div>
            <div><span className="text-[var(--fg-tertiary)]">Scripts:</span> {user.counts?.scripts ?? 0}</div>
          </div>
        </div>

        {/* Actions */}
        <div className="glass rounded-2xl p-5 space-y-3">
          <h2 className="text-lg font-semibold">Actions</h2>
          
          {/* Adjust Credit */}
          <div className="space-y-2">
            <input
              type="number"
              value={delta}
              onChange={(e) => setDelta(Number(e.target.value))}
              placeholder="Delta (-10000 to 10000)"
              className="w-full px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white"
            />
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Lý do (≥ 10 ký tự)"
              className="w-full px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)]"
            />
            <button
              onClick={handleAdjust}
              disabled={adjusting}
              className="w-full px-4 py-2 rounded-lg bg-[var(--brand-500)] text-white font-semibold disabled:opacity-50"
            >
              {adjusting ? 'Adjusting…' : 'Adjust Credit'}
            </button>
          </div>

          {/* Ban/Unban */}
          {user.banned_at ? (
            <button
              onClick={async () => {
                await fetch(`/api/admin/users/${userId}/unban`, { method: 'POST' });
                const updated = await fetch(`/api/admin/users/${userId}`).then(r => r.json());
                setUser(updated);
              }}
              className="w-full px-4 py-2 rounded-lg bg-green-500/20 text-green-400 font-semibold"
            >
              Unban User
            </button>
          ) : (
            <button
              onClick={handleBan}
              className="w-full px-4 py-2 rounded-lg bg-orange-500/20 text-orange-400 font-semibold"
            >
              Ban User
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
```

**Verify command:**
```powershell
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"
```

**Expected output:** No errors.

---

### Step 9: Tạo `apps/web/app/(admin)/admin/credits/page.tsx`
**File:** `apps/web/app/(admin)/admin/credits/page.tsx` (NEW)
**Vai trò:** Ledger + stats + Export CSV.
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `aesthetic`.

**Code cần viết:**
```tsx
'use client';

import { useEffect, useState } from 'react';

interface Transaction {
  id: string;
  user_id: string;
  action: string;
  amount: number;
  balance_after: number;
  reason: string;
  created_at: string;
  users?: { email: string };
}

interface Stats {
  total_issued: number;
  total_spent: number;
  total_hold: number;
  total_refunded: number;
  sparkline: Array<{ date: string; spent: number }>;
}

export default function AdminCreditsPage() {
  const [txs, setTxs] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState<Stats | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetch(`/api/admin/credit/ledger?page=${page}&limit=100`)
      .then((r) => r.json())
      .then((data) => {
        setTxs(data.transactions || []);
        setTotal(data.total || 0);
      });
    fetch('/api/admin/credit/stats')
      .then((r) => r.json())
      .then(setStats);
  }, [page]);

  function handleExport() {
    const from = prompt('From date (YYYY-MM-DD):', new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString().slice(0, 10));
    if (!from) return;
    const to = prompt('To date (YYYY-MM-DD):', new Date().toISOString().slice(0, 10));
    if (!to) return;
    window.location.href = `/api/admin/credit/export?from_date=${from}&to_date=${to}`;
  }

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Credit Ledger</span>
        </h1>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {[
            { label: 'Total Issued', value: stats.total_issued, color: 'text-green-400' },
            { label: 'Total Spent', value: stats.total_spent, color: 'text-red-400' },
            { label: 'Total Hold', value: stats.total_hold, color: 'text-yellow-400' },
            { label: 'Total Refunded', value: stats.total_refunded, color: 'text-blue-400' },
          ].map((s) => (
            <div key={s.label} className="glass-strong rounded-2xl p-5">
              <p className="text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">{s.label}</p>
              <p className={`text-3xl font-bold tabular-nums ${s.color}`}>{s.value.toLocaleString()}</p>
            </div>
          ))}
        </div>
      )}

      {/* Export button */}
      <div className="flex justify-end">
        <button
          onClick={handleExport}
          className="px-4 py-2 rounded-lg bg-[var(--brand-500)] text-white font-semibold"
        >
          Export CSV
        </button>
      </div>

      {/* Table */}
      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--surface)] border-b border-[var(--glass-border)]">
            <tr>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">User</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Action</th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Amount</th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Balance After</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Reason</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Date</th>
            </tr>
          </thead>
          <tbody>
            {txs.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-12 text-center text-[var(--fg-tertiary)]">No transactions</td></tr>
            ) : txs.map((tx) => (
              <tr key={tx.id} className="border-b border-[var(--glass-border)]">
                <td className="px-4 py-3 text-[var(--fg-secondary)]">{tx.users?.email || tx.user_id.slice(0, 8)}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-[var(--brand-500)]/20 text-[var(--brand-300)]">
                    {tx.action}
                  </span>
                </td>
                <td className={`px-4 py-3 text-right tabular-nums ${tx.amount > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {tx.amount > 0 ? '+' : ''}{tx.amount}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">{tx.balance_after}</td>
                <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)] max-w-xs truncate">{tx.reason || '—'}</td>
                <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)]">
                  {new Date(tx.created_at).toLocaleString('vi-VN')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-[var(--fg-tertiary)] text-center">
        Showing {txs.length} of {total} transactions
      </p>
    </div>
  );
}
```

**Verify command:**
```powershell
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"
```

**Expected output:** No errors.

---

### Step 10: UPDATE `apps/web/app/(admin)/layout.tsx` enable Users + Credits
**File:** `apps/web/app/(admin)/layout.tsx` (UPDATE — 2 dòng)
**Vị trí:** Line 9 (`Users.enabled = false` → `true`) và line 10 (`Credits.enabled = false` → `true`).
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `debugging`.

**Code cần viết (2 lần `StrReplace`):**

**Thay 1 — line 9:**
```typescript
  { href: '/admin/users', label: 'Users', icon: IconUsers, enabled: false },
```
**Đổi thành:**
```typescript
  { href: '/admin/users', label: 'Users', icon: IconUsers, enabled: true },
```

**Thay 2 — line 10:**
```typescript
  { href: '/admin/credits', label: 'Credits', icon: IconChannels, enabled: false },
```
**Đổi thành:**
```typescript
  { href: '/admin/credits', label: 'Credits', icon: IconChannels, enabled: true },
```

**KHÔNG được sửa:**
- 6 mục còn lại (Pricing, API Keys, Routing, Alerts, Audit Logs).
- Layout structure khác.

**Verify command:**
```powershell
Get-Content "apps\web\app\(admin)\layout.tsx" | Select-String "enabled:" | Measure-Object -Line
```

**Expected output:** 8 lines (1 cho từng mục).

---

### Step 11: Self-verify toàn bộ
**Skill Invocation:**
  - **Primary:** `debugging`.
  - **Reference:** `code-review`.
  - **Fallback:** `backend-development`.

**Verify commands (PowerShell):**
```powershell
cd d:\appDK

# 1) All Python imports compile
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.routers.admin_users import router; print('admin_users OK')"
python -c "from apps.api.routers.admin_credit import router; print('admin_credit OK')"
python -c "from apps.api.routers.admin_pricing import router; print('admin_pricing OK')"

# 2) Admin routes registered
python -c "from apps.api.main import app; routes = sorted([r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path]); print(len(routes), 'admin routes'); print('\n'.join(routes))"

# 3) Existing test không regression
cd apps\api
python -m pytest test_credit_manager.py -v 2>&1 | Select-String "PASSED|FAILED"

# 4) TS compile
cd ..\..\apps\web
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"

# 5) 3 trang admin tồn tại
Test-Path "app\(admin)\admin\users\page.tsx"
Test-Path "app\(admin)\admin\users\[id]\page.tsx"
Test-Path "app\(admin)\admin\credits\page.tsx"
```

**Expected output:**
- 4 dòng "OK"
- 15+ admin routes in list
- 2 tests PASSED
- 0 errors TS
- 3 file = True

**Nếu bất kỳ check nào fail:**
- Invoke skill `debugging`.
- Ghi vào `BLOCKERS.md` với format:
  ```
  ## Step X failure
  - Verify command: ...
  - Expected: ...
  - Actual: ...
  - Hypothesized cause: ...
  ```

---

## Definition of Done cho Phase này
- Migration 0022 đã apply (Phase 5 đã làm).
- 3 routers admin mới (`admin_users`, `admin_credit`, `admin_pricing`) mount trong `main.py`.
- 13+ endpoint admin trả về status code đúng (200/201/204/400/404/403).
- 4 web proxy routes mới (users + adjust-credit + ledger + pricing list).
- 3 trang admin UI (`/admin/users`, `/admin/users/[id]`, `/admin/credits`) render không lỗi.
- Sidebar enable Users + Credits.
- TS compile 0 errors.
- Existing pytest PASSED.
- Mọi mutation admin ghi được vào `admin_audit_logs` (qua Supabase Dashboard check).
- KHÔNG file nào trong `apps/api/dependencies/admin.py`, `apps/api/services/audit.py`, migration 0022, user-facing routes bị đụng.
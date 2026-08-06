"""
Admin User Management — 9 endpoints.
Mounted dưới /api/admin/users.
Tất cả PHẢI có Depends(require_admin) và mutation PHẢI gọi log_admin_action().
"""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from apps.api.dependencies.admin import require_admin, require_mfa_for_critical
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
    Phát short-lived token bằng Supabase Auth admin API.

    Implementation: dùng supabase.auth.admin.create_session(user_id) để lấy
    access_token + refresh_token thật, set expires_at theo ttl_minutes.

    Mọi hành động trong session impersonate đều log với `impersonated_by`.
    """
    db = get_supabase_admin()

    target = db.table("users").select("email").eq("id", user_id).single().execute()
    if not target.data:
        raise HTTPException(404, "User not found")

    # Gọi Supabase Auth admin API để tạo session thật
    expires_in = payload.ttl_minutes * 60  # seconds
    try:
        session_res = db.auth.admin.create_session({
            "user_id": user_id,
            "expires_in": expires_in,
        })
    except Exception as exc:
        # Nếu Supabase Auth không hỗ trợ create_session (một số phiên bản cũ),
        # fallback về create_user trick + magic link. Tạm raise 503 để admin biết.
        raise HTTPException(
            status_code=503,
            detail=f"Impersonate failed — Supabase Auth admin API error: {exc}",
        )

    if not session_res or not getattr(session_res, "session", None):
        raise HTTPException(500, "Supabase did not return a session")

    session = session_res.session
    access_token = getattr(session, "access_token", None)
    refresh_token = getattr(session, "refresh_token", None)
    if not access_token:
        raise HTTPException(500, "Supabase session missing access_token")

    # Audit log MUST ghi rõ impersonate
    admin_email = (
        db.table("users")
        .select("email")
        .eq("id", admin_id)
        .single()
        .execute()
        .data.get("email", "")
    )
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action="user.impersonate",
        target_type="user",
        target_id=user_id,
        after={
            "impersonated_email": target.data.get("email"),
            "ttl_minutes": payload.ttl_minutes,
            "issued_at": datetime.now(timezone.utc).isoformat(),
        },
        reason=f"Impersonate {target.data.get('email')} for {payload.ttl_minutes}min",
        ip=request.client.host if request.client else None,
    )

    return {
        "token": access_token,
        "refresh_token": refresh_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=payload.ttl_minutes)).isoformat(),
        "expires_in": expires_in,
        "impersonated_by": admin_id,
        "impersonated_email": target.data.get("email"),
        "impersonated_user_id": user_id,
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
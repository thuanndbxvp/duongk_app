"""
Admin MFA Management — 5 endpoints (status, enroll, verify, disable, regenerate-backup-codes).
Mounted dưới /api/admin/mfa.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from uuid import UUID
from apps.api.dependencies.admin import require_admin
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.audit import log_admin_action
from apps.api.services.mfa_setup import (
    start_enrollment,
    verify_and_activate,
    disable_mfa,
    get_active_secret,
)
from apps.api.services.mfa import (
    generate_backup_codes,
    hash_backup_code,
    is_user_locked,
    verify_totp,
)


router = APIRouter(prefix="/api/admin/mfa", tags=["Admin MFA"])


class VerifyRequest(BaseModel):
    code: str


class DisableRequest(BaseModel):
    code: str  # Yêu cầu verify trước khi disable


@router.get("")
async def get_mfa_status(
    admin_id: str = Depends(require_admin),
):
    """Get MFA status cho current admin."""
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    
    result = (
        db.table('mfa_challenges')
        .select('status, enrolled_at, last_verified_at, failed_attempts, locked_until')
        .eq('user_id', admin_id)
        .in_('status', ['pending', 'active'])
        .order('updated_at', desc=True)
        .limit(1)
        .execute()
    )
    
    if not result.data:
        return {'status': 'not_enrolled', 'can_enroll': True}
    
    return {
        'status': result.data[0]['status'],
        'enrolled_at': result.data[0].get('enrolled_at'),
        'last_verified_at': result.data[0].get('last_verified_at'),
        'failed_attempts': result.data[0].get('failed_attempts', 0),
        'locked_until': result.data[0].get('locked_until'),
    }


@router.post("/enroll")
async def enroll_mfa(
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Step 1: Generate secret + QR + backup codes. status=pending."""
    db = get_supabase_admin()
    user_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    
    enrollment = start_enrollment(admin_id, user_email)
    
    admin_email = user_email
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='mfa.enroll_started',
        target_type='mfa',
        target_id=admin_id,
        ip=request.client.host if request.client else None,
    )
    
    # KHÔNG return qr_png_base64 nếu 1MB+ — return URL tới /api/admin/mfa/qr/{id}
    return enrollment


@router.post("/verify")
async def verify_mfa_code(
    payload: VerifyRequest,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Step 2: User nhập 6-digit code → verify → activate."""
    if is_user_locked(admin_id):
        raise HTTPException(423, 'MFA locked — wait 15 minutes')
    
    success = verify_and_activate(admin_id, payload.code)
    if not success:
        raise HTTPException(401, 'Invalid MFA code')
    
    db = get_supabase_admin()
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='mfa.activated',
        target_type='mfa',
        target_id=admin_id,
        ip=request.client.host if request.client else None,
    )
    
    return {'status': 'active'}


@router.post("/disable")
async def disable_admin_mfa(
    payload: DisableRequest,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Disable MFA. Yêu cầu verify code trước."""
    secret = get_active_secret(admin_id)
    if not secret:
        raise HTTPException(400, 'MFA not active')
    
    if not verify_totp(secret, payload.code):
        raise HTTPException(401, 'Invalid MFA code — cannot disable')
    
    disable_mfa(admin_id)
    
    db = get_supabase_admin()
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='mfa.disabled',
        target_type='mfa',
        target_id=admin_id,
        ip=request.client.host if request.client else None,
    )
    
    return {'status': 'disabled'}


@router.post("/regenerate-backup-codes")
async def regenerate_backup_codes(
    payload: VerifyRequest,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Generate new 10 backup codes (invalidate old). Require MFA verify trước."""
    secret = get_active_secret(admin_id)
    if not secret:
        raise HTTPException(400, 'MFA not active')
    
    if not verify_totp(secret, payload.code):
        raise HTTPException(401, 'Invalid MFA code')
    
    db = get_supabase_admin()
    
    # Generate new
    new_codes = generate_backup_codes(count=10, length=8)
    new_hashes = [hash_backup_code(c) for c in new_codes]
    
    # Delete old + insert new
    db.table('mfa_backup_codes').delete().eq('user_id', admin_id).execute()
    db.table('mfa_backup_codes').insert([
        {'user_id': admin_id, 'code_hash': h}
        for h in new_hashes
    ]).execute()
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='mfa.backup_regenerated',
        target_type='mfa',
        target_id=admin_id,
        ip=request.client.host if request.client else None,
    )
    
    # Return plaintext codes (1 lần)
    return {'backup_codes': new_codes}
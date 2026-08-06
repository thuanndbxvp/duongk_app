"""
RBAC dependency cho admin endpoints.
Yêu cầu user có role 'admin' hoặc 'super_admin'.
"""
import functools
from typing import Optional
from fastapi import Depends, HTTPException, Request
from apps.api.dependencies.auth import get_supabase_user
from apps.api.services.credit_manager import get_user_role


_ROLE_CACHE: dict[str, tuple[str, float]] = {}
_CACHE_TTL = 60  # seconds


def require_admin(request: Request, user_id: str = Depends(get_supabase_user)) -> str:
    """
    Verify user có role admin/super_admin.

    Args:
        request: FastAPI request (used to read dev role from `state`).
        user_id: Từ JWT (auto-injected bởi get_supabase_user).

    Returns:
        user_id nếu pass.

    Raises:
        HTTPException 403 nếu không phải admin.
    """
    import time

    # Dev mode shortcut: honor role embedded in the dev mock token.
    dev_role = getattr(request.state, 'dev_role', None)
    if dev_role:
        if dev_role not in ('admin', 'super_admin'):
            raise HTTPException(403, f'Admin only (dev role={dev_role})')
        return user_id

    cached = _ROLE_CACHE.get(user_id)
    if cached:
        role, expires_at = cached
        if time.time() < expires_at:
            if role not in ('admin', 'super_admin'):
                raise HTTPException(403, 'Admin only')
            return user_id

    role = get_user_role(user_id)
    _ROLE_CACHE[user_id] = (role, time.time() + _CACHE_TTL)

    if role not in ('admin', 'super_admin'):
        raise HTTPException(403, 'Admin only')
    return user_id


def require_super_admin(user_id: str = Depends(get_supabase_user)) -> str:
    """Require role = 'super_admin' only."""
    role = get_user_role(user_id)
    if role != 'super_admin':
        raise HTTPException(403, f'Super admin required (got role={role})')
    return user_id


def require_mfa_for_critical(user_id: str, mfa_code: Optional[str] = None) -> bool:
    """
    Verify MFA code cho critical operations.
    Caller phải check role=super_admin + lấy X-MFA-Code header.
    
    Returns True nếu:
    - User không phải super_admin → bypass
    - Super admin có valid TOTP code
    - Super admin có valid backup code
    
    Raises:
        HTTPException 401 nếu super_admin + invalid/missing code
        HTTPException 423 nếu locked
    """
    role = get_user_role(user_id)
    if role != 'super_admin':
        return True  # Non-super_admin không cần MFA
    
    if not mfa_code:
        raise HTTPException(401, 'MFA code required (X-MFA-Code header missing)')
    
    # Check lockout
    from apps.api.services.mfa import is_user_locked, record_failed_attempt, reset_failed_attempts, verify_backup_code
    if is_user_locked(user_id):
        raise HTTPException(423, 'MFA locked — too many failed attempts. Wait 15 minutes.')
    
    # Get secret
    from apps.api.services.mfa_setup import get_active_secret
    secret = get_active_secret(user_id)
    if not secret:
        raise HTTPException(401, 'MFA not enrolled. Setup MFA first.')
    
    # Verify TOTP code (6 digits)
    from apps.api.services.mfa import verify_totp
    if mfa_code.isdigit() and len(mfa_code) == 6 and verify_totp(secret, mfa_code):
        reset_failed_attempts(user_id)
        return True
    
    # Try backup code (8 chars)
    if verify_backup_code(user_id, mfa_code):
        reset_failed_attempts(user_id)
        return True
    
    # Failed
    count = record_failed_attempt(user_id)
    if count >= 5:
        raise HTTPException(423, 'MFA locked — 5 failed attempts. Wait 15 minutes.')
    raise HTTPException(401, f'Invalid MFA code ({count}/5 attempts)')
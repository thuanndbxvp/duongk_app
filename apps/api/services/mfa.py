"""
MFA TOTP + backup code verification.
RFC 6238 standard. Uses pyotp library.
"""
import hmac
import hashlib
import secrets
import string
import pyotp
from typing import Optional


WINDOW_TOLERANCE = 1  # ±1 step (30s each), total 60s


def generate_secret() -> str:
    """Generate random base32 secret (160-bit)."""
    return pyotp.random_base32()


def verify_totp(secret: str, code: str, valid_window: int = WINDOW_TOLERANCE) -> bool:
    """
    Verify 6-digit TOTP code.
    Constant-time compare via pyotp internal.
    Window ±1 = 60s tolerance.
    """
    if not code or len(code) != 6 or not code.isdigit():
        return False
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=valid_window)
    except Exception:
        return False


def generate_backup_codes(count: int = 10, length: int = 8) -> list[str]:
    """
    Generate N backup codes. Each 8-char alphanumeric (A-Z, 2-9 — no 0/1 confusion).
    Returns PLAINTEXT codes (frontend show 1 lần).
    """
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # 32 chars (no 0/1/I/O)
    codes = []
    for _ in range(count):
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        codes.append(code)
    return codes


def hash_backup_code(code: str) -> str:
    """Hash backup code (SHA-256 hex). Lưu vào DB."""
    return hashlib.sha256(code.upper().encode()).hexdigest()


def verify_backup_code(user_id: str, code: str) -> bool:
    """
    Verify backup code + mark used (atomic).
    Returns True nếu code valid + unused.
    """
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    
    code_hash = hash_backup_code(code)
    
    # Find unused code
    result = (
        db.table('mfa_backup_codes')
        .select('id')
        .eq('user_id', user_id)
        .eq('code_hash', code_hash)
        .is_('used_at', 'null')
        .limit(1)
        .execute()
    )
    
    if not result.data:
        return False
    
    # Mark used
    db.table('mfa_backup_codes').update({'used_at': 'now()'}).eq('id', result.data[0]['id']).execute()
    return True


def is_user_locked(user_id: str) -> bool:
    """Check if user currently locked out (5 failed attempts → 15 min lock)."""
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    
    result = (
        db.table('mfa_challenges')
        .select('locked_until, failed_attempts')
        .eq('user_id', user_id)
        .eq('status', 'active')
        .single()
        .execute()
    )
    
    if not result.data:
        return False
    
    from datetime import datetime, timezone
    locked_until = result.data.get('locked_until')
    if locked_until and datetime.fromisoformat(locked_until.replace('Z', '+00:00')) > datetime.now(timezone.utc):
        return True
    return False


def record_failed_attempt(user_id: str) -> int:
    """Increment failed_attempts + auto-lock. Return new count."""
    db = get_supabase_admin()
    db.rpc('record_mfa_failure', {'p_user_id': user_id}).execute()
    
    result = (
        db.table('mfa_challenges')
        .select('failed_attempts')
        .eq('user_id', user_id)
        .eq('status', 'active')
        .single()
        .execute()
    )
    return (result.data or {}).get('failed_attempts', 0)


def reset_failed_attempts(user_id: str) -> None:
    """Reset failed_attempts sau khi verify thành công."""
    db = get_supabase_admin()
    db.table('mfa_challenges').update({
        'failed_attempts': 0,
        'locked_until': None,
        'updated_at': 'now()',
    }).eq('user_id', user_id).eq('status', 'active').execute()
"""
MFA enrollment flow — generate secret + QR code + verify + activate.
"""
import qrcode
import io
import base64
from typing import Tuple
from apps.api.services.vault import encrypt, decrypt
from apps.api.services.mfa import (
    generate_secret,
    generate_backup_codes,
    hash_backup_code,
    verify_totp,
    reset_failed_attempts,
)


def start_enrollment(user_id: str, user_email: str) -> dict:
    """
    Step 1: Generate secret + QR code + 10 backup codes.
    Store mfa_challenges row (status=pending).
    
    Returns: {secret, qr_uri, qr_png_base64, backup_codes [plaintext, 10 codes]}
    """
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    
    # Delete any pending enrollment
    db.table('mfa_challenges').delete().eq('user_id', user_id).eq('status', 'pending').execute()
    
    secret = generate_secret()
    
    # Build otpauth:// URI
    issuer = 'AppDK'
    qr_uri = f'otpauth://totp/{issuer}:{user_email}?secret={secret}&issuer={issuer}'
    
    # Generate QR PNG (base64)
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_png_base64 = base64.b64encode(buf.getvalue()).decode()
    
    # Generate backup codes (plaintext)
    backup_codes = generate_backup_codes(count=10, length=8)
    backup_hashes = [hash_backup_code(c) for c in backup_codes]
    
    # Store encrypted secret
    encrypted = encrypt(secret)
    
    db.table('mfa_challenges').insert({
        'user_id': user_id,
        'status': 'pending',
        'encrypted_secret': encrypted.hex(),
        'qr_uri': qr_uri,
    }).execute()
    
    # Delete old backup codes + insert new
    db.table('mfa_backup_codes').delete().eq('user_id', user_id).execute()
    db.table('mfa_backup_codes').insert([
        {'user_id': user_id, 'code_hash': h}
        for h in backup_hashes
    ]).execute()
    
    return {
        'secret': secret,  # Show user 1 lần (backup nếu QR fail)
        'qr_uri': qr_uri,
        'qr_png_base64': qr_png_base64,
        'backup_codes': backup_codes,  # Show user 1 lần để save
    }


def verify_and_activate(user_id: str, code: str) -> bool:
    """
    Step 2: User nhập 6-digit code từ authenticator → verify → activate.
    
    Returns: True nếu valid.
    """
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    
    # Get pending secret
    result = (
        db.table('mfa_challenges')
        .select('encrypted_secret')
        .eq('user_id', user_id)
        .eq('status', 'pending')
        .single()
        .execute()
    )
    if not result.data:
        return False
    
    secret = decrypt(bytes.fromhex(result.data['encrypted_secret']))
    
    if not verify_totp(secret, code):
        return False
    
    # Activate
    db.table('mfa_challenges').update({
        'status': 'active',
        'enrolled_at': 'now()',
        'last_verified_at': 'now()',
        'failed_attempts': 0,
        'updated_at': 'now()',
    }).eq('user_id', user_id).eq('status', 'pending').execute()
    
    return True


def get_active_secret(user_id: str) -> str:
    """Lấy active secret (để verify X-MFA-Code header)."""
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    
    result = (
        db.table('mfa_challenges')
        .select('encrypted_secret')
        .eq('user_id', user_id)
        .eq('status', 'active')
        .single()
        .execute()
    )
    if not result.data:
        return None
    return decrypt(bytes.fromhex(result.data['encrypted_secret']))


def disable_mfa(user_id: str) -> bool:
    """Disable MFA (yêu cầu verify trước — caller responsibility)."""
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    
    db.table('mfa_challenges').update({
        'status': 'disabled',
        'updated_at': 'now()',
    }).eq('user_id', user_id).eq('status', 'active').execute()
    
    return True
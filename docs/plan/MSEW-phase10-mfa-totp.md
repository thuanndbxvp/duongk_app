# MSEW: phase10-mfa-totp

## Prerequisites (Điều kiện tiên quyết)
- **Đọc CONTEXT:** `docs/plan/CONTEXT-phase10-mfa-totp.md`
- **Đọc PLAN:** `docs/plan/PLAN-phase10-mfa-totp.md`
- **Admin Panel MVP xong (Phase 5-9):** 32 endpoint + 7 UI page + 5 service.
- **Branch:** main
- **Working dir:** `d:\appDK`
- **Line Ending:** CRLF

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | Migration `0027_mfa_challenges.sql` | `database-admin` | `better-auth` | `backend-development` |
| 2 | Service `mfa.py` | `better-auth` | `backend-development` | `debugging` |
| 3 | Service `mfa_setup.py` | `better-auth` | `backend-development` | `debugging` |
| 4 | UPDATE `dependencies/admin.py` | `better-auth` | `backend-development` | `code-review` |
| 5 | UPDATE 3 admin routers (MFA header) | `backend-development` | `better-auth` | `code-review` |
| 6 | Router `admin_mfa.py` | `better-auth` | `backend-development` | `database-admin` |
| 7 | UPDATE `main.py` | `backend-development` | `debugging` | `code-review` |
| 8 | 3 web proxy routes | `frontend-development` | `better-auth` | `debugging` |
| 9 | UI `admin/security/mfa/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` |
| 10 | UPDATE `layout.tsx` | `frontend-development` | `ui-styling` | `debugging` |
| 11 | Self-verify | `debugging` | `code-review` | `better-auth` |

## Files KHÔNG được đụng (Do Not Touch)
- Phase 5/6/7/8/9 files NGOẠI TRỪ:
  - `apps/api/dependencies/admin.py` (UPDATE — thêm dependency mới)
  - `apps/api/routers/admin_users.py` (UPDATE — DELETE check MFA)
  - `apps/api/routers/admin_api_keys.py` (UPDATE — DELETE/rotate check MFA)
  - `apps/api/routers/admin_audit.py` (UPDATE — export CSV check MFA)
  - `apps/api/main.py` (UPDATE — mount router)
  - `apps/web/app/(admin)/layout.tsx` (UPDATE — sidebar)
- User-facing routes.
- `apps/api/services/vault.py` (Phase 7) — dùng để encrypt secret nhưng KHÔNG sửa.

---

## Micro-Steps

### Step 1: Tạo `supabase/migrations/0027_mfa_challenges.sql`
**File:** `supabase/migrations/0027_mfa_challenges.sql` (NEW)
**Skill Invocation:**
  - **Primary:** `database-admin`.
  - **Reference:** `better-auth`.
  - **Fallback:** `backend-development`.

**Code cần viết:**
```sql
-- ============================================================
-- Migration: 0027_mfa_challenges.sql
-- Purpose: MFA TOTP + backup codes storage for super_admin
-- ============================================================

-- Main MFA enrollment table
CREATE TABLE IF NOT EXISTS mfa_challenges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('pending','active','disabled')),
  encrypted_secret BYTEA NOT NULL,           -- Fernet-encrypted TOTP secret
  qr_uri TEXT,                               -- otpauth:// URI
  enrolled_at TIMESTAMPTZ,
  last_verified_at TIMESTAMPTZ,
  failed_attempts INT NOT NULL DEFAULT 0,
  locked_until TIMESTAMPTZ,                  -- Brute force lockout (5 fail → 15 min)
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, status) DEFERRABLE INITIALLY DEFERRED  -- 1 active per user
);

CREATE INDEX IF NOT EXISTS idx_mfa_user_status ON mfa_challenges(user_id, status);

-- Backup codes table (10 codes per user, 1-time use)
CREATE TABLE IF NOT EXISTS mfa_backup_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  code_hash TEXT NOT NULL,                   -- SHA-256 hex of code
  used_at TIMESTAMPTZ,                       -- null = unused
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backup_codes_user ON mfa_backup_codes(user_id);

-- RLS: deny non-service
ALTER TABLE mfa_challenges ENABLE ROW LEVEL SECURITY;
ALTER TABLE mfa_backup_codes ENABLE ROW LEVEL SECURITY;

-- RPC: increment failed_attempts + lock if needed (atomic)
CREATE OR REPLACE FUNCTION record_mfa_failure(p_user_id UUID) RETURNS VOID AS $$
BEGIN
  UPDATE mfa_challenges
  SET failed_attempts = failed_attempts + 1,
      locked_until = CASE WHEN failed_attempts + 1 >= 5 THEN NOW() + INTERVAL '15 minutes' ELSE locked_until END,
      updated_at = NOW()
  WHERE user_id = p_user_id AND status = 'active';
END;
$$ LANGUAGE plpgsql;
```

**Verify command:**
```powershell
# Apply via Supabase Dashboard SQL Editor
```
**Expected:** 2 tables + 1 RPC created.

---

### Step 2: Tạo `apps/api/services/mfa.py`
**File:** `apps/api/services/mfa.py` (NEW)
**Vai trò:** TOTP verify + backup code verify (RFC 6238).
**Skill Invocation:**
  - **Primary:** `better-auth`.
  - **Reference:** `backend-development`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
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
```

**Verify command:**
```powershell
pip install pyotp
cd d:\appDK
python -c "from apps.api.services.mfa import generate_secret, verify_totp, generate_backup_codes, hash_backup_code; s = generate_secret(); print('secret:', s[:10] + '...'); codes = generate_backup_codes(); print('codes:', codes[:3]); import pyotp; code = pyotp.TOTP(s).now(); print('verify:', verify_totp(s, code))"
```

**Expected output:**
```
secret: ABCDEFGHIJ...
codes: ['ABCD2345', 'EFGH6789', 'JKLM3456']
verify: True
```

---

### Step 3: Tạo `apps/api/services/mfa_setup.py`
**File:** `apps/api/services/mfa_setup.py` (NEW)
**Vai trò:** Enrollment flow (generate secret + QR + verify + activate).
**Skill Invocation:**
  - **Primary:** `better-auth`.
  - **Reference:** `backend-development`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
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
```

**Verify command:**
```powershell
pip install qrcode[pil]
python -c "from apps.api.services.mfa_setup import start_enrollment, verify_and_activate; print('mfa_setup OK')"
```

**Expected output:** `mfa_setup OK`.

---

### Step 4: UPDATE `apps/api/dependencies/admin.py`
**File:** `apps/api/dependencies/admin.py` (UPDATE)
**Vị trí:** Cuối file.
**Skill Invocation:**
  - **Primary:** `better-auth`.
  - **Reference:** `backend-development`.
  - **Fallback:** `code-review`.

**Code cần viết (THÊM function cuối file):**
```python
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
```

**Thêm import đầu file:**
```python
from typing import Optional
```

**KHÔNG sửa:** `require_admin()` function (giữ nguyên cho 32 endpoint Phase 5-9).

**Verify command:**
```powershell
python -c "from apps.api.dependencies.admin import require_admin, require_super_admin, require_mfa_for_critical; print('admin deps OK')"
```

**Expected output:** `admin deps OK`.

---

### Step 5: UPDATE 3 admin routers (header check MFA)
**Files (3 UPDATE):**
- `apps/api/routers/admin_users.py` (Phase 6)
- `apps/api/routers/admin_api_keys.py` (Phase 7)
- `apps/api/routers/admin_audit.py` (Phase 9)

**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `code-review`.

**Pattern chung cho mỗi file:**

**`admin_users.py`** — Modify `DELETE /api/admin/users/{user_id}`:
```python
@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Soft-delete user. Require MFA for super_admin."""
    mfa_code = request.headers.get('X-MFA-Code')
    require_mfa_for_critical(admin_id, mfa_code)
    
    # ... existing logic ...
```

**`admin_api_keys.py`** — Modify `DELETE` + `POST /rotate`:
```python
@router.delete("/{key_id}")
async def archive_key(
    key_id: str,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Archive API key. Require MFA for super_admin."""
    mfa_code = request.headers.get('X-MFA-Code')
    require_mfa_for_critical(admin_id, mfa_code)
    
    # ... existing logic ...

@router.post("/{key_id}/rotate")
async def rotate_key(
    key_id: str,
    payload: KeyRotate,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Rotate API key. Require MFA for super_admin."""
    mfa_code = request.headers.get('X-MFA-Code')
    require_mfa_for_critical(admin_id, mfa_code)
    
    # ... existing logic ...
```

**`admin_audit.py`** — Modify `GET /export/csv`:
```python
@router.get("/export/csv")
async def export_audit_csv(
    admin_id: str = Depends(require_admin),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    """Export audit log. Require MFA for super_admin."""
    from fastapi import Request
    request: Request = None  # Need actual request — modify signature
    mfa_code = request.headers.get('X-MFA-Code')
    require_mfa_for_critical(admin_id, mfa_code)
    
    # ... existing logic ...
```

**Lưu ý:** `export_audit_csv` cần thêm `request: Request` parameter (FastAPI tự inject). Modify signature:
```python
async def export_audit_csv(
    request: Request,
    admin_id: str = Depends(require_admin),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
```

**Verify command:**
```powershell
python -c "from apps.api.routers.admin_users import router as ru; from apps.api.routers.admin_api_keys import router as rak; from apps.api.routers.admin_audit import router as ra; print('3 routers OK')"
```

**Expected output:** `3 routers OK`.

---

### Step 6: Tạo `apps/api/routers/admin_mfa.py`
**File:** `apps/api/routers/admin_mfa.py` (NEW)
**Skill Invocation:**
  - **Primary:** `better-auth`.
  - **Reference:** `backend-development`.
  - **Fallback:** `database-admin`.

**Code cần viết:**
```python
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
```

**Verify command:**
```powershell
python -c "from apps.api.routers.admin_mfa import router; print('admin_mfa OK')"
```

**Expected output:** `admin_mfa OK`.

---

### Step 7: UPDATE `apps/api/main.py` mount router
**File:** `apps/api/main.py` (UPDATE)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `debugging`.
  - **Fallback:** `code-review`.

**Code cần viết:**

**SAU** Phase 9 admin imports, **THÊM:**
```python
from apps.api.routers.admin_mfa import router as admin_mfa_router
```

**SAU** Phase 9 admin mounts, **THÊM:**
```python
app.include_router(admin_mfa_router)
```

**Verify command:**
```powershell
python -c "from apps.api.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and 'mfa' in r.path]; print(len(routes), 'mfa routes'); [print(r) for r in sorted(routes)]"
```

**Expected output:** ≥ 6 routes (status + enroll + verify + disable + regenerate-backup + nested).

---

### Step 8: Tạo 3 web proxy routes
**Files (3 NEW):**
- `apps/web/app/api/admin/mfa/route.ts`
- `apps/web/app/api/admin/mfa/verify/route.ts`
- `apps/web/app/api/admin/mfa/disable/route.ts`
- `apps/web/app/api/admin/mfa/regenerate-backup-codes/route.ts`

**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `better-auth`.
  - **Fallback:** `debugging`.

**Pattern lặp lại tương tự các phase trước.** Lưu ý: KHÔNG proxy `X-MFA-Code` header (để frontend tự include).

**Verify command:**
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"
```

**Expected output:** No errors.

---

### Step 9: Tạo `apps/web/app/(admin)/admin/security/mfa/page.tsx`
**File:** `apps/web/app/(admin)/admin/security/mfa/page.tsx` (NEW)
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `aesthetic`.

**Code cần viết:**
```tsx
'use client';

import { useEffect, useState } from 'react';

type MfaStatus = 'not_enrolled' | 'pending' | 'active' | 'disabled';

interface EnrollmentData {
  secret: string;
  qr_uri: string;
  qr_png_base64: string;
  backup_codes: string[];
}

export default function AdminMfaPage() {
  const [status, setStatus] = useState<MfaStatus>('not_enrolled');
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [enrollment, setEnrollment] = useState<EnrollmentData | null>(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [disableCode, setDisableCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/admin/mfa').then(r => r.json()).then(d => {
      setStatus(d.status);
      setLoading(false);
    });
  }, []);

  async function handleEnroll() {
    setError('');
    const res = await fetch('/api/admin/mfa/enroll', { method: 'POST' });
    if (res.ok) {
      setEnrollment(await res.json());
      setStep(2);
      setStatus('pending');
    } else {
      setError('Enroll failed');
    }
  }

  async function handleVerify() {
    setError('');
    const res = await fetch('/api/admin/mfa/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: verifyCode }),
    });
    if (res.ok) {
      setStep(3);
      setStatus('active');
    } else {
      const err = await res.json();
      setError(err.detail || 'Invalid code');
    }
  }

  async function handleDisable() {
    setError('');
    const res = await fetch('/api/admin/mfa/disable', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: disableCode }),
    });
    if (res.ok) {
      setStatus('disabled');
      setStep(1);
      setEnrollment(null);
      setDisableCode('');
    } else {
      const err = await res.json();
      setError(err.detail);
    }
  }

  if (loading) return <div className="p-8 text-center text-[var(--fg-tertiary)]">Loading…</div>;

  return (
    <div className="p-8 space-y-6 animate-fade-up max-w-3xl">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin · Security
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Multi-Factor Auth</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">Bảo vệ tài khoản super_admin bằng TOTP (Google Authenticator / 1Password).</p>
      </div>

      {/* Status banner */}
      <div className={`glass rounded-2xl p-5 border-l-4 ${
        status === 'active' ? 'border-green-500' :
        status === 'pending' ? 'border-orange-500' :
        status === 'disabled' ? 'border-red-500' : 'border-blue-500'
      }`}>
        <p className="text-sm">
          Status: <strong>{status === 'active' ? '✓ Active' : status === 'pending' ? '⏳ Pending' : status === 'disabled' ? '✗ Disabled' : '○ Not enrolled'}</strong>
        </p>
        {status === 'active' && (
          <button onClick={() => setStep(1)} className="mt-3 text-sm text-red-400 underline">
            Disable MFA
          </button>
        )}
      </div>

      {error && <div className="glass rounded-xl p-3 text-sm text-red-400">{error}</div>}

      {/* Step 1: Setup */}
      {step === 1 && status !== 'active' && (
        <div className="glass rounded-2xl p-6 space-y-4">
          <h2 className="text-xl font-bold">Setup MFA</h2>
          <ol className="space-y-2 text-sm text-[var(--fg-secondary)]">
            <li>1. Cài <strong>Google Authenticator</strong> hoặc <strong>1Password</strong></li>
            <li>2. Click "Generate QR Code" bên dưới</li>
            <li>3. Scan QR → app hiển thị 6-digit code</li>
            <li>4. Nhập code → verify</li>
            <li>5. Save 10 backup codes ở nơi an toàn</li>
          </ol>
          <button onClick={handleEnroll} className="w-full px-4 py-3 rounded-lg bg-[var(--brand-500)] text-white font-semibold">
            Generate QR Code
          </button>
        </div>
      )}

      {/* Step 1 disable: input code */}
      {step === 1 && status === 'active' && (
        <div className="glass rounded-2xl p-6 space-y-4">
          <h2 className="text-xl font-bold text-red-400">Disable MFA</h2>
          <p className="text-sm text-[var(--fg-secondary)]">Nhập TOTP code hiện tại để xác nhận disable:</p>
          <input type="text" value={disableCode} onChange={(e) => setDisableCode(e.target.value)} maxLength={8}
            placeholder="123456 (TOTP) hoặc ABCD2345 (backup)"
            className="w-full px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)]" />
          <button onClick={handleDisable} className="w-full px-4 py-3 rounded-lg bg-red-500 text-white font-semibold">
            Disable MFA
          </button>
        </div>
      )}

      {/* Step 2: Scan QR + verify */}
      {step === 2 && enrollment && (
        <div className="glass rounded-2xl p-6 space-y-4">
          <h2 className="text-xl font-bold">Scan QR Code</h2>
          <div className="flex justify-center bg-white p-4 rounded-lg">
            <img src={`data:image/png;base64,${enrollment.qr_png_base64}`} alt="MFA QR" className="w-64 h-64" />
          </div>
          <details className="text-xs">
            <summary className="cursor-pointer text-[var(--fg-tertiary)]">Không scan được? Hiển thị secret key</summary>
            <code className="block mt-2 p-2 bg-[var(--surface)] rounded font-mono break-all">{enrollment.secret}</code>
          </details>
          <hr className="border-[var(--glass-border)]" />
          <h3 className="font-semibold">Nhập 6-digit code từ authenticator:</h3>
          <input type="text" value={verifyCode} onChange={(e) => setVerifyCode(e.target.value)} maxLength={6}
            placeholder="123456"
            className="w-full px-3 py-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white text-center text-2xl tracking-widest placeholder:text-[var(--fg-tertiary)]" />
          <button onClick={handleVerify} disabled={verifyCode.length !== 6}
            className="w-full px-4 py-3 rounded-lg bg-[var(--brand-500)] text-white font-semibold disabled:opacity-30">
            Verify
          </button>
        </div>
      )}

      {/* Step 3: Save backup codes */}
      {step === 3 && enrollment && (
        <div className="glass rounded-2xl p-6 space-y-4 border-l-4 border-green-500">
          <h2 className="text-xl font-bold text-green-400">✓ MFA Active</h2>
          <p className="text-sm text-[var(--fg-secondary)]">Save 10 backup codes sau. Mỗi code dùng 1 lần khi mất authenticator.</p>
          <div className="grid grid-cols-2 gap-2 bg-[var(--surface)] rounded-lg p-4">
            {enrollment.backup_codes.map((code, i) => (
              <code key={i} className="font-mono text-sm text-[var(--brand-300)]">{code}</code>
            ))}
          </div>
          <button onClick={() => {
            navigator.clipboard.writeText(enrollment.backup_codes.join('\n'));
            alert('Copied!');
          }} className="w-full px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white text-sm">
            📋 Copy all
          </button>
          <button onClick={() => { setEnrollment(null); setStep(1); }} className="w-full px-4 py-3 rounded-lg bg-green-500 text-white font-semibold">
            Done — đã save
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

### Step 10: UPDATE `apps/web/app/(admin)/layout.tsx` add Security submenu
**File:** `apps/web/app/(admin)/layout.tsx` (UPDATE)
**Vị trí:** Sau Audit Logs (line 15).
**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `ui-styling`.
  - **Fallback:** `debugging`.

**Code cần viết:**

**Thêm dòng mới sau line 15 (Audit Logs):**
```typescript
  { href: '/admin/security/mfa', label: 'Security', icon: IconShield, enabled: true },
```

**Lưu ý:** Phase 10 chỉ thêm 1 submenu Security > MFA. Sidebar sẽ là flat list (Phase 11+ mới làm nested).

**Verify command:**
```powershell
Get-Content "apps\web\app\(admin)\layout.tsx" | Select-String "enabled:" | Measure-Object -Line
```

**Expected output:** 9 lines.

---

### Step 11: Self-verify toàn bộ
**Skill Invocation:**
  - **Primary:** `debugging`.
  - **Reference:** `code-review`.
  - **Fallback:** `better-auth`.

**Verify commands (PowerShell):**
```powershell
cd d:\appDK

# 1) Dependencies installed
pip show pyotp 2>&1 | Select-String "Name|Version"
pip show qrcode 2>&1 | Select-String "Name|Version"

# 2) All Python imports
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.services.mfa import generate_secret, verify_totp, generate_backup_codes; print('mfa OK')"
python -c "from apps.api.services.mfa_setup import start_enrollment, verify_and_activate; print('mfa_setup OK')"
python -c "from apps.api.dependencies.admin import require_admin, require_super_admin, require_mfa_for_critical; print('admin deps OK')"
python -c "from apps.api.routers.admin_mfa import router; print('admin_mfa OK')"

# 3) Admin MFA routes count
python -c "from apps.api.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and 'mfa' in r.path]; print(len(routes), 'mfa routes')"

# 4) Test TOTP roundtrip
python -c "from apps.api.services.mfa import generate_secret, verify_totp; import pyotp; s = generate_secret(); c = pyotp.TOTP(s).now(); print('roundtrip:', verify_totp(s, c))"

# 5) Test backup code generation + hash
python -c "from apps.api.services.mfa import generate_backup_codes, hash_backup_code; cs = generate_backup_codes(); print('codes:', cs[:3]); print('hash same:', hash_backup_code(cs[0]) == hash_backup_code(cs[0]))"

# 6) Existing test không regression
cd apps\api
python -m pytest test_credit_manager.py -v 2>&1 | Select-String "PASSED|FAILED"

# 7) TS compile
cd ..\..\apps\web
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"

# 8) UI page exists
Test-Path "app\(admin)\admin\security\mfa\page.tsx"
```

**Expected output:**
- 2 packages installed (pyotp, qrcode)
- 5 dòng "OK"
- ≥ 6 mfa routes
- `roundtrip: True`
- `hash same: True`
- 2 tests PASSED
- 0 errors TS
- 1 UI page = True

---

## Definition of Done cho Phase này
- Migration 0027 apply thành công (2 tables + 1 RPC).
- 2 service mới (`mfa.py` + `mfa_setup.py`).
- 1 dependency update (`require_super_admin` + `require_mfa_for_critical`).
- 3 admin router UPDATE (users DELETE, api_keys DELETE/rotate, audit export CSV).
- 1 router admin MFA (5 endpoints).
- 4 web proxy + 1 UI setup wizard + sidebar update.
- TS compile 0 errors.
- Existing pytest PASSED.
- Test enrollment flow: generate secret → verify code → activate.
- Test invalid code: 401.
- Test backup code: 1 lần.
- Test MFA header: super_admin DELETE user không có X-MFA-Code → 401.
- `pyotp` + `qrcode[pil]` đã cài.
- KHÔNG file nào trong Phase 5/6/7/8/9 bị đụng ngoài 6 file UPDATE đã nêu.
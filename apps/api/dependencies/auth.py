"""
JWT authentication dependency for FastAPI.
Uses PyJWT to verify Supabase Auth tokens.
"""
import base64
import json
import os
import time
import jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


security = HTTPBearer(auto_error=True)


def _is_dev_mode() -> bool:
    """Detect dev/mock mode.

    Dev mode is enabled when ANY of:
    - NEXT_PUBLIC_SUPABASE_URL contains 'xxx' (placeholder URL — frontend matches)
    - ENV=development (set explicitly in apps/api/.env)
    - SUPABASE_DEV_MODE=true (explicit opt-in)

    Production callers must NOT have any of these, so the dev mock token
    path is automatically disabled.
    """
    if os.getenv('ENV', '').lower() == 'development':
        return True
    if os.getenv('SUPABASE_DEV_MODE', '').lower() == 'true':
        return True
    url = os.getenv('NEXT_PUBLIC_SUPABASE_URL') or 'https://xxx.supabase.co'
    return 'xxx' in url


def _decode_dev_token(token: str) -> dict | None:
    """
    Decode a dev mock token (format: dev.<base64 payload>.mock).
    Returns the payload dict if valid, None otherwise.
    """
    parts = token.split('.')
    if len(parts) != 3 or parts[0] != 'dev' or parts[2] != 'mock':
        return None
    try:
        payload = json.loads(base64.b64decode(parts[1]).decode('utf-8'))
    except Exception:
        return None
    if not isinstance(payload, dict) or 'sub' not in payload:
        return None
    if 'exp' in payload and isinstance(payload['exp'], (int, float)):
        if payload['exp'] < time.time():
            return None
    return payload


def _stash_dev_role(request: Request | None, payload: dict) -> None:
    """When a dev token is used, expose its role on request.state so that
    `require_admin` can short-circuit the DB lookup in dev mode."""
    if request is not None:
        role = payload.get('role')
        if role:
            request.state.dev_role = role


def get_supabase_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Verify JWT from Supabase Auth and return user_id.

    In dev mode (NEXT_PUBLIC_SUPABASE_URL contains 'xxx'), also accepts
    the `dev.<base64 payload>.mock` token format used by the frontend.

    Args:
        request: FastAPI request (used to stash dev role on `state`).
        credentials: Bearer token from Authorization header

    Returns:
        user_id (UUID string) from JWT 'sub' claim

    Raises:
        HTTPException: 401 if token invalid, 500 if server misconfigured
    """
    token = credentials.credentials

    # Dev mode shortcut: accept mock token issued by frontend /api/auth/login.
    if _is_dev_mode():
        payload = _decode_dev_token(token)
        if payload is not None:
            _stash_dev_role(request, payload)
            return payload['sub']

    secret = os.getenv('SUPABASE_JWT_SECRET')

    if not secret:
        raise HTTPException(
            status_code=500,
            detail='Server misconfigured: SUPABASE_JWT_SECRET not set',
        )

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=['HS256'],
            audience='authenticated',
            options={
                'require': ['exp', 'sub', 'aud'],
                'verify_signature': True,
                'verify_exp': True,
                'verify_aud': True,
            },
        )
        return payload['sub']
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, 'Token expired')
    except jwt.InvalidAudienceError:
        raise HTTPException(401, 'Invalid token audience')
    except jwt.InvalidTokenError as e:
        raise HTTPException(401, f'Invalid token: {str(e)}')

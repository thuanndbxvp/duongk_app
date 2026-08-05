"""
JWT authentication dependency for FastAPI.
Uses PyJWT to verify Supabase Auth tokens.
"""
import os
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


security = HTTPBearer()


def get_supabase_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Verify JWT from Supabase Auth and return user_id.
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        user_id (UUID string) from JWT 'sub' claim
        
    Raises:
        HTTPException: 401 if token invalid, 500 if server misconfigured
    """
    token = credentials.credentials
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

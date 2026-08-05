"""
Unit tests for JWT auth dependency.
"""
import os
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient


SECRET = 'test-secret-12345'
USER_ID = '11111111-1111-1111-1111-111111111111'


@pytest.fixture(autouse=True)
def mock_secret():
    """Mock JWT secret."""
    os.environ['SUPABASE_JWT_SECRET'] = SECRET


@pytest.fixture
def valid_token():
    """Generate valid JWT token."""
    payload = {
        'sub': USER_ID,
        'aud': 'authenticated',
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        'email': 'test@example.com',
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')


@pytest.fixture
def expired_token():
    """Generate expired JWT token."""
    payload = {
        'sub': USER_ID,
        'aud': 'authenticated',
        'exp': datetime.now(timezone.utc) - timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')


@pytest.fixture
def wrong_signature_token():
    """Generate token with wrong signature."""
    payload = {
        'sub': USER_ID,
        'aud': 'authenticated',
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, 'wrong-secret', algorithm='HS256')


@pytest.fixture
def wrong_audience_token():
    """Generate token with wrong audience."""
    payload = {
        'sub': USER_ID,
        'aud': 'anon',
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')


@pytest.fixture
def missing_claims_token():
    """Generate token missing required claims."""
    payload = {
        'sub': USER_ID,
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        # Missing 'aud'
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')


class TestGetSupabaseUser:
    """Test JWT verify function."""

    def test_valid_token_returns_user_id(self, valid_token):
        """Test: valid token returns user_id."""
        from apps.api.dependencies.auth import get_supabase_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials=valid_token)
        user_id = get_supabase_user(credentials=creds)
        assert user_id == USER_ID

    def test_expired_token_raises_401(self, expired_token):
        """Test: expired token returns 401."""
        from apps.api.dependencies.auth import get_supabase_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials=expired_token)
        
        with pytest.raises(HTTPException) as exc:
            get_supabase_user(credentials=creds)
        assert exc.value.status_code == 401
        assert 'expired' in exc.value.detail.lower()

    def test_wrong_signature_raises_401(self, wrong_signature_token):
        """Test: forged token (wrong secret) returns 401."""
        from apps.api.dependencies.auth import get_supabase_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials=wrong_signature_token)
        
        with pytest.raises(HTTPException) as exc:
            get_supabase_user(credentials=creds)
        assert exc.value.status_code == 401

    def test_wrong_audience_raises_401(self, wrong_audience_token):
        """Test: wrong audience returns 401."""
        from apps.api.dependencies.auth import get_supabase_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials=wrong_audience_token)
        
        with pytest.raises(HTTPException) as exc:
            get_supabase_user(credentials=creds)
        assert exc.value.status_code == 401

    def test_missing_claims_raises_401(self, missing_claims_token):
        """Test: missing required claims returns 401."""
        from apps.api.dependencies.auth import get_supabase_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials=missing_claims_token)
        
        with pytest.raises(HTTPException) as exc:
            get_supabase_user(credentials=creds)
        assert exc.value.status_code == 401

    def test_no_secret_raises_500(self):
        """Test: missing JWT secret returns 500."""
        from apps.api.dependencies.auth import get_supabase_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        os.environ.pop('SUPABASE_JWT_SECRET', None)
        
        creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials='any-token')
        
        with pytest.raises(HTTPException) as exc:
            get_supabase_user(credentials=creds)
        assert exc.value.status_code == 500

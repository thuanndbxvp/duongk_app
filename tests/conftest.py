"""
Shared test fixtures.
"""
import pytest
import os
import jwt
from datetime import datetime, timedelta, timezone
from supabase import create_client


SUPABASE_URL = os.getenv('SUPABASE_URL', 'http://localhost:54321')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'test-key')
JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET', 'test-secret')


@pytest.fixture
def admin_client():
    """Admin client (bypasses RLS)."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@pytest.fixture
def make_user_token():
    """Generate JWT for a test user."""
    def _make(user_id: str, email: str = 'test@example.com') -> str:
        payload = {
            'sub': user_id,
            'aud': 'authenticated',
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
            'email': email,
        }
        return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return _make


@pytest.fixture
def user_client(make_user_token):
    """Create user-scoped client."""
    def _make(user_id: str):
        token = make_user_token(user_id)
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        client.auth.session = type('S', (), {'access_token': token})()
        return client
    return _make

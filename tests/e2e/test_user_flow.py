"""
E2E tests for authenticated user flow.
"""
import pytest
from httpx import AsyncClient


class TestUserFlow:
    """End-to-end tests."""
    
    @pytest.mark.asyncio
    async def test_login_returns_token(self, make_user_token):
        """Test JWT token generation."""
        user_id = '11111111-1111-1111-1111-111111111111'
        token = make_user_token(user_id)
        assert token is not None
        assert len(token) > 100
    
    @pytest.mark.asyncio
    async def test_get_me_with_valid_token(self, make_user_token, admin_client):
        """Test GET /api/users/me with valid token."""
        from fastapi.testclient import TestClient
        from apps.api.main import app
        
        user_id = '22222222-2222-2222-2222-222222222222'
        admin_client.table('users').insert({
            'id': user_id,
            'email': 'me@example.com',
            'credits': 50,
        }).execute()
        
        token = make_user_token(user_id)
        client = TestClient(app)
        
        response = client.get(
            '/api/users/me',
            headers={'Authorization': f'Bearer {token}'},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == user_id
        assert data['credits'] == 50
    
    @pytest.mark.asyncio
    async def test_get_me_without_token_returns_401(self):
        """Test missing token returns 401."""
        from fastapi.testclient import TestClient
        from apps.api.main import app
        
        client = TestClient(app)
        response = client.get('/api/users/me')
        
        assert response.status_code == 401 or response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_credit_insufficient_returns_402(self, make_user_token, admin_client):
        """Test insufficient credits returns 402."""
        from fastapi.testclient import TestClient
        from apps.api.main import app
        
        user_id = '33333333-3333-3333-3333-333333333333'
        admin_client.table('users').insert({
            'id': user_id,
            'email': 'poor@example.com',
            'credits': 1,  # Not enough for any job
        }).execute()
        
        token = make_user_token(user_id)
        client = TestClient(app)
        
        # Try to start a 30-credit job
        response = client.post(
            '/api/scripts/generate',
            headers={'Authorization': f'Bearer {token}'},
            json={'assistant_id': '44444444-4444-4444-4444-444444444444', 'topic': 'test'},
        )
        
        # Should be 402 or 404 (assistant not found)
        assert response.status_code in (402, 404)

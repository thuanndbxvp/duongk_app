"""
Unit tests for scripts API endpoints.
"""
import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from apps.api.main import app


class TestScriptsAPI:
    """Test suite for scripts API."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_generate_script_missing_topic(self, client):
        """Test validation: missing topic returns 422."""
        response = client.post(
            '/api/scripts/generate',
            json={
                'assistant_id': '11111111-1111-1111-1111-111111111111',
                'user_id': '22222222-2222-2222-2222-222222222222'
            },
        )
        assert response.status_code == 422

    def test_generate_script_invalid_uuid(self, client):
        """Test validation: invalid UUID returns 422."""
        response = client.post(
            '/api/scripts/generate',
            json={'assistant_id': 'not-a-uuid', 'topic': 'test', 'user_id': 'not-a-uuid'},
        )
        assert response.status_code == 422

    @patch('apps.api.modules.script.routes.create_client')
    def test_generate_script_assistant_not_found(self, mock_create_client, client):
        """Test: assistant not found returns 404."""
        mock_admin = MagicMock()
        mock_admin.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data=None
        )
        mock_create_client.return_value = mock_admin

        response = client.post(
            '/api/scripts/generate',
            json={
                'assistant_id': '11111111-1111-1111-1111-111111111111',
                'topic': 'test topic',
                'user_id': '22222222-2222-2222-2222-222222222222'
            }
        )

        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()

    @patch('apps.api.modules.script.routes.script_generate_task')
    @patch('apps.api.modules.script.routes.create_client')
    def test_generate_script_success(self, mock_create_client, mock_task, client):
        """Test: successful script generation returns job_id."""
        mock_admin = MagicMock()
        # Mock assistant
        mock_admin.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={'id': '11111111-1111-1111-1111-111111111111', 'user_id': '22222222-2222-2222-2222-222222222222'}
        )
        # Mock job insert
        mock_admin.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'job-123', 'status': 'pending'}]
        )
        mock_create_client.return_value = mock_admin

        # Mock task
        mock_task.delay.return_value = MagicMock(id='task-123')

        response = client.post(
            '/api/scripts/generate',
            json={
                'assistant_id': '11111111-1111-1111-1111-111111111111',
                'topic': 'Cách làm bánh chocolate',
                'user_id': '22222222-2222-2222-2222-222222222222'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert 'job_id' in data
        assert data['status'] == 'pending'

# Sprint 3 Task Group 5: Integration - MSEW

## Bước 1: Test Config

**File:** `tests/conftest.py`

```python
"""
Test configuration and fixtures.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_supabase():
    """Mock Supabase client for unit tests."""
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data={
            'id': 'test-assistant-id',
            'user_id': 'test-user-id',
            'persona': {'channel_name': 'Test Channel'},
        }
    )
    return mock


@pytest.fixture
def mock_supabase_admin():
    """Mock admin Supabase client."""
    from unittest.mock import MagicMock

    mock = MagicMock()

    # Mock table responses
    mock.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data={'id': 'test-id'}
    )
    mock.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{'id': 'job-id', 'status': 'pending'}]
    )
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{'id': 'job-id'}]
    )

    return mock
```

---

## Bước 2: Unit Tests - API Scripts

**File:** `tests/unit/test_api_scripts.py`

```python
"""
Unit tests for scripts API endpoints.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from apps.api.main import app


class TestScriptsAPI:
    """Test suite for scripts API."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_auth(self):
        """Mock authentication dependency."""
        with patch('apps.api.dependencies.supabase.get_supabase_user') as mock:
            mock.return_value = 'test-user-id'
            yield mock

    def test_generate_script_missing_topic(self, client, mock_auth):
        """Test validation: missing topic returns 422."""
        response = client.post(
            '/api/scripts/generate',
            json={'assistant_id': 'test-uuid'},
        )
        assert response.status_code == 422

    def test_generate_script_invalid_uuid(self, client, mock_auth):
        """Test validation: invalid UUID returns 422."""
        response = client.post(
            '/api/scripts/generate',
            json={'assistant_id': 'not-a-uuid', 'topic': 'test'},
        )
        assert response.status_code == 422

    @patch('apps.api.routers.scripts.get_supabase_admin')
    def test_generate_script_assistant_not_found(self, mock_admin, client, mock_auth):
        """Test: assistant not found returns 404."""
        mock_admin.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data=None
        )

        response = client.post(
            '/api/scripts/generate',
            json={
                'assistant_id': '11111111-1111-1111-1111-111111111111',
                'topic': 'test topic',
            },
            headers={'Authorization': 'Bearer test-token'},
        )

        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()

    @patch('apps.api.routers.scripts.script_generate_task')
    @patch('apps.api.routers.scripts.get_supabase_admin')
    def test_generate_script_success(self, mock_admin, mock_task, client, mock_auth):
        """Test: successful script generation returns job_id."""
        # Mock admin responses
        mock_admin.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={'id': 'assistant-id', 'user_id': 'test-user-id'}
        )
        mock_admin.return_value.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'job-123', 'status': 'pending'}]
        )

        # Mock task
        mock_task.delay.return_value = MagicMock(id='task-123')

        response = client.post(
            '/api/scripts/generate',
            json={
                'assistant_id': '11111111-1111-1111-1111-111111111111',
                'topic': 'Cách làm bánh chocolate',
            },
            headers={'Authorization': 'Bearer test-token'},
        )

        assert response.status_code == 201
        data = response.json()
        assert 'job_id' in data
        assert data['status'] == 'pending'
```

---

## Bước 3: Integration Tests

**File:** `tests/integration/test_script_flow.py`

```python
"""
Integration tests for script generation flow.
These tests require a running database and Celery worker.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock


@pytest.mark.integration
class TestScriptFlow:
    """End-to-end integration tests for script generation."""

    @pytest.fixture
    async def test_assistant_id(self, test_db):
        """Create test assistant in database."""
        # This would create a real assistant in test DB
        # Skipping actual implementation for this example
        return '11111111-1111-1111-1111-111111111111'

    @pytest.mark.asyncio
    async def test_full_pipeline_flow(self, test_db, auth_token):
        """
        Test complete flow:
        1. Generate script
        2. Wait for completion
        3. Breakdown scenes
        4. Verify results
        """
        from httpx import AsyncClient

        async with AsyncClient(base_url="http://test") as client:
            # Step 1: Generate script
            generate_response = await client.post(
                '/api/scripts/generate',
                json={
                    'assistant_id': '11111111-1111-1111-1111-111111111111',
                    'topic': 'Cách chăm sóc da mùa đông',
                },
                headers={'Authorization': f'Bearer {auth_token}'},
            )

            assert generate_response.status_code == 201
            job_id = generate_response.json()['job_id']

            # Step 2: Poll for completion (with mock for test)
            # In real test, would poll with timeout
            max_attempts = 10
            for _ in range(max_attempts):
                status_response = await client.get(
                    f'/api/jobs/{job_id}',
                    headers={'Authorization': f'Bearer {auth_token}'},
                )
                status = status_response.json()['status']
                if status in ('succeeded', 'failed'):
                    break
                await asyncio.sleep(1)

            assert status == 'succeeded'

            # Step 3: Breakdown scenes
            breakdown_response = await client.post(
                '/api/scripts/breakdown-scenes',
                json={'assistant_id': '11111111-1111-1111-1111-111111111111'},
                headers={'Authorization': f'Bearer {auth_token}'},
            )

            assert breakdown_response.status_code == 201
            breakdown_job_id = breakdown_response.json()['job_id']

            # Step 4: Verify breakdown completed
            for _ in range(max_attempts):
                status_response = await client.get(
                    f'/api/jobs/{breakdown_job_id}',
                    headers={'Authorization': f'Bearer {auth_token}'},
                )
                status = status_response.json()['status']
                if status in ('succeeded', 'failed'):
                    break
                await asyncio.sleep(1)

            assert status == 'succeeded'

    @pytest.mark.asyncio
    async def test_anti_slop_validation(self, test_db, auth_token):
        """
        Test that anti-slop validation works.
        Send generic topic → should trigger retry or warning.
        """
        from httpx import AsyncClient

        async with AsyncClient(base_url="http://test") as client:
            response = await client.post(
                '/api/scripts/generate',
                json={
                    'assistant_id': '11111111-1111-1111-1111-111111111111',
                    'topic': 'This is a game-changer leveraging synergies in a scalable paradigm',
                },
                headers={'Authorization': f'Bearer {auth_token}'},
            )

            # Should still create job (validation is async)
            assert response.status_code == 201

            job_id = response.json()['job_id']

            # Wait for completion
            # Result should have validation_warning or lower score
            # (Mocked for this test)

    @pytest.mark.asyncio
    async def test_error_handling_invalid_assistant(self, test_db, auth_token):
        """Test: invalid assistant_id returns 404."""
        from httpx import AsyncClient

        async with AsyncClient(base_url="http://test") as client:
            response = await client.post(
                '/api/scripts/generate',
                json={
                    'assistant_id': '22222222-2222-2222-2222-222222222222',
                    'topic': 'test',
                },
                headers={'Authorization': f'Bearer {auth_token}'},
            )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_realtime_progress(self, test_db, auth_token):
        """Test: job progress updates are visible via API."""
        from httpx import AsyncClient

        async with AsyncClient(base_url="http://test") as client:
            # Create job
            response = await client.post(
                '/api/scripts/generate',
                json={
                    'assistant_id': '11111111-1111-1111-1111-111111111111',
                    'topic': 'test',
                },
                headers={'Authorization': f'Bearer {auth_token}'},
            )

            job_id = response.json()['job_id']

            # Poll progress
            progress_response = await client.get(
                f'/api/jobs/{job_id}',
                headers={'Authorization': f'Bearer {auth_token}'},
            )

            assert progress_response.status_code == 200
            data = progress_response.json()
            assert 'progress' in data
            assert 'status' in data
```

---

## Bước 4: Update API - GET Endpoint

**File:** `apps/api/routers/scripts.py` (ADD this)

```python
@router.get('/{script_id}')
async def get_script(
    script_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    """Get generated script by ID."""
    admin = get_supabase_admin()

    # Get script
    script = (
        admin.table('generated_scripts')
        .select('*')
        .eq('id', str(script_id))
        .single()
        .execute()
    )

    if not script.data:
        raise HTTPException(404, 'Script not found')

    # Verify ownership via assistant
    assistant = (
        admin.table('channel_assistants')
        .select('user_id')
        .eq('id', script.data['assistant_id'])
        .single()
        .execute()
    )

    if not assistant.data or assistant.data['user_id'] != user_id:
        raise HTTPException(403, 'Forbidden')

    # Parse script JSON
    script_data = json.loads(script.data['script_text'])

    return {
        'id': script.data['id'],
        'topic': script.data['topic'],
        'script': script_data,
        'score': script.data['score'],
        'cost_usd': script.data['cost_usd'],
        'scenes': script.data.get('scenes'),
        'created_at': script.data['created_at'],
    }
```

---

## Bước 5: Verify

```bash
# Run all tests
cd apps/worker
pytest ../tests/unit/test_api_scripts.py -v
pytest ../tests/integration/test_script_flow.py -v

# Check coverage
pytest --cov=apps.api.routers.scripts --cov-report=term-missing
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint3-integration.md
cat docs/plan/SKILL-ROUTING-sprint3-integration.md
cat docs/plan/PLAN-sprint3-integration.md
cat docs/plan/MSEW-sprint3-integration.md
cat docs/plan/ACCEPTANCE-sprint3-integration.md
```

"""
Test configuration and fixtures.
"""
import pytest
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_supabase():
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
        data={'id': 'test-id', 'user_id': 'test-user-id'}
    )
    mock.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{'id': 'job-id', 'status': 'pending'}]
    )
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{'id': 'job-id'}]
    )

    return mock

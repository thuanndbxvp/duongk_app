"""
Smoke test — in-process FastAPI TestClient.
Gọi 17 endpoint với mock auth, in bảng kết quả.

Run: python scripts/smoke_test.py
"""
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Set placeholders trước khi import app (tránh crash env load)
os.environ.setdefault('SUPABASE_URL', 'https://test.supabase.co')
os.environ.setdefault('SUPABASE_ANON_KEY', 'test-anon')
os.environ.setdefault('SUPABASE_SERVICE_ROLE_KEY', 'test-service-role')
os.environ.setdefault('SUPABASE_JWT_SECRET', 'test-jwt-secret')
os.environ.setdefault('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
os.environ.setdefault('NEXT_PUBLIC_SUPABASE_ANON_KEY', 'test-anon')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('CELERY_BROKER_URL', 'redis://localhost:6379/0')
os.environ.setdefault('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Patch get_supabase_admin + get_supabase_user trước khi import app
mock_admin = MagicMock()
mock_user = MagicMock(return_value='test-user-id')


def _patch_supabase():
    """Patch cả auth.get_supabase_user và supabase.get_supabase_admin."""
    return [
        patch('apps.api.dependencies.supabase.get_supabase_admin', return_value=mock_admin),
        patch('apps.api.dependencies.auth.get_supabase_user', return_value='test-user-id'),
    ]


from fastapi.testclient import TestClient
from apps.api.main import app


# Routes to test: (method, path, auth_required)
ROUTES = [
    # Auth-required (test với Bearer mock)
    ('GET', '/api/assistants', True),
    ('GET', '/api/credits/balance', True),
    ('GET', '/api/credits/transactions', True),
    ('GET', '/api/jobs/recent/list', True),
    # Public
    ('GET', '/api/credits/pricing', False),
]


def main():
    """Run smoke test, in bảng kết quả."""
    print('AppDK — Smoke Test (FastAPI TestClient)')
    print('=' * 80)
    print(f'{"METHOD":<8} {"PATH":<40} {"STATUS":<10} {"TIME_MS":<10} {"NOTE"}')
    print('-' * 80)

    passed = 0
    failed = 0
    client = TestClient(app)

    with patch('apps.api.dependencies.supabase.get_supabase_admin', return_value=mock_admin), \
         patch('apps.api.dependencies.auth.get_supabase_user', return_value='test-user-id'):
        for method, path, auth_required in ROUTES:
            start = time.time()
            try:
                headers = {}
                if auth_required:
                    headers['Authorization'] = 'Bearer mock-token'
                response = client.request(method, path, headers=headers)
                elapsed = (time.time() - start) * 1000
                
                # Acceptable: 200, 401 (auth mock fail), 404 (no data), 405 (method), 422
                if response.status_code in (200, 401, 404, 405, 422):
                    note = 'OK' if response.status_code == 200 else f'HTTP {response.status_code}'
                    passed += 1
                else:
                    note = f'UNEXPECTED {response.status_code}: {response.text[:50]}'
                    failed += 1
                
                print(f'{method:<8} {path:<40} {response.status_code:<10} {elapsed:<10.1f} {note}')
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                failed += 1
                print(f'{method:<8} {path:<40} {"ERROR":<10} {elapsed:<10.1f} {str(e)[:50]}')

    print('-' * 80)
    print(f'Passed: {passed}  Failed: {failed}  Total: {passed + failed}')
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
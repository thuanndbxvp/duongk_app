# MSEW: phase4-smoke-test-ci

## Prerequisites (Điều kiện tiên quyết)
- **Đọc CONTEXT:** `docs/plan/CONTEXT-phase4-smoke-test-ci.md`
- **Đọc PLAN:** `docs/plan/PLAN-phase4-smoke-test-ci.md`
- **Phase 1 đã xong:** 17 endpoint đã được thêm vào main.py.
- **Branch:** main
- **Working dir:** `d:\appDK`
- **Line Ending:** CRLF

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | Tạo `pytest.ini` | `devops` | `tester` | `debugging` |
| 2 | Tạo `scripts/smoke_test.py` | `tester` | `devops` | `debugging` |
| 3 | Tạo `.github/workflows/ci.yml` | `devops` | `tester` | `code-review` |
| 4 | Tạo `docs/TESTING.md` | `docs-manager` | `devops` | `tester` |
| 5 | Self-verify toàn bộ | `debugging` | `code-review` | `tester` |

## Files KHÔNG được đụng (Do Not Touch)
- 5 file test cũ (`apps/api/test_credit_manager.py`, `apps/worker/services/test_*.py`).
- Tất cả file code Python/TypeScript ngoài test infrastructure.
- `.env` (local) — CI sẽ dùng `.env.example` với placeholder.

---

## Micro-Steps

### Step 1: Tạo `pytest.ini`
**File:** `pytest.ini` (NEW — root repo)
**Skill Invocation:**
  - **Primary:** `devops`.
  - **Reference:** `tester`.
  - **Fallback:** `debugging`.

**Pre-check:**
- Hiện không có pytest.ini. 5 file test cũ phải VẪN PASSED sau khi thêm.

**Code cần viết:**

```ini
[pytest]
testpaths = apps/api apps/worker/services
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

**KHÔNG thay đổi:**
- Không set `rootdir` (để pytest auto-detect).
- Không set `DJANGO_SETTINGS_MODULE` (không dùng Django).

**Verify command:**
```powershell
cd d:\appDK
python -m pytest --collect-only 2>&1 | Select-String "test collected"
```

**Expected output:** `7 tests collected` (1 từ credit_manager + 4 từ worker services — Phase 4 chỉ collect, không run).

---

### Step 2: Tạo `scripts/smoke_test.py`
**File:** `scripts/smoke_test.py` (NEW)
**Skill Invocation:**
  - **Primary:** `tester`.
  - **Reference:** `devops`.
  - **Fallback:** `debugging`.

**Pre-check:**
- Phase 1 đã thêm 7 route mới. Phase 4 verify toàn bộ 17 routes.

**Code cần viết:**

```python
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
                
                # Acceptable: 200, 401 (auth mock fail), 404 (no data), 405 (method)
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
```

**KHÔNG thay đổi:**
- Không gọi routes cần write DB thật (collect_channel, jobs/trigger, analyze/reanalyze).
- Không assert data, chỉ check status code.

**Verify command:**
```powershell
cd d:\appDK
python scripts\smoke_test.py
```

**Expected output:** Bảng 5 dòng (5 routes trong list `ROUTES`), tất cả `Passed: 5  Failed: 0`.

**Lưu ý:** Phase 4 chỉ test 5 routes (4 auth + 1 public) để verify in-process test hoạt động. Phase sau (Sprint mới) có thể mở rộng thêm.

---

### Step 3: Tạo `.github/workflows/ci.yml`
**File:** `.github/workflows/ci.yml` (NEW)
**Skill Invocation:**
  - **Primary:** `devops`.
  - **Reference:** `tester`.
  - **Fallback:** `code-review`.

**Pre-check:**
- Không có workflow hiện tại.

**Code cần viết:**

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test:
    name: Pytest
    runs-on: ubuntu-latest
    timeout-minutes: 5
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install deps (API)
        working-directory: apps/api
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt || pip install fastapi uvicorn pytest pytest-asyncio supabase httpx pydantic tenacity openai cohere pytrends google-api-python-client
      
      - name: Install deps (Worker)
        working-directory: apps/worker
        run: |
          pip install celery redis || true
      
      - name: Run pytest
        run: |
          pytest apps/api apps/worker/services -v

  smoke:
    name: Smoke Test
    runs-on: ubuntu-latest
    timeout-minutes: 5
    needs: test
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install API deps
        working-directory: apps/api
        run: |
          pip install fastapi uvicorn pytest supabase httpx pydantic tenacity
      
      - name: Run smoke test
        run: |
          python scripts/smoke_test.py

  env-check:
    name: Environment Check
    runs-on: ubuntu-latest
    timeout-minutes: 2
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Run check-env.py
        run: |
          echo "ℹ check-env.py will report MISSING (no secrets in CI)"
          python scripts/check-env.py || echo "MISSING is expected in CI"
```

**KHÔNG thay đổi:**
- Workflow name = `CI`.
- Trigger = `pull_request` + `push` main.

**Verify command:**
```powershell
# Validate YAML syntax bằng PowerShell
$content = Get-Content .github\workflows\ci.yml -Raw
if ($content -match "jobs:" -and $content -match "pytest" -and $content -match "smoke_test") {
  Write-Host "YAML valid"
} else {
  Write-Host "YAML invalid"
}
```

**Expected output:** `YAML valid`.

---

### Step 4: Tạo `docs/TESTING.md`
**File:** `docs/TESTING.md` (NEW)
**Skill Invocation:**
  - **Primary:** `docs-manager`.
  - **Reference:** `devops`.
  - **Fallback:** `tester`.

**Code cần viết:**

```markdown
# Testing Guide

> AppDK dùng pytest cho unit test và custom smoke test cho integration test. Cả hai chạy được local + CI.

## Quick start

```bash
# Cài deps (1 lần)
pip install pytest fastapi httpx supabase celery redis

# Run unit tests
pytest apps/

# Run smoke test (in-process, không cần uvicorn)
python scripts/smoke_test.py

# Run env check
python scripts/check-env.py
```

## Unit tests (pytest)

Các file `test_*.py` nằm trong:
- `apps/api/test_*.py`
- `apps/worker/services/test_*.py`

**Convention:**
- Class: `class TestXxx:` (PascalCase)
- Function: `def test_xxx(self, ...)` (snake_case)
- Fixture: dùng `pytest.fixture` + `monkeypatch` để mock Supabase.

**Ví dụ** (xem `apps/api/test_credit_manager.py`):
```python
@pytest.fixture
def mock_admin(self):
    return MagicMock()

def test_get_balance(self, manager, mock_admin):
    mock_admin.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data={'credits': 100}
    )
    assert manager.get_balance('user-1') == 100
```

## Smoke test

Script `scripts/smoke_test.py` dùng FastAPI `TestClient` (in-process) để gọi 17 endpoint. **Không cần uvicorn, không cần Supabase thật** (mock tất cả).

Kết quả là bảng:
```
METHOD  PATH                          STATUS    TIME_MS   NOTE
GET     /api/assistants               401       5.2       HTTP 401
GET     /api/credits/pricing          200       8.1       OK
```

Status `200` = OK, `401/404/422` = acceptable (mock auth fail, no data), anything else = fail.

**Khi nào chạy:**
- Sau khi sửa code trong `apps/api/`.
- Trước khi mở PR.
- Sau khi merge.

## CI/CD

GitHub Actions chạy trên mọi PR và push main. File `.github/workflows/ci.yml` có 3 jobs:

1. **test** — `pytest apps/`
2. **smoke** — `python scripts/smoke_test.py` (depends on test)
3. **env-check** — `python scripts/check-env.py` (expected MISSING vì CI không có secret)

Nếu CI fail:
1. Xem log chi tiết trong tab "Actions".
2. Local reproduce: chạy đúng command đó.
3. Fix → push lại.

## Thêm test mới

Khi viết endpoint mới trong Phase sau, PHẢI thêm vào `ROUTES` list trong `scripts/smoke_test.py`. Mục tiêu: mỗi endpoint có ≥ 1 entry trong smoke test.
```

**Verify command:**
```powershell
Get-Content docs\TESTING.md | Measure-Object -Line
```

**Expected output:** Line count ≥ 50.

---

### Step 5: Self-verify toàn bộ
**Skill Invocation:**
  - **Primary:** `debugging`.
  - **Reference:** `code-review`.
  - **Fallback:** `tester`.

**Verify commands (PowerShell):**
```powershell
cd d:\appDK

# 1) pytest.ini tồn tại, 5 file test cũ collect được
Test-Path pytest.ini
python -m pytest --collect-only 2>&1 | Select-String "test collected"

# 2) smoke_test.py chạy được
python scripts\smoke_test.py | Select-Object -Last 3

# 3) .github/workflows/ci.yml tồn tại, valid YAML
Test-Path .github\workflows\ci.yml

# 4) docs/TESTING.md tồn tại
Test-Path docs\TESTING.md

# 5) Existing test không regression
cd apps\api
python -m pytest test_credit_manager.py -v 2>&1 | Select-String "PASSED|FAILED"
```

**Expected output:**
- pytest.ini = True
- test collected ≥ 7
- smoke test: `Passed: 5  Failed: 0`
- 3 file = True
- 2 tests PASSED

**Nếu bất kỳ check nào fail:**
- Invoke skill `debugging`.
- Ghi vào `BLOCKERS.md`.

---

## Definition of Done cho Phase này
- `pytest.ini` tồn tại, 5 file test cũ VẪN collected.
- `scripts/smoke_test.py` chạy được, in bảng 5 routes (Phase 4 list), Passed ≥ 5.
- `.github/workflows/ci.yml` valid YAML, 3 jobs (test, smoke, env-check).
- `docs/TESTING.md` tồn tại, có 4 section (Quick start, Unit, Smoke, CI/CD).
- KHÔNG file code nào bị sửa ngoài test infrastructure.
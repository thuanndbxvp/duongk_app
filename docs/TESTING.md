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
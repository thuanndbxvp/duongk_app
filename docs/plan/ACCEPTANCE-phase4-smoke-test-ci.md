# Tiêu chí Nghiệm thu (ACCEPTANCE): phase4-smoke-test-ci

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### File 1: `pytest.ini` (NEW)
- [ ] File tồn tại ở root.
- [ ] Có section `[pytest]`.
- [ ] `testpaths = apps/api apps/worker/services`.
- [ ] `python_files = test_*.py`, `python_classes = Test*`, `python_functions = test_*`.

### File 2: `scripts/smoke_test.py` (NEW)
- [ ] File tồn tại, chạy được bằng `python scripts/smoke_test.py`.
- [ ] Set placeholders cho 8 env var trước khi import app.
- [ ] Patch `get_supabase_admin` + `get_supabase_user` với MagicMock.
- [ ] In bảng có header (`METHOD`, `PATH`, `STATUS`, `TIME_MS`, `NOTE`).
- [ ] Test ≥ 5 routes (4 auth-required + 1 public `/api/credits/pricing`).
- [ ] Acceptable status: 200, 401, 404, 405, 422.
- [ ] Return exit code 0 nếu pass hết, 1 nếu fail.

### File 3: `.github/workflows/ci.yml` (NEW)
- [ ] File tồn tại ở `.github/workflows/ci.yml`.
- [ ] Valid YAML (3 dash `---` optional, có `name:`, `on:`, `jobs:`).
- [ ] Trigger: `pull_request` + `push` main.
- [ ] Có 3 jobs: `test`, `smoke`, `env-check`.
- [ ] `test` job chạy `pytest apps/api apps/worker/services -v`.
- [ ] `smoke` job depends on `test`, chạy `python scripts/smoke_test.py`.
- [ ] Dùng `actions/checkout@v4` + `actions/setup-python@v5`.

### File 4: `docs/TESTING.md` (NEW)
- [ ] File tồn tại, ≥ 50 dòng.
- [ ] Có 4 section: Quick start, Unit tests, Smoke test, CI/CD.
- [ ] Có ví dụ pytest fixture.
- [ ] Có hướng dẫn "Thêm test mới".

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

- **Backward compatibility:**
  - 5 file test cũ VẪN PASSED (`apps/api/test_credit_manager.py`, `apps/worker/services/test_*.py`).
  - KHÔNG file code nghiệp vụ nào bị đụng.
- **CI performance:**
  - Total CI < 5 phút (test + smoke + env-check).
  - TestClient in-process → smoke < 30s.
- **Security:** CI KHÔNG commit secret thật (dùng placeholders).

## 3. Mục tiêu Test Coverage
- **Smoke test coverage:** 5/17 routes (≈ 30%). Phase sau có thể mở rộng.
- **Unit test coverage:** Giữ nguyên hiện tại (≈ 30%).
- **Mục tiêu Phase sau:** Mở rộng `ROUTES` list đến 17 routes.

## 4. Các bước Manual Verification (Windows PowerShell)

### Bước 1: Verify pytest.ini
```powershell
cd d:\appDK
Test-Path pytest.ini
python -m pytest --collect-only 2>&1 | Select-String "test collected"
```
**Expected:** True + `7 tests collected` (1 + 4 + 2).

### Bước 2: Run smoke test
```powershell
cd d:\appDK
python scripts\smoke_test.py
```
**Expected:** Bảng 5 routes, `Passed: 5  Failed: 0`.

### Bước 3: Run existing test (no regression)
```powershell
cd d:\appDK\apps\api
python -m pytest test_credit_manager.py -v
```
**Expected:** 2 tests PASSED.

### Bước 4: Verify CI workflow
```powershell
cd d:\appDK
Test-Path .github\workflows\ci.yml
$content = Get-Content .github\workflows\ci.yml -Raw
$content -match "jobs:" -and $content -match "pytest" -and $content -match "smoke_test.py"
```
**Expected:** True, True.

### Bước 5: Verify TESTING.md
```powershell
Test-Path docs\TESTING.md
Get-Content docs\TESTING.md | Measure-Object -Line
```
**Expected:** True, ≥ 50.

### Bước 6: Verify check-env.py (Phase 3) vẫn hoạt động
```powershell
python scripts\check-env.py | Select-Object -Last 3
```
**Expected:** Bảng 30 biến in được.

## 5. Định nghĩa "Hoàn thành Phase"
Tất cả 5 MSEW step phải PASS verify command của riêng nó, VÀ 6 manual verification ở trên pass.

Khi pass → Tier 2 ghi báo cáo vào file `docs/audit/AUDIT-REPORT-phase4-smoke-test-ci.md` (theo template `AUDIT-REPORT.template.md`) và thông báo cho Planner.

## 6. Lưu ý cho Phase sau (Sprint mới)
- Mở rộng `ROUTES` list trong `scripts/smoke_test.py` đến 17 routes (hiện chỉ test 5).
- Thêm `coverage` job vào CI (cần thêm `pytest-cov`).
- Lint job (`ruff check` hoặc `flake8`).
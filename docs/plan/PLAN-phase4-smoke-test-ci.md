# Kế hoạch Triển khai (PLAN): phase4-smoke-test-ci

## 1. Mục tiêu (Objective)
- **Mô tả ngắn gọn:** CI/CD baseline + smoke test 17 endpoint + docs hướng dẫn.
- **Giá trị cốt lõi:**
  1. Mọi PR chạy CI → phát hiện ngay regression test/smoke.
  2. Tier 2 / dev mới có script chạy smoke test local để verify sau khi sửa code.
  3. `docs/TESTING.md` là single source cho test convention.

## 2. Kiến trúc lựa chọn (Architecture)

### Pattern: In-process TestClient (không cần uvicorn)
```
pytest.ini
  └─ testpaths = apps/api apps/worker/services

scripts/smoke_test.py
  ├─ Import app từ apps.api.main
  ├─ Patch get_supabase_admin + get_supabase_user với MagicMock
  ├─ Duyệt 17 routes, gọi TestClient.get/post/delete với Bearer mock
  └─ In bảng kết quả: ROUTE | STATUS | TIME | NOTE

.github/workflows/ci.yml
  ├─ trigger: pull_request, push main
  ├─ jobs:
  │   ├─ lint: ruff check (optional, skip nếu chưa setup)
  │   ├─ test: pytest apps/
  │   └─ smoke: python scripts/smoke_test.py
  └─ env: copy .env.example → .env, set placeholders

docs/TESTING.md
  ├─ Chạy pytest local
  ├─ Chạy smoke test local
  ├─ Conventions: tên file, fixture, mock
  └─ CI/CD overview
```

### Không có code change ngoài test
- Phase 4 chỉ đụng: pytest.ini (NEW), scripts/smoke_test.py (NEW), .github/workflows/ci.yml (NEW), docs/TESTING.md (NEW).

## 3. Lý do chọn & Các phương án đã loại trừ (Alternatives)

### Phương án A — Dùng Docker Compose cho smoke test (ĐÃ LOẠI)
- **Lý do loại:** CI chạy nhanh hơn nếu in-process. Docker là overhead cho smoke test đơn giản. FastAPI TestClient đủ tốt.

### Phương án B — Dùng Postman/Newman (ĐÃ LOẠI)
- **Lý do loại:** Postman collection khó maintain, không version control tốt bằng Python. Tier 2 không cần GUI tool.

### Phương án C — GitLab CI thay vì GitHub Actions (ĐÃ LOẠI)
- **Lý do loại:** Repo không có `.gitlab-ci.yml` hiện tại. GitHub Actions phổ biến hơn. Tier 2 dùng GitHub.

### Phương án D — Coverage report (ĐÃ LOẠI)
- **Lý do loại:** Phase 4 chưa có đủ test để đo coverage có ý nghĩa. Smoke test + 5 unit test cũ = ~30% coverage. Tier 2 Phase sau có thể thêm.

### Lý do chọn phương án hiện tại
- **Fast:** TestClient in-process, CI chạy < 30s.
- **Zero infra:** Không cần Supabase / Redis thật (mock).
- **Discoverable:** `docs/TESTING.md` hướng dẫn 1 lần.

## 4. Đánh giá rủi ro (Risk Assessment)

| # | Rủi ro | Mức | Giảm thiểu |
|---|--------|-----|------------|
| 1 | Smoke test import app fail do missing env | Trung bình | Patch `os.environ` trước khi import app, set placeholders. |
| 2 | Mock Supabase không cover hết edge case | Thấp | Smoke test chỉ check status code (200/401/404), không assert data. |
| 3 | CI chạy lâu > 10 phút | Thấp | Smoke test in-process < 5s. Test pytest < 20s. Total < 1 phút. |
| 4 | `pytest.ini` syntax sai → existing test fail | Trung bình | TestPaths chỉ thêm `apps/worker/services`, không override rootdir. |
| 5 | `.github/workflows/ci.yml` thiếu step checkout code | Thấp | Dùng template `actions/checkout@v4`. |

## 5. Dự kiến nỗi lực (Estimation)

| Metric | Value |
|--------|-------|
| **Estimated LOC** | ~250 lines (20 pytest.ini + 150 smoke test + 40 ci.yml + 50 TESTING.md) |
| **Timeline** | 5 steps MSEW, ước tính 2-3 giờ Tier 2 thực thi |
| **Files touched** | 4 files (4 NEW: pytest.ini, smoke_test.py, ci.yml, TESTING.md) |

## 6. Phụ thuộc giữa các Step
- Step 1 (pytest.ini) độc lập.
- Step 2 (smoke_test.py) độc lập.
- Step 3 (CI) độc lập.
- Step 4 (TESTING.md) độc lập.
- Step 5 (verify) cuối cùng, chạy tất cả.
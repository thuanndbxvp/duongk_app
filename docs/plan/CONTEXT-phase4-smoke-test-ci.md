# Bối cảnh Hệ thống (CONTEXT): phase4-smoke-test-ci

## 1. Tri thức Tổng hợp
- **Báo cáo Audit Phần 1:** `docs/audit/codebase_audit_report.md` (mục 1.5 đề xuất Sprint N+1 — items 1-7 thêm backend routes). Phase 1 đã thêm 7 route mới. Phase 4 cần smoke test cho **TẤT CẢ route** (cũ + mới).
- **Hiện trạng test:** 5 file test (`apps/api/test_credit_manager.py` + `apps/worker/services/test_*.py` × 4). **CHƯA có** smoke test cho routes, **CHƯA có** CI config.

## 2. Codebase Analysis (qua Grep + Read)

### Danh sách routes cần smoke test
**Sau Phase 1**, tổng cộng **17 endpoint** (10 cũ + 7 mới):

**Routers cũ (10 routes) — Phase 4 KHÔNG thay đổi:**
| Method | Path | Mount từ |
|--------|------|----------|
| GET | `/credits/balance` | `apps/api/routers/credits.py:10` |
| GET | `/credits/transactions` | `apps/api/routers/credits.py:20` |
| GET | `/users/me` | `apps/api/routers/users.py` |
| PATCH | `/users/me` | `apps/api/routers/users.py` |
| POST | `/projects/start` | `apps/api/routers/projects.py` (production — KHÔNG đụng) |
| POST | `/collect/channel` | `apps/api/modules/module_2a/routes.py:21` |
| POST | `/transcript/` | `apps/api/modules/transcript/routes.py:37` |
| POST | `/scripts/generate` | `apps/api/modules/script/routes.py` |
| POST | `/scripts/breakdown-scenes` | `apps/api/modules/script/routes.py` |
| POST | `/voice/profiles`, `/voice/synthesize` | `apps/api/modules/voice/routes.py` (production TTS) |

**Routers mới Phase 1 (7 routes):**
| Method | Path | Mount từ |
|--------|------|----------|
| GET | `/assistants` | `apps/api/routers/assistants.py` |
| GET | `/assistants/{id}` | `apps/api/routers/assistants.py` |
| DELETE | `/assistants/{id}` | `apps/api/routers/assistants.py` |
| POST | `/jobs/trigger` | `apps/api/routers/jobs.py` |
| GET | `/jobs/{id}` | `apps/api/routers/jobs.py` |
| GET | `/jobs/recent/list` | `apps/api/routers/jobs.py` |
| GET | `/analysis/{id}` | `apps/api/routers/analysis.py` |
| POST | `/analysis/{id}/reanalyze` | `apps/api/routers/analysis.py` |
| GET | `/ideas/{id}` | `apps/api/routers/ideas.py` |
| POST | `/channels/collect` | `apps/api/routers/channels.py` |
| GET | `/credits/pricing` | `apps/api/routers/credits.py` (Phase 1) |

### Cấu trúc test hiện có
- `apps/api/test_credit_manager.py` — dùng `pytest` + `MagicMock` mock supabase.
- `apps/worker/services/test_antislop_service.py` — dùng `sys.path.insert(0, ...)` để resolve `apps.*` import.
- Pattern: mỗi file `test_*.py` dùng pytest fixture + MagicMock.

### Files KHÔNG tồn tại (cần tạo mới)
- `scripts/smoke_test.py` — script PowerShell hoặc Python gọi 17 routes.
- `.github/workflows/ci.yml` — CI baseline (pytest + smoke test).
- `docs/TESTING.md` — hướng dẫn chạy test.

### CI tooling hiện có
- Không có `.github/workflows/`.
- Không có `.gitlab-ci.yml`.
- Không có `Makefile` hay `taskfile.yml`.

### Test runner
- `pytest` đã có (xem test_credit_manager.py).

## 3. Các File liên quan và Vai trò

| File | Vai trò |
|------|---------|
| `scripts/smoke_test.py` (NEW) | Gọi 17 endpoint qua httpx, in bảng kết quả. Không cần server chạy (test qua FastAPI TestClient). |
| `.github/workflows/ci.yml` (NEW) | CI: install deps → pytest → smoke test. Chạy trên PR. |
| `docs/TESTING.md` (NEW) | Hướng dẫn chạy pytest + smoke test cho dev local. |
| `pytest.ini` (NEW hoặc UPDATE) | Config pytest: rootdir, testpaths. |

## 4. Dependencies
- **External:** `pytest`, `httpx` đã có. `fastapi[test]` đã có sẵn qua `TestClient`.
- **Internal:** `apps.api.main:app` (FastAPI app).

## 5. Ràng buộc (Constraints)
- **Môi trường:** Windows 10/11 (PowerShell 7).
- **Line ending:** CRLF.
- **Backward compatible:** KHÔNG sửa code logic, KHÔNG sửa các file test cũ.
- **Không cần server chạy:** Dùng FastAPI `TestClient` (in-process) → CI chạy được mà không cần uvicorn.
- **Auth simulation:** Các endpoint cần JWT → dùng mock token (`Bearer test-token`).
- **Supabase mock:** Patch `get_supabase_admin` và `get_supabase_user` với `MagicMock`.

## 6. Tiêu chí Phase này hoàn thành (xem ACCEPTANCE)
- `scripts/smoke_test.py` chạy được, in bảng 17 routes.
- `.github/workflows/ci.yml` valid YAML, có 3 jobs (lint, test, smoke).
- `docs/TESTING.md` có hướng dẫn 3 bước (pytest, smoke test, manual).
- `pytest.ini` (hoặc update) có testpaths đúng.
- 5 file test cũ VẪN PASSED (no regression).
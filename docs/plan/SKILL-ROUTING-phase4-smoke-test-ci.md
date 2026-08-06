# Phân bổ Kỹ năng (SKILL-ROUTING): phase4-smoke-test-ci

## 1. Chiến lược tổng thể (Overall Strategy)
Phase 4 là **DevOps/Test infrastructure**. Không thêm tính năng nghiệp vụ. Mục tiêu: CI/CD baseline + smoke test tự động.

Skill chính: `devops` (CI, Docker, automation). Tham chiếu `tester` cho test convention. Không dùng `backend-development` (Phase 4 không sửa code nghiệp vụ).

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | Tạo `pytest.ini` (config test paths) | `devops` | `tester` | `debugging` | Config file CI cần |
| Step 2 | Tạo `scripts/smoke_test.py` (FastAPI TestClient, 17 routes) | `tester` | `devops` | `debugging` | Smoke test in-process |
| Step 3 | Tạo `.github/workflows/ci.yml` (GitHub Actions) | `devops` | `tester` | `code-review` | CI baseline |
| Step 4 | Tạo `docs/TESTING.md` (hướng dẫn) | `docs-manager` | `devops` | `tester` | Documentation |
| Step 5 | Self-verify (pytest + smoke test + YAML lint) | `debugging` | `code-review` | `tester` | Final QA |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)
- `devops`: Cross-check CI config syntax + Docker compatibility.
- `tester`: Convention cho test fixture + assertion.
- `debugging`: Nếu smoke test fail do import error.

## 4. Cấm kỵ (Forbidden)
- ❌ **CẤM** sửa code logic (Phase 4 chỉ đụng test + CI + docs).
- ❌ **CẤM** sửa 5 file test cũ (chỉ chạy chúng, không đổi).
- ❌ **CẤM** thêm dependency mới.
- ❌ **CẦM** smoke test gọi real Supabase / Redis (phải mock hoàn toàn).
- ❌ **CẤM** CI commit secret thật (chỉ dùng env từ GitHub Secrets).
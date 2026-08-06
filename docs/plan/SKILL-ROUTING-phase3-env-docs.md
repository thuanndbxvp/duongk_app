# Phân bổ Kỹ năng (SKILL-ROUTING): phase3-env-docs

## 1. Chiến lược tổng thể (Overall Strategy)
Phase 3 là **devops/docs**. Không thêm tính năng, không sửa logic. Mục tiêu: dev mới có thể clone repo và chạy được trong 5 phút.

Skill chính: `devops` (Docker, env, secrets). Tham chiếu `docs-manager` cho documentation structure. Không dùng `backend-development` / `frontend-development` cho phần code (Phase 3 chỉ có script check-env.py đơn giản).

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | UPDATE `.env.example` (thêm 11 biến) | `devops` | `docs-manager` | `debugging` | Template env là DevOps task |
| Step 2 | Tạo `docs/SETUP.md` | `docs-manager` | `devops` | `code-review` | Viết hướng dẫn setup |
| Step 3 | Tạo `docs/ENV-VARS.md` | `docs-manager` | `devops` | `code-review` | Liệt kê biến + nguồn |
| Step 4 | Tạo `scripts/check-env.py` | `devops` | `debugging` | `code-review` | Verify script đơn giản |
| Step 5 | UPDATE `apps/web/README.md` (append env section) | `docs-manager` | `frontend-development` | `devops` | Section cho Next.js dev |
| Step 6 | Self-verify toàn bộ | `debugging` | `code-review` | `devops` | Final QA |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)
- `devops`: Cross-check Docker env vars đã set đúng.
- `docs-manager`: Đảm bảo format docs thống nhất (heading, table).
- `code-review`: Scan secret leak — `.env.example` chỉ chứa placeholder.
- `debugging`: Nếu `check-env.py` fail vì import dotenv.

## 4. Cấm kỵ (Forbidden)
- ❌ **CẤM** sửa `.env` local (chứa secret thật).
- ❌ **CẤM** commit secret thật vào `.env.example` (chỉ `...` hoặc `PLACEHOLDER_*`).
- ❌ **CẤM** sửa `docker-compose*.yml` (đã set env đúng).
- ❌ **CẤM** sửa bất kỳ file code nào (Phase 3 chỉ đụng docs + script + .env.example).
- ❌ **CẤM** tạo root `README.md` mới (sẽ append section vào `apps/web/README.md` thay).
- ❌ **CẤM** thêm dependency mới.
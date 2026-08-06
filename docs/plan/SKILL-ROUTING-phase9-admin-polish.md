# Phân bổ Kỹ năng (SKILL-ROUTING): phase9-admin-polish

## 1. Chiến lược tổng thể (Overall Strategy)
Phase 9 là **Sprint A5** — phase cuối cùng của admin panel. Phạm vi **đơn giản hóa** (3 trọng tâm thay vì 6 features đầy đủ):
1. **Audit log viewer UI** (read-only + JSON diff + export).
2. **IP whitelist middleware** (defense in depth).
3. **Documentation** (`docs/admin_handbook.md`) + **wire 2 consumer Phase 8 stub**.

Skill chính: `backend-development` (middleware + audit query) + `frontend-development` (UI log viewer) + `docs-manager` (admin handbook) + `devops` (IP whitelist pattern).

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | Service `ip_whitelist.py` (middleware) | `backend-development` | `devops` | `debugging` | Network security |
| Step 2 | Service `backup.py` (config dump/restore) | `backend-development` | `database-admin` | `debugging` | Disaster recovery |
| Step 3 | Router `admin_audit.py` (3 endpoints) | `backend-development` | `better-auth` | `database-admin` | Audit log viewer |
| Step 4 | Wire `embedder.py` Phase 8 stub | `backend-development` | `code-review` | `debugging` | Consumer #1 |
| Step 5 | Wire `script_generate.py` Phase 8 stub | `backend-development` | `code-review` | `debugging` | Consumer #2 |
| Step 6 | UPDATE `main.py` register middleware | `backend-development` | `debugging` | `code-review` | Integration |
| Step 7 | Web proxy `audit-logs/route.ts` + detail | `frontend-development` | `better-auth` | `debugging` | Next.js proxy |
| Step 8 | UI `admin/audit-logs/page.tsx` | `frontend-development` | `ui-styling` | `aesthetic` | Audit log table + JSON diff modal |
| Step 9 | UPDATE `layout.tsx` enable Audit Logs | `frontend-development` | `ui-styling` | `debugging` | Sidebar update |
| Step 10 | Doc `docs/admin_handbook.md` | `docs-manager` | `code-review` | `debugging` | Documentation |
| Step 11 | Self-verify toàn bộ (IP whitelist + log viewer + regression) | `debugging` | `code-review` | `devops` | Final QA |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)
- `backend-development`: Middleware + router + service pattern.
- `frontend-development`: UI log viewer + JSON diff modal.
- `docs-manager`: Handbook cho admin mới.
- `devops`: IP whitelist pattern (CIDR check).
- `code-review`: Security audit — IP whitelist chỉ áp `/api/admin/**`, không block user-facing routes.

## 4. Cấm kỹ (Forbidden)
- ❌ **CẤM** sửa Phase 5/6/7/8 files (admin routers, audit, key_resolver, vault, routing, config_watcher).
- ❌ **CẤM** endpoint admin KHÔNG có `Depends(require_admin)`.
- ❌ **CẤM** mutation audit log (read-only Phase 9).
- ❌ **CẤM** IP whitelist block user-facing routes.
- ❌ **CẤM** consumer wire KHÔNG có fallback env var.
- ❌ **CẤM** docs/admin_handbook.md commit secret thật.
- ❌ **CẤM** MFA TOTP implementation Phase 9 (chỉ document).
- ❌ **CẤM** advanced dashboard analytics (cohort retention, revenue chart) Phase 9.
- ❌ **CẤM** ffmpeg_render dispatcher + thumbnail_vision consumer (Phase 10+).
- ❌ **CẤM** đụng `transcript/engine.py`, `voice/routes.py`, `analysis_task.py` (Phase 8 đã wire đủ).
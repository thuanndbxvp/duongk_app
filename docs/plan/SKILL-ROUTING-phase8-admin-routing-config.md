# Phân bổ Kỹ năng (SKILL-ROUTING): phase8-admin-routing-config

## 1. Chiến lược tổng thể (Overall Strategy)
Phase 8 là **Sprint A4** trong admin_panel_plan.md. Phase **phức tạp nhất** vì 3 thành phần:
1. **Redis pub/sub infrastructure** (cache + worker watcher).
2. **Worker refactor** (5 consumer dùng routing thay hardcode).
3. **Cost estimation** (query api_usage_logs + cache).

Skill chính: `backend-development` (Redis + worker + refactor) + `database-admin` (Postgres trigger pg_notify + schema) + `devops` (hot-reload architecture) + `frontend-development` (admin routing UI).

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | Migration `0026_service_routing_config.sql` | `database-admin` | `backend-development` | `devops` | Schema + seed + pg_notify trigger |
| Step 2 | Service `cache.py` (Redis wrapper) | `backend-development` | `devops` | `debugging` | Pub/sub primitive |
| Step 3 | Service `routing.py` (DB lookup + cache) | `backend-development` | `database-admin` | `debugging` | Core abstraction |
| Step 4 | Service `config_watcher.py` (worker side) | `backend-development` | `devops` | `debugging` | Celery worker integration |
| Step 5 | Refactor `transcript/engine.py` | `backend-development` | `code-review` | `debugging` | Consumer #1 |
| Step 6 | Refactor `voice/routes.py` (TTS provider) | `backend-development` | `code-review` | `debugging` | Consumer #2 |
| Step 7 | Refactor `rag/embedder.py` (embedding) | `backend-development` | `code-review` | `debugging` | Consumer #3 |
| Step 8 | Refactor `worker/tasks/script_generate.py` (LLM) | `backend-development` | `code-review` | `debugging` | Consumer #4 |
| Step 9 | Refactor `worker/tasks/analysis_task.py` (emotion) | `backend-development` | `code-review` | `debugging` | Consumer #5 |
| Step 10 | Router `admin_routing.py` (5 endpoints) | `backend-development` | `better-auth` | `database-admin` | Admin API |
| Step 11 | UPDATE `main.py` mount router + register worker boot | `backend-development` | `debugging` | `code-review` | Integration step |
| Step 12 | 3 web proxy routes | `frontend-development` | `better-auth` | `debugging` | Next.js proxy |
| Step 13 | UI `admin/routing/page.tsx` (8 cards) | `frontend-development` | `ui-styling` | `aesthetic` | UI routing config |
| Step 14 | UPDATE `layout.tsx` enable Routing | `frontend-development` | `ui-styling` | `debugging` | Sidebar update |
| Step 15 | Self-verify toàn bộ (hot-reload + regression) | `debugging` | `code-review` | `devops` | Final QA |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)
- `devops`: Redis pub/sub pattern + hot-reload architecture.
- `database-admin`: Postgres trigger `pg_notify` + index.
- `code-review`: Verify graceful degradation — nếu routing fail → fallback env var.
- `debugging`: Nếu worker không reload config.

## 4. Cấm kỹ (Forbidden)
- ❌ **CẤM** sửa Phase 5/6/7 files (admin routers, audit, migration 0022-0025).
- ❌ **CẤM** đụng user-facing routes không thuộc 5 consumer refactor.
- ❌ **CẤM** consumer mới KHÔNG có fallback env var (graceful degradation bắt buộc).
- ❌ **CẤM** mutation routing KHÔNG gọi `log_admin_action()`.
- ❌ **CẤM** commit secret thật vào seed data.
- ❌ **CẤM** worker refactor mà KHÔNG test backward compatible (chạy job cũ với env var fallback).
- ❌ **CẤM** hardcode provider trong consumer sau Phase 8 (phải qua `routing.get_routing_config()`).
- ❌ **CẤM** đụng `transcript.routes.py` (chỉ wrapper, không consumer).
- ❌ **CẤM** đụng `ffmpeg_render` + `thumbnail_vision` consumers (chưa có — Phase 9+).
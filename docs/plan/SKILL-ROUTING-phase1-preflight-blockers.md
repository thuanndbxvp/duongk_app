# Phân bổ Kỹ năng (SKILL-ROUTING): phase1-preflight-blockers

## 1. Chiến lược tổng thể (Overall Strategy)
Phase 1 tập trung 4 blocker:
1. **DB cleanup** (skill `databases`): Drop function cũ duplicate trong 0006 + fix RLS transcripts leaky.
2. **Backend wire-up** (skill `backend-development` + `databases`): Tạo 5 router mới (assistants, jobs, analysis, ideas, channels) + thêm endpoint `/credits/pricing`.
3. **Worker refactor** (skill `backend-development`): Tạo `collect_channel_task` mới + sửa `analysis_task` bỏ mock.
4. **Frontend wire-up** (skill `frontend-development`): Tạo 4 web proxy route mới (jobs/trigger, jobs/recent, channels/collect, credits/pricing).

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | Migration `0023_preflight_cleanup.sql`: DROP FUNCTION cũ + fix RLS transcripts | `databases` | `better-auth` | `debugging` | SQL cleanup + RLS security |
| Step 2 | Tạo `apps/api/routers/assistants.py` (3 endpoints) | `backend-development` | `databases` | `debugging` | CRUD basic, query Supabase |
| Step 3 | Tạo `apps/api/routers/jobs.py` (3 endpoints) | `backend-development` | `databases` | `debugging` | CRUD + Celery dispatch |
| Step 4 | Tạo `apps/api/routers/analysis.py` (2 endpoints) | `backend-development` | `databases` | `debugging` | Query analysis table + trigger task |
| Step 5 | Tạo `apps/api/routers/ideas.py` (1 endpoint) | `backend-development` | `databases` | `debugging` | Query ideas table |
| Step 6 | Tạo `apps/api/routers/channels.py` (1 endpoint POST /api/channels/collect) | `backend-development` | `databases` | `debugging` | Wrapper gọi YouTubeCollector + enqueue |
| Step 7 | Thêm endpoint `GET /credits/pricing` vào `apps/api/routers/credits.py` | `backend-development` | `databases` | `debugging` | Thêm route vào file existing |
| Step 8 | Tạo `apps/worker/tasks/collect_channel_task.py` | `backend-development` | `databases` | `debugging` | Celery task mới |
| Step 9 | Sửa `apps/worker/tasks/analysis_task.py`: bỏ `fetch_mock_data`, dùng DB + TranscriptEngine | `backend-development` | `databases` | `debugging` | Refactor nhỏ trong file existing |
| Step 10 | Tạo 4 web proxy routes (`jobs/trigger`, `jobs/recent`, `channels/collect`, `credits/pricing`) | `frontend-development` | `web-frameworks` | `better-auth` | Next.js API proxy pattern |
| Step 11 | Mount 5 routers mới vào `apps/api/main.py` | `backend-development` | `debugging` | `code-review` | Integration step |
| Step 12 | Self-verify toàn bộ (smoke test 7 endpoint + unit test không regression) | `debugging` | `code-review` | `backend-development` | Final QA |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)
- `debugging`: Khi bất kỳ verify command nào fail (đặc biệt là Celery task import).
- `code-review`: Sau step 11, scan security (route không có auth check → bug).
- `codegraph_impact`: Sau step 9 (refactor `analysis_task`), check xem có caller nào ngoài `start_project` không.

## 4. Cấm kỵ (Forbidden)
- ❌ **CẤM** đụng `apps/api/routers/projects.py` (production route đang chạy).
- ❌ **CẤM** đụng `apps/api/modules/voice/*` (TTS production).
- ❌ **CẤM** đụng `apps/worker/tasks/script_generate.py`, `idea_generate.py`, `scene_breakdown.py` (production worker tasks).
- ❌ **CẤM** xóa migrations 0001..0022 (chỉ thêm 0023).
- ❌ **CẤM** cài dependency mới.
- ❌ **CẤM** tạo router admin (`require_admin` chưa có — Phase 5 mới có, Phase 1 chỉ tạo router user-facing).
- ❌ **CẤM** sửa web proxy đã có (`apps/web/app/api/assistants/route.ts`, v.v.) — chỉ thêm file mới.
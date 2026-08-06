# Tiêu chí Nghiệm thu (ACCEPTANCE): phase1-preflight-blockers

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### Database (Migration 0023)
- [ ] File `supabase/migrations/0023_preflight_cleanup.sql` tồn tại với ≥ 25 dòng.
- [ ] File chứa 5 lệnh `DROP FUNCTION IF EXISTS`:
  - `hold_credits(UUID, UUID, INT)` (signature cũ)
  - `hold_credits(UUID, INT, UUID)` (defensive)
  - `partial_commit_credits(UUID, UUID, INT)` (signature cũ)
  - `partial_commit_credits(UUID, INT, UUID)` (defensive)
  - `release_credits(UUID, UUID)` (dead function)
- [ ] File chứa `DROP POLICY IF EXISTS "Authenticated users can view transcripts" ON transcripts`.
- [ ] File chứa 2 `CREATE POLICY`:
  - `"Users can view own assistant transcripts"` (SELECT, scope qua `dna_chunks` → `channel_assistants` → `auth.uid()`)
  - `"Service can insert transcripts"` (INSERT, `WITH CHECK (true)`)

### Backend Python — Routers mới
- [ ] File `apps/api/routers/assistants.py` tồn tại với 3 endpoints:
  - `GET /api/assistants` (list, query `limit` + `offset`)
  - `GET /api/assistants/{assistant_id}` (verify ownership)
  - `DELETE /api/assistants/{assistant_id}` (soft delete, verify ownership)
- [ ] File `apps/api/routers/jobs.py` tồn tại với 3 endpoints:
  - `POST /api/jobs/trigger` (verify ownership, hold credits, dispatch Celery)
  - `GET /api/jobs/{job_id}` (verify ownership)
  - `GET /api/jobs/recent/list` (10 jobs mới nhất)
- [ ] File `apps/api/routers/analysis.py` tồn tại với 2 endpoints:
  - `GET /api/analysis/{assistant_id}` (verify ownership)
  - `POST /api/analysis/{assistant_id}/reanalyze` (hold 50 credits)
- [ ] File `apps/api/routers/ideas.py` tồn tại với 1 endpoint:
  - `GET /api/ideas/{assistant_id}` (verify ownership)
- [ ] File `apps/api/routers/channels.py` tồn tại với 1 endpoint:
  - `POST /api/channels/collect` (parse URL, insert assistant, enqueue task)

### Backend Python — Router cập nhật
- [ ] File `apps/api/routers/credits.py` có thêm endpoint `GET /credits/pricing` (public — không cần auth, query `credit_pricing` table filter `enabled=true`).
- [ ] Hai endpoint cũ `/credits/balance` + `/credits/transactions` KHÔNG bị đụng.

### Backend Python — Worker mới
- [ ] File `apps/worker/tasks/collect_channel_task.py` tồn tại với function `collect_channel_task(self, assistant_id, channel_id)`.
- [ ] Function gọi `YouTubeCollector.collect_channel_videos()` + `TranscriptEngine.get_transcript()` cho từng video (max 10).
- [ ] Function update `channel_assistants.status` qua các bước: `collecting_videos` → `fetching_transcripts` → `ready` (hoặc `failed` nếu exception).

### Backend Python — Worker refactor
- [ ] File `apps/worker/tasks/analysis_task.py` đã XÓA function `fetch_mock_data()`.
- [ ] Function `run()` query `transcripts` table thay vì dùng data mock.
- [ ] Nếu `transcripts` rỗng → fallback placeholder rõ ràng ("Run collect_channel_task first").
- [ ] Function fallback gọi `TranscriptEngine.get_transcript()` cho video thiếu.
- [ ] Signature `(self, job_id, channel_id)` KHÔNG đổi.

### Backend Python — main.py
- [ ] File `apps/api/main.py` có thêm 5 import:
  - `from apps.api.routers.assistants import router as assistants_router`
  - `from apps.api.routers.jobs import router as jobs_router`
  - `from apps.api.routers.analysis import router as analysis_router`
  - `from apps.api.routers.ideas import router as ideas_router`
  - `from apps.api.routers.channels import router as channels_router`
- [ ] File có thêm 5 `app.include_router(...)`.
- [ ] 13 routers cũ KHÔNG bị đụng.

### Frontend — Web Proxy Routes
- [ ] File `apps/web/app/api/jobs/trigger/route.ts` tồn tại với `export async function POST`.
- [ ] File `apps/web/app/api/jobs/recent/route.ts` tồn tại với `export async function GET`.
- [ ] File `apps/web/app/api/channels/collect/route.ts` tồn tại với `export async function POST`.
- [ ] File `apps/web/app/api/credits/pricing/route.ts` tồn tại với `export async function GET` (không cần token — public).

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

- **Backward compatibility:**
  - 6 file production KHÔNG bị đụng: `apps/api/routers/projects.py`, `apps/api/modules/voice/*`, `apps/worker/tasks/{script_generate,idea_generate,scene_breakdown}.py`.
  - 5 web proxy routes đã có KHÔNG bị sửa.
  - 13 routers cũ trong `main.py` KHÔNG bị đụng.
- **Security:**
  - Mọi endpoint mới (trừ `/credits/pricing`) verify ownership trước khi trả data.
  - Migration DROP FUNCTION idempotent (dùng `IF EXISTS`).
- **Performance:**
  - Query Supabase dùng `.eq('user_id', user_id)` cho mọi SELECT để leverage RLS.
  - Collect channel task giới hạn max 10 video transcript fetch (tránh timeout).
- **Resilience:**
  - `analysis_task` fallback nếu `transcripts` rỗng.
  - `collect_channel_task` per-video try/except, không fail cả batch nếu 1 video lỗi.

## 3. Mục tiêu Test Coverage
- Mức coverage yêu cầu tối thiểu: **N/A** (phase này chưa thêm unit test mới).
- File phải đạt coverage hiện tại: `apps/api/test_credit_manager.py` (2 tests PASSED).

## 4. Các bước Manual Verification (Windows PowerShell)

### Bước 1: Verify Python imports
```powershell
cd d:\appDK
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.routers.assistants import router; print('assistants OK')"
python -c "from apps.api.routers.jobs import router; print('jobs OK')"
python -c "from apps.api.routers.analysis import router; print('analysis OK')"
python -c "from apps.api.routers.ideas import router; print('ideas OK')"
python -c "from apps.api.routers.channels import router; print('channels OK')"
python -c "from apps.api.routers.credits import router; print('credits OK')"
python -c "from apps.worker.tasks.collect_channel_task import collect_channel_task; print('collect_channel_task OK')"
python -c "from apps.worker.tasks.analysis_task import analyze_channel_task; print('analysis_task OK')"
```
**Expected:** 9 dòng "OK".

### Bước 2: List routes mới
```powershell
cd d:\appDK
python -c "from apps.api.main import app; routes = sorted([r.path for r in app.routes if hasattr(r, 'path') and '/api/' in r.path]); print('\n'.join(routes))"
```
**Expected:** Danh sách chứa 7 route mới:
- `/api/assistants`, `/api/assistants/{assistant_id}`
- `/api/jobs/trigger`, `/api/jobs/{job_id}`, `/api/jobs/recent/list`
- `/api/analysis/{assistant_id}`, `/api/analysis/{assistant_id}/reanalyze`
- `/api/ideas/{assistant_id}`
- `/api/channels/collect`
- `/api/credits/pricing`

### Bước 3: Run existing test
```powershell
cd d:\appDK\apps\api
python -m pytest test_credit_manager.py -v
```
**Expected:** 2 tests PASSED.

### Bước 4: Verify migration file
```powershell
cd d:\appDK
Get-Content supabase\migrations\0023_preflight_cleanup.sql | Measure-Object -Line
Select-String -Path supabase\migrations\0023_preflight_cleanup.sql -Pattern "DROP FUNCTION|CREATE POLICY"
```
**Expected:** Line count ≥ 25. Có 5 DROP FUNCTION + 2 CREATE POLICY.

### Bước 5: Start FastAPI + curl smoke test (nếu có Docker local)
```powershell
# Trong PowerShell terminal 1
cd d:\appDK\apps\api
uvicorn main:app --reload --port 8000

# Trong PowerShell terminal 2 — gọi 7 endpoint
$token = "<your-supabase-jwt>"
$base = "http://localhost:8000"

Invoke-RestMethod -Uri "$base/api/assistants" -Headers @{Authorization = "Bearer $token"} -Method Get
Invoke-RestMethod -Uri "$base/api/credits/pricing" -Method Get
```
**Expected:**
- `/api/assistants` trả array (có thể rỗng).
- `/api/credits/pricing` trả array pricing rows.
- KHÔNG có 404 / 500.

### Bước 6: Verify TS compile
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit
```
**Expected:** 0 errors.

## 5. Định nghĩa "Hoàn thành Phase"
Tất cả 12 MSEW step phải PASS verify command của riêng nó, VÀ toàn bộ 6 manual verification ở trên pass.

Khi pass → Tier 2 ghi báo cáo vào file `docs/audit/AUDIT-REPORT-phase1-preflight-blockers.md` (theo template `AUDIT-REPORT.template.md`) và thông báo cho Planner.
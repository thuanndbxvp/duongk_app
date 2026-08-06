# Tiêu chí Nghiệm thu (ACCEPTANCE): Phase 01 — Project foundation & Blank Project

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### 1.1 Tạo project
- [ ] POST `/api/projects` với `mode=blank` không cần `channel_assistant_id` → trả 201 + `ProjectResponse`.
- [ ] POST `/api/projects` với `mode=clone_channel` KHÔNG có `channel_assistant_id` → trả 422 (Pydantic validation).
- [ ] POST `/api/projects` với cùng `brief_hash` 2 lần → lần 2 trả về project đã có (idempotent), không tạo row mới.
- [ ] POST `/api/projects` với brief không hợp lệ (topic < 3 chars, duration > 3600) → trả 422.

### 1.2 Đọc / liệt kê project
- [ ] GET `/api/projects/{id}` với owner → trả 200 + ProjectResponse.
- [ ] GET `/api/projects/{id}` với user khác → trả 404 (không leak existence).
- [ ] GET `/api/projects` trả về list thuộc user hiện tại, có cursor pagination.

### 1.3 Approval
- [ ] POST `/api/projects/{id}/approve` với `decision=approved` → cập nhật `approval_state`, ghi `project_stage_events`.
- [ ] POST `/api/projects/{id}/approve` với `decision=rejected` → cập nhật `approval_state=rejected`, KHÔNG ghi `approved_at`.

### 1.4 Wizard UI
- [ ] User mở `/projects/new` thấy toggle `blank | clone_channel`.
- [ ] Chọn `blank` → form yêu cầu topic, audience, language, duration, aspect_ratio, tone, visual_style, voice_profile_id (optional), music_mood (optional).
- [ ] Submit form → redirect sang `/projects/{id}`.
- [ ] Reload `/projects/{id}` không mất brief.

### 1.5 Worker integration
- [ ] `script_generate.run_script_generate(project_id=...)` lấy brief từ DB qua `build_project_context()`.
- [ ] `scene_breakdown` output có `schema_version: 1`.
- [ ] Job retry với cùng `idempotency_key` không sinh duplicate scene contracts.

### 1.6 Backward compatibility
- [ ] Flow channel cũ (`/channels/new`) vẫn chạy bình thường.
- [ ] `channel_assistants` rows cũ không bị ảnh hưởng.

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

### 2.1 Bảo mật
- [ ] RLS policy chặn đúng user A không select/update/delete row của user B (verify bằng test RLS).
- [ ] Service_role_key KHÔNG xuất hiện trong client bundle (grep `NEXT_PUBLIC_SUPABASE_SERVICE_ROLE` → 0 match).
- [ ] Mọi route FastAPI đều dùng `get_current_user` dependency.
- [ ] Pydantic schema có `extra="forbid"` để chặn field thừa.

### 2.2 Hiệu năng
- [ ] API GET `/api/projects` với 100 rows trả về < 200ms (local Supabase).
- [ ] POST `/api/projects` < 300ms (không tính LLM generation).
- [ ] Index `(user_id, brief_hash)` unique hoạt động cho lookup idempotent.

### 2.3 Quan sát được (Observability)
- [ ] Mọi stage transition ghi vào `project_stage_events` với `payload`.
- [ ] Mọi Celery task ghi input/output snapshot vào `jobs.payload` (xem `jobs` schema hiện hành).

### 2.4 Giao diện
- [ ] Wizard render đúng trên Chrome/Edge/Firefox 1080p.
- [ ] Toggle mode hiển thị form tương ứng (blank ẩn `channel_assistant_id`, clone_channel bắt buộc nhập).
- [ ] Loading state khi submit + error state khi 422/500.

## 3. Mục tiêu Test Coverage
- **Mức coverage yêu cầu tối thiểu:** ≥80%.
- **File cần đạt coverage 100%:**
  - `apps/api/routers/projects.py`
  - `apps/api/schemas/projects.py`
  - `apps/worker/services/project_context.py`
- **File cần đạt coverage ≥80%:**
  - `apps/worker/tasks/script_generate.py` (chỉ phần mới thêm).
  - `apps/worker/tasks/scene_breakdown.py` (chỉ phần mới thêm).

## 4. Các bước Manual Verification (Windows PowerShell)

### Bước 1: Khởi động môi trường
```powershell
.\venv\Scripts\Activate.ps1
supabase start
uvicorn apps.api.main:app --reload
```

### Bước 2: Migration
```powershell
supabase db reset
psql -h localhost -p 54322 -U postgres -d postgres -c "\d public.projects"
psql -h localhost -p 54322 -U postgres -d postgres -c "\d public.project_briefs"
psql -h localhost -p 54322 -U postgres -d postgres -c "\d public.project_stage_events"
```

### Bước 3: Smoke test API (PowerShell)
```powershell
$token = "<user_jwt>"
$headers = @{ Authorization = "Bearer $token" }

# Tạo project blank
$body = @{
  mode = "blank"
  brief = @{
    topic = "Test topic"
    audience = "developers"
    language = "vi"
    duration_target_seconds = 600
    aspect_ratio = "16:9"
    tone = "casual"
    visual_style = "cinematic"
  }
} | ConvertTo-Json -Depth 5

$resp = Invoke-RestMethod -Uri "http://localhost:8000/api/projects" -Method Post -Headers $headers -ContentType "application/json" -Body $body
Write-Host $resp.id

# Tạo lại cùng brief → phải trả cùng id
$resp2 = Invoke-RestMethod -Uri "http://localhost:8000/api/projects" -Method Post -Headers $headers -ContentType "application/json" -Body $body
Write-Host $resp2.id  # phải = $resp.id
```

### Bước 4: Verify RLS
```powershell
# Test với user B, gọi GET project của user A → phải 404
```

### Bước 5: Run tests
```powershell
.\venv\Scripts\Activate.ps1
pytest tests/api/test_projects.py tests/worker/test_script_generate.py tests/api/test_schemas_projects.py -v --cov=apps.api.routers.projects --cov=apps.api.schemas.projects --cov=apps.worker.services.project_context --cov=apps.worker.tasks.script_generate --cov=apps.worker.tasks.scene_breakdown --cov-report=term-missing
```

### Bước 6: Verify backward compat
```powershell
# Mở /channels/new → vẫn tạo channel-based flow
```

## 5. Định nghĩa "Done" cho Tier 2

Phase 01 được coi là done khi:
- Tất cả checkbox ở mục 1 và 2 đều pass.
- Coverage đạt mục tiêu mục 3.
- Tất cả command ở mục 4 chạy thành công.
- AUDIT-REPORT đã nộp cho Tier 1 (Planner) duyệt.
- KHÔNG tự push git — chờ sếp duyệt.

## 6. Báo cáo Blockers

Nếu bất kỳ verify command nào fail:
1. KHÔNG tự sửa code ngoài scope.
2. Ghi vào `docs/plan/BLOCKERS-phase-01.md`.
3. Invoke skill `debugging-protocol`.
4. Báo cáo lên Tier 1 để có "Quyết định của Planner".
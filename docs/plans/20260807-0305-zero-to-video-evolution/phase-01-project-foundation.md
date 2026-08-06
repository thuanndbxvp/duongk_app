# Phase 01 — Project foundation và Blank Project onboarding

## Context

- Existing: `apps/web/app/(dashboard)/projects/new/page.tsx` hiện yêu cầu YouTube channel URL.
- Existing: `channel_assistants` là root cho idea/script hiện tại.
- Existing: `jobs` có status, progress, payload và credits.
- Existing: `generated_scripts` lưu scenes dưới JSONB.

## Mục tiêu

Cho phép user bắt đầu từ topic mà không cần channel assistant. Tạo `project` làm root entity, đồng thời giữ backward compatibility với flow channel cloning.

## Requirements

### Functional

- Chế độ `blank` và `clone_channel`.
- Creative brief gồm topic, audience, language, duration, aspect ratio, tone, visual style, voice profile, music mood.
- Tạo project idempotent.
- Lưu draft/version của brief.
- Generate concept/outline/script/scene job theo project.
- Approval state: `draft`, `awaiting_approval`, `approved`, `rejected`.
- Project page hiển thị stage và job progress.

### Non-functional

- RLS theo `user_id`.
- Validate payload bằng Pydantic/Zod.
- Không expose service-role key ở client.
- Mọi task lưu input snapshot và output snapshot.

## Architecture

```text
Next.js project wizard
  → FastAPI /api/projects
  → projects + project_briefs
  → Celery content tasks
  → jobs / sub_progress
  → project workspace
```

`channel_assistant_id` nullable. Với blank project, prompt dùng preset genre/style thay vì DNA channel.

## Related files

### Modify

- `D:\appDK\apps\web\app\(dashboard)\projects\new\page.tsx` — thêm mode blank.
- `D:\appDK\apps\api\main.py` — mount project router nếu chưa có.
- `D:\appDK\apps\worker\tasks\script_generate.py` — nhận project brief và optional assistant.
- `D:\appDK\apps\worker\tasks\scene_breakdown.py` — output scene contract mới.
- `D:\appDK\apps\worker\services\rag_service.py` — blank context fallback.

### Create

- `D:\appDK\supabase\migrations\0023_projects_foundation.sql`
- `D:\appDK\apps\api\routers\projects.py`
- `D:\appDK\apps\api\schemas\projects.py`
- `D:\appDK\apps\worker\services\project_context.py`
- `D:\appDK\apps\web\app\(dashboard)\projects\[id]\page.tsx`
- `D:\appDK\apps\web\components\project-wizard.tsx`

## Implementation steps

1. Tạo migration `projects`, `project_briefs`, `project_stage_events`.
2. Thêm enum/check constraints cho mode, status và approval state.
3. Viết API create/get/update/approve project.
4. Tách prompt context thành `build_project_context()`.
5. Cho script task nhận `project_id`, lấy brief snapshot và optional channel DNA.
6. Map script output sang schema versioned.
7. Thêm workspace route và stage status.
8. Bổ sung tests API/RLS/task payload/idempotency.

## Acceptance criteria

- User tạo project bằng topic mà không có assistant.
- User cũ vẫn chạy flow channel-based.
- Project reload không mất brief.
- Job retry dùng cùng project và không tạo duplicate output.
- Unauthorized user không đọc hoặc sửa project khác.

## Risks

- Đổi root từ assistant sang project có thể phá API cũ.
- Mitigation: nullable `project_id` ở migration chuyển tiếp, adapter lookup và deprecation plan.

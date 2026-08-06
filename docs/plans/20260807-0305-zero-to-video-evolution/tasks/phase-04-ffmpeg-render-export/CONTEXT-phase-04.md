# Bối cảnh Hệ thống (CONTEXT): Phase 04 — FFmpeg Render & Export

## 1. Tri thức Tổng hợp
- **Repomix Bundle:** `.\CONTEXT_BUNDLE.md`
- **Phase plan:** `D:\appDK\docs\plans\20260807-0305-zero-to-video-evolution\phase-04-ffmpeg-render-export.md`

## 2. Codebase Analysis
- FFmpeg binary có sẵn trong Docker worker (xem `docker-compose.yml`).
- `apps/worker/progress_tracker.py` đã có (cần mở rộng cho render).
- Chưa có render queue riêng; cần tạo.

## 3. Files
### Modify
- `apps/worker/celery_app.py` — thêm `render` queue routing.
- `apps/worker/progress_tracker.py` — progress theo stage + subprocess.
- `docker-compose.yml` — worker render, concurrency giới hạn.

### Create
- `supabase/migrations/0026_render_jobs.sql`
- `apps/worker/services/render_planner.py`
- `apps/worker/services/ffmpeg_runner.py`
- `apps/worker/tasks/render_video.py`
- `apps/api/routers/render.py`
- `apps/api/schemas/render.py`
- `apps/web/components/video-preview.tsx`
- `tests/worker/test_ffmpeg_runner.py`

## 4. Dependencies
- ffmpeg, ffprobe.
- psutil (để kill process).
- supabase-py.

## 5. Ràng buộc
- Windows PowerShell.
- Cancel phải kill FFmpeg process thật, không chỉ set flag.
- Output verify bằng ffprobe trước khi upload R2.
- H.264 MP4 MVP; 4K để sau.
- Chỉ 1 draft active / project.
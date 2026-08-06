# Phase 04 — FFmpeg Draft/Final Render và Export

## Mục tiêu

Tạo video thực sự từ timeline model, có draft nhanh, final render, progress, cancel thật, retry và output verification.

## Kiến trúc

```text
Timeline JSON
  → RenderPlanner
  → Celery render task
  → FFmpeg subprocess
  → progress events
  → R2 output
  → ffprobe verification
```

Render job phải giữ process handle trong worker registry theo `job_id`. API cancel chỉ đặt `cancel_requested` và gửi signal an toàn tới process; worker xác nhận trạng thái cuối cùng là `cancelled`.

## Render stages

1. Validate timeline/assets/audio/subtitle.
2. Normalize video input: scale/pad/crop/fps/pixel format.
3. Ken Burns cho ảnh tĩnh; trim/scale cho video.
4. Xfade transitions.
5. Subtitle overlay theo SRT/style.
6. Mix voice + music + SFX; sidechain ducking và fade.
7. Encode H.264 MP4 cho MVP.
8. ffprobe verify streams, duration, dimensions, FPS và codec.
9. Upload output và ghi manifest.

## Data/API

Mở rộng `jobs` hoặc tạo migration `0026_render_jobs.sql`:

- `project_id`.
- `job_type`.
- `cancel_requested`.
- `worker_task_id`.
- `output_asset_id`.
- `render_config`.
- `error_code`.
- `retry_count`.

API:

- `POST /api/projects/{id}/render/draft`.
- `POST /api/projects/{id}/render/final`.
- `GET /api/jobs/{id}`.
- `POST /api/jobs/{id}/cancel`.
- `GET /api/projects/{id}/exports`.

## Draft strategy

- 720p.
- Lower CRF/fast preset.
- Optional low-bitrate preview.
- Có thể giới hạn 1 draft active/project.

Final:

- 1080p MVP; 4K sau khi cost/performance rõ.
- H.264 MP4.
- Preserve SRT, voiceover và project manifest.

## Related files

### Create

- `apps/worker/services/render_planner.py`.
- `apps/worker/services/ffmpeg_runner.py`.
- `apps/worker/tasks/render_video.py`.
- `apps/api/routers/render.py`.
- `apps/api/schemas/render.py`.
- `apps/web/components/video-preview.tsx`.
- `supabase/migrations/0026_render_jobs.sql`.

### Modify

- `apps/worker/celery_app.py` — thêm render queue routing.
- `apps/worker/progress_tracker.py` — progress theo stage và subprocess.
- `docker-compose.yml` — worker render, giới hạn concurrency.

## Acceptance criteria

- Render được video từ 3 scene image + voice + SRT.
- Progress tăng thực theo stderr/time, không chỉ fake increment.
- Cancel dừng FFmpeg và không đánh dấu completed.
- Một scene/asset lỗi cho error code rõ và retry được.
- Output verify trước khi trả download URL.

# MSEW: Phase 04 — FFmpeg Render & Export

## Prerequisites
- Branch: `feature/phase-04-render`.
- Phase 03 merged (cần `timelines` + `voice_lines` + `subtitle_tracks`).
- FFmpeg binary verify: `ffmpeg -version`.

## Files KHÔNG được đụng
- `apps/worker/tasks/tts_scene.py` (Phase 03).
- `apps/worker/services/scene_breaker.py`.

---

## Micro-Steps

### Step 1: Migration `0026_render_jobs.sql`

```sql
-- Mở rộng jobs (nếu cần) hoặc tạo mới render_jobs
CREATE TABLE IF NOT EXISTS public.render_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  job_type text NOT NULL CHECK (job_type IN ('draft', 'final')),
  cancel_requested boolean NOT NULL DEFAULT false,
  worker_task_id text NULL,
  output_asset_id uuid NULL REFERENCES public.assets(id) ON DELETE SET NULL,
  render_config jsonb NOT NULL DEFAULT '{}'::jsonb,
  error_code text NULL,
  error_message text NULL,
  retry_count int NOT NULL DEFAULT 0,
  started_at timestamptz NULL,
  finished_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled'))
);

CREATE INDEX idx_render_jobs_project_status ON public.render_jobs(project_id, status);

ALTER TABLE public.render_jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "render_jobs_owner_all" ON public.render_jobs
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = render_jobs.project_id AND p.user_id = auth.uid()))
  WITH CHECK (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = render_jobs.project_id AND p.user_id = auth.uid()));
```

---

### Step 2: Pydantic schemas `render.py`

```python
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

RenderKind = Literal["draft", "final"]

class RenderStartRequest(BaseModel):
    model_config = {"extra": "forbid"}
    kind: RenderKind = "draft"
    timeline_id: UUID  # specific timeline version

class RenderJobResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    project_id: UUID
    job_type: RenderKind
    status: str
    progress: float = Field(default=0.0, ge=0, le=1)
    error_code: Optional[str]
    output_asset_id: Optional[UUID]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

class ExportResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    job_id: UUID
    download_url: str
    expires_at: datetime
```

---

### Step 3: FastAPI router `/api/render`

```python
# POST /api/projects/{id}/render/draft|final
# GET /api/jobs/{job_id}
# POST /api/jobs/{job_id}/cancel
# GET /api/projects/{id}/exports
```

---

### Step 4: RenderPlanner

```python
# apps/worker/services/render_planner.py
def compile(timeline_model: dict, kind: str) -> list[str]:
    # kind = "draft" → 720p, fast preset; "final" → 1080p, slow preset.
    # Trả về argv[] cho FFmpeg.
    ...
```

---

### Step 5: FFmpegRunner

```python
# apps/worker/services/ffmpeg_runner.py
import subprocess, re
def run(argv: list[str], cancel_event, progress_cb) -> int:
    proc = subprocess.Popen(argv, stderr=subprocess.PIPE, universal_newlines=True, encoding="utf-8")
    pid = proc.pid
    # ... poll cancel_event → kill nếu True
    # ... parse stderr time= → progress_cb
    return proc.wait()
```

Register PID ở `WorkerRegistry` để cancel có thể kill.

---

### Step 6: Celery task `render_video.py`

```python
@shared_task(bind=True)
def render_video(self, render_job_id: str):
    job = get_render_job(render_job_id)
    job.status = "running"; job.started_at = datetime.utcnow(); save(job)
    try:
        argv = RenderPlanner.compile(get_timeline(job.timeline_id), job.job_type)
        rc = FFmpegRunner.run(argv, cancel_event=lambda: job.cancel_requested, progress_cb=lambda p: update_progress(job.id, p))
        if rc != 0: raise RuntimeError(f"ffmpeg exit {rc}")
        verify_output(job)
        job.status = "success"
    except CancelledError:
        job.status = "cancelled"
    except Exception as e:
        job.status = "failed"; job.error_code = classify_error(e)
    job.finished_at = datetime.utcnow(); save(job)
```

---

### Step 7: Output verification

```python
import subprocess, json
def verify_output(job):
    path = local_path_of(job)
    info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path]))
    if not info["streams"]: raise RuntimeError("no_streams")
    if float(info["format"]["duration"]) < 1.0: raise RuntimeError("too_short")
    # codec phải là h264
```

---

### Step 8: Video preview UI

`apps/web/components/video-preview.tsx` — HTML5 `<video>` với download URL từ export response. Hiển thị progress bar reatime qua WebSocket / SSE.

---

### Step 9: Tests

Test cases:
- Cancel mid-render → FFmpeg process chết, status='cancelled', output KHÔNG tồn tại.
- Progress callback được gọi với giá trị tăng dần.
- Output verification: ffprobe trả streams + duration hợp lệ.
- Retry 1 render fail tăng `retry_count`, không tạo duplicate output.
- 1 project chỉ có 1 draft active.

```powershell
pytest tests/worker/test_ffmpeg_runner.py tests/worker/test_render_video.py -v --cov=apps.worker.services.render_planner --cov=apps.worker.services.ffmpeg_runner --cov=apps.worker.tasks.render_video --cov-report=term-missing
```

Expected coverage ≥80%.
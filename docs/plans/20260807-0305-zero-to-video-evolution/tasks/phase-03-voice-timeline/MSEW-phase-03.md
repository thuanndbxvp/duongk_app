# MSEW: Phase 03 — Voice per Scene, SRT & Timeline

## Prerequisites
- Branch: `git checkout -b feature/phase-03-voice-timeline`.
- Phase 02 merged (cần `project_scenes`).
- OmniVoice local chạy: `curl http://localhost:8001/health`.

## Files KHÔNG được đụng
- `apps/omnivoice/app/main.py` (chỉ thêm wrapper, không đụng inference core).
- `apps/worker/services/scene_breaker.py`.

---

## Micro-Steps

### Step 1: Migration `0025_voice_lines_timelines.sql`

```sql
CREATE TABLE IF NOT EXISTS public.voice_lines (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scene_id uuid NOT NULL REFERENCES public.project_scenes(id) ON DELETE CASCADE,
  voice_profile_id uuid NULL REFERENCES public.voice_profiles(id),
  voice_version int NOT NULL DEFAULT 1,
  text text NOT NULL,
  storage_key text NULL,
  duration_seconds numeric(10,3) NULL,
  provider text NOT NULL,
  model_version text NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled')),
  error_code text NULL,
  error_message text NULL,
  started_at timestamptz NULL,
  finished_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (scene_id, voice_version)
);

CREATE TABLE IF NOT EXISTS public.subtitle_tracks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  format text NOT NULL DEFAULT 'srt',
  storage_key text NOT NULL,
  version int NOT NULL DEFAULT 1,
  status text NOT NULL DEFAULT 'draft',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id, version)
);

CREATE TABLE IF NOT EXISTS public.timelines (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  version int NOT NULL,
  schema_version smallint NOT NULL DEFAULT 1,
  model jsonb NOT NULL,
  status text NOT NULL DEFAULT 'draft',
  created_by uuid REFERENCES auth.users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id, version)
);

ALTER TABLE public.voice_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subtitle_tracks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.timelines ENABLE ROW LEVEL SECURITY;

-- Policies tương tự project_scenes (join qua projects.user_id).
```

**Verify:** `supabase db reset && psql ... -c "\d public.voice_lines"`

---

### Step 2: Pydantic schemas `voice.py`

```python
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

VoiceStatus = Literal["pending", "running", "success", "failed", "cancelled"]

class VoiceStartRequest(BaseModel):
    model_config = {"extra": "forbid"}
    voice_profile_id: UUID
    voice_version: int = Field(default=1, ge=1)
    scene_ids: Optional[list[UUID]] = None  # None = all scenes

class VoiceLineResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    scene_id: UUID
    voice_version: int
    duration_seconds: Optional[float]
    status: VoiceStatus
    error_code: Optional[str]

class SubtitleTrackResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    project_id: UUID
    format: str
    version: int
    status: str

class TimelineResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    project_id: UUID
    version: int
    schema_version: int
    model: dict
    status: str
    created_at: datetime
```

---

### Step 3: FastAPI router `/api/voice`

Endpoints:
- `POST /api/projects/{id}/voice/start`
- `GET /api/projects/{id}/voice/status`
- `POST /api/projects/{id}/voice/retry/{scene_id}` — retry 1 scene.
- `POST /api/projects/{id}/timeline/compile` — trigger compile.
- `GET /api/projects/{id}/timeline` — lấy current.

---

### Step 4: Celery task `tts_scene.py`

```python
from celery import shared_task
from apps.worker.services.omnivoice_client import synthesize

@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def tts_scene(self, voice_line_id: str):
    line = get_voice_line(voice_line_id)
    if line.status == "success":
        return  # idempotent
    line.status = "running"
    line.started_at = datetime.utcnow()
    save(line)
    try:
        audio_key = synthesize(text=line.text, voice_profile_id=str(line.voice_profile_id))
        line.storage_key = audio_key
        # ffprobe duration
        line.duration_seconds = measure_duration_ffprobe(audio_key)
        line.status = "success"
        line.finished_at = datetime.utcnow()
    except TimeoutError as e:
        line.status = "failed"
        line.error_code = "tts_timeout"
        line.error_message = str(e)
    save(line)
    # Trigger timeline recompile nếu đủ scenes done
    maybe_recompile_timeline(line.scene.project_id)
```

---

### Step 5: ffprobe service

```python
import subprocess, json
def measure_duration_ffprobe(storage_key: str) -> float:
    local_path = download_from_r2(storage_key)
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", local_path
    ])
    return float(json.loads(out)["format"]["duration"])
```

---

### Step 6: SRT generator

```python
def build_srt(voice_lines: list[dict]) -> str:
    blocks = []
    cursor = 0.0
    for line in voice_lines:
        start = cursor
        dur = line["duration_seconds"]
        end = start + dur
        blocks.append(f"{len(blocks)+1}\n{sec_to_srt(start)} --> {sec_to_srt(end)}\n{line['text']}\n")
        cursor = end
    return "\n".join(blocks)
```

---

### Step 7: Timeline compiler

Output JSON:
```json
{
  "schema_version": 1,
  "clips": [{"scene_id": "...", "asset_id": "...", "start": 0, "duration": 6.5, "fit_mode": "cover", "motion": "ken_burns_zoom_in"}],
  "transitions": [...],
  "audio_tracks": [{"kind": "voice", "track_id": "..."}, {"kind": "music", "track_id": null}],
  "subtitle_track": {"source": "srt", "style": "default", "safe_area": "1080x1920_20pct"},
  "output": {"width": 1080, "height": 1920, "fps": 30, "codec": "h264", "quality": "high"}
}
```

---

### Step 8: UI timeline editor

Component `timeline-editor.tsx`: hiển thị clips + audio tracks + subtitle safe area; cho phép kéo thả reorder, chỉnh motion preset.

---

### Step 9: Tests

Test cases:
- tts_scene idempotent (gọi 2 lần cùng key → không tạo duplicate audio).
- timeout → status=failed, error_code="tts_timeout".
- ffprobe trả về duration đúng (test với file fixture).
- SRT timestamp khớp với tổng voice line duration.
- Timeline compile tự động khi tất cả scene done.

```powershell
pytest tests/api/test_voice.py tests/worker/test_tts_scene.py -v --cov=apps.api.routers.voice --cov=apps.worker.tasks.tts_scene --cov-report=term-missing
```

Expected coverage ≥80%.
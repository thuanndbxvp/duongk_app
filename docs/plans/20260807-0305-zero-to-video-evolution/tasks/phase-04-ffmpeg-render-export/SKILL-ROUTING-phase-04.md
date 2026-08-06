# SKILL-ROUTING: Phase 04 — FFmpeg Render

## Per-step Mapping

| Step | Task | Primary | Reference | Fallback |
|---|---|---|---|---|
| 1 | Migration `jobs` extension | `databases` | `backend-development` | `debugging` |
| 2 | Pydantic schemas render | `backend-development` | `databases` | `debugging` |
| 3 | FastAPI router render (start/cancel/status) | `backend-development` | `databases` | `debugging` |
| 4 | RenderPlanner từ timeline JSON → ffmpeg command | `backend-development` | `planning` | `debugging` |
| 5 | FFmpegRunner với progress + cancel | `backend-development` | `media-processing` | `debugging` |
| 6 | Celery task render_video | `backend-development` | `planning` | `debugging` |
| 7 | Output verification (ffprobe) | `backend-development` | `media-processing` | `debugging` |
| 8 | Video preview UI | `frontend-development` | `ui-styling` | `aesthetic` |
| 9 | Tests cancel + progress + verify | `testing-protocol` | `debugging-protocol` | `debugging` |
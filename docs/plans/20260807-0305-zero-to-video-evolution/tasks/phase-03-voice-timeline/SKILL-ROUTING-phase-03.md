# SKILL-ROUTING: Phase 03 — Voice per Scene

## 1. Chiến lược
Phase 03 wire-up TTS với scene contract, đo actual duration, sinh SRT, compile timeline. Ưu tiên:
- Idempotency chặt (retry an toàn).
- Duration từ audio thật (không đoán WPM).
- Timeline version rollback.

## 2. Per-step Mapping

| Step | Task | Primary | Reference | Fallback |
|---|---|---|---|---|
| 1 | Migration voice_lines + subtitle_tracks + timelines | `databases` | `backend-development` | `debugging` |
| 2 | Pydantic schemas voice | `backend-development` | `databases` | `debugging` |
| 3 | FastAPI router voice + start/status | `backend-development` | `databases` | `debugging` |
| 4 | Celery task tts_scene (idempotent) | `backend-development` | `planning` | `debugging` |
| 5 | ffprobe service đo duration | `backend-development` | `media-processing` | `debugging` |
| 6 | SRT generator từ timing | `backend-development` | `planning` | `debugging` |
| 7 | Timeline compiler | `backend-development` | `planning` | `debugging` |
| 8 | UI timeline editor | `frontend-development` | `ui-styling` | `aesthetic` |
| 9 | Tests | `testing-protocol` | `debugging-protocol` | `debugging` |
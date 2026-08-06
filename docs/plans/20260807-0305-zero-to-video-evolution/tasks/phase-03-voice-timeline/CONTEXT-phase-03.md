# Bối cảnh Hệ thống (CONTEXT): Phase 03 — Voice per Scene, SRT & Timeline Model

## 1. Tri thức Tổng hợp
- **Repomix Bundle:** `.\CONTEXT_BUNDLE.md`
- **Phase plan:** `D:\appDK\docs\plans\20260807-0305-zero-to-video-evolution\phase-03-voice-timeline.md`

## 2. Codebase Analysis
- Module `apps/omnivoice/app/main.py`: OmniVoice inference có lock + timeout sẵn.
- `voice_profiles` đã tồn tại (từ Phase 0).
- TTS chưa liên kết chặt với scene contract từ Phase 02.

## 3. Files liên quan
### Modify
- `apps/worker/tasks/scene_breakdown.py` (Phase 02): gắn voice_line_id.
- `apps/omnivoice/app/main.py`: nhận `voice_lines` row + trả duration.

### Create
- `supabase/migrations/0025_voice_lines_timelines.sql`
- `apps/api/routers/voice.py`
- `apps/api/schemas/voice.py`
- `apps/worker/tasks/tts_scene.py`
- `apps/worker/tasks/srt_generate.py`
- `apps/worker/services/timeline_compiler.py`
- `apps/web/components/timeline-editor.tsx`
- `tests/api/test_voice.py`
- `tests/worker/test_tts_scene.py`

## 4. Dependencies
- OmniVoice SDK (đã có).
- ffmpeg + ffprobe (sẵn).
- supabase-py.

## 5. Ràng buộc
- Windows PowerShell verify.
- CRLF.
- **KHÔNG dùng WPM làm duration cuối** — chỉ là estimate trước TTS. Duration thật = ffprobe.
- Voice line idempotency: `(project_id, scene_id, voice_version)`.
- Timeout cho mỗi scene ≤ 60s.
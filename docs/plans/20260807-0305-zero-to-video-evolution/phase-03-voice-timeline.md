# Phase 03 — Voice per scene, SRT và Timeline Model

## Context

- OmniVoice service tại `apps/omnivoice/app/main.py` đã có inference lock và timeout.
- `voice_profiles` đã tồn tại.
- TTS hiện chưa là stage có liên kết chặt với scene/timeline.

## Mục tiêu

Tạo voice track từ narration theo từng scene, đo duration thật, sinh subtitle và compile thành timeline model.

## Data model

Tạo migration `0025_voice_lines_timelines.sql`:

- `voice_lines`: scene id, text, voice profile, provider, storage key, duration, status.
- `subtitle_tracks`: project id, format, storage key, version, status.
- `timelines`: project id, version, JSON model, status, created_by.

## Flow

```text
Scene narration
  → TTS job per scene
  → Audio output + actual duration
  → Recalculate scene timestamps
  → Generate SRT
  → Create timeline version
```

Không dùng WPM làm duration cuối. WPM chỉ là estimate trước TTS.

## Timeline contract

- `clips`: asset id, scene id, start, duration, fit mode, motion.
- `transitions`: type, duration, offset.
- `audio_tracks`: voice/music/SFX, volume, fade, ducking.
- `subtitle_track`: source, style, safe area.
- `output`: dimensions, FPS, codec, quality.

Mỗi save tạo version hoặc revision có thể rollback.

## Implementation steps

1. Thêm API start voice job và status.
2. Tách TTS request theo scene, idempotency key `project_id:scene_id:voice_version`.
3. Materialize audio output lên R2.
4. Đo duration bằng ffprobe/wave.
5. Cập nhật actual duration và tính lại timestamps.
6. Sinh SRT từ voice line timing.
7. Tạo timeline compiler từ scene/assets/voice/subtitles.
8. UI hiển thị audio duration và mismatch cảnh.
9. Test serial inference, timeout, retry và partial failure.

## Acceptance criteria

- Regenerate một scene không cần chạy lại TTS của scene khác.
- TTS timeout chuyển job thành failed có error code.
- Timeline tự cập nhật khi duration thật thay đổi.
- SRT khớp voice line timestamps.
- User có thể chọn preset hoặc voice profile của mình.

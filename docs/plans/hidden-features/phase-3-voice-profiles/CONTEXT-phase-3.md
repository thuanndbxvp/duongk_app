# Phase 3 — Context & Background

## 1. Why this phase exists

Voice profile là **core production feature** — mỗi video cần voice narration. Hiện user phải chọn voice mặc định (system voices). Tính năng clone voice riêng (từ sample audio) là differentiator lớn của appDK so với competitor.

Backend đã implement đầy đủ (8 endpoints). User không có UI để access.

## 2. Background: TTS Providers

3 providers:
- **OmniVoice** (Vietnamese-focused, primary)
- **ElevenLabs** (English/global)
- **Google Cloud TTS** (fallback)

Mỗi provider có:
- Supported languages
- Clone support (yes/no)
- Sample requirement (yes/no)

Frontend cần show capabilities khác nhau.

## 3. Background: Voice clone workflow

1. User record 30s audio (MP3/WAV)
2. Upload → POST /api/voices with multipart
3. Backend validate → call provider API → save voice_id
4. Voice có thể dùng cho bất kỳ project nào

Sample audio yêu cầu:
- 10-60 seconds duration
- Single speaker
- No background noise
- Format: MP3 hoặc WAV

## 4. Background: Test endpoint

POST /api/voices/{id}/test takes text → returns generated audio. Dùng để verify voice clone quality trước khi commit.

## 5. What is NOT in this phase

- Style Bible UI (P4)
- Voice profile import từ URL (deferred)
- Bulk voice operations (deferred)
- Voice analytics (deferred)

## 6. References

- `apps/api/modules/voices/routes.py` (existing endpoints)
- `apps/worker/services/voice_clone.py` (clone logic)
- `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` §3.1.B
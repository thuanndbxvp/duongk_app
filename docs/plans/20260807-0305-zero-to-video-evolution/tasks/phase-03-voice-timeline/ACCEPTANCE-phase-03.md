# ACCEPTANCE: Phase 03 — Voice per Scene

## 1. Functional
- [ ] User start voice job → TTS chạy per scene.
- [ ] Regenerate 1 scene không cần chạy lại scene khác.
- [ ] Timeout chuyển job `failed` với `error_code`.
- [ ] Timeline tự cập nhật khi actual_duration thay đổi.
- [ ] SRT khớp voice line timestamps (test bằng ffprobe so sánh).
- [ ] User chọn voice preset hoặc voice profile của mình.

## 2. Non-functional
- [ ] Idempotency: `(scene_id, voice_version)` unique.
- [ ] Timeout per scene ≤ 60s.
- [ ] Storage R2 signed URL ≤ 5 phút.

## 3. Coverage
- ≥80% cho `apps/api/routers/voice.py`, `apps/worker/tasks/tts_scene.py`, `apps/worker/services/timeline_compiler.py`.
- 100% cho `apps/api/schemas/voice.py`.

## 4. Manual Verify
```powershell
.\venv\Scripts\Activate.ps1
uvicorn apps.api.main:app --reload
# Start voice cho 1 project test, kiểm tra SRT output khớp audio duration.
```

## 5. Done
- Tất cả checkbox pass.
- Coverage đạt.
- AUDIT-REPORT nộp.
- KHÔNG push git.
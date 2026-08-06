# ACCEPTANCE: Phase 04 — FFmpeg Render

## 1. Functional
- [ ] Render được từ 3 scene (image + voice + SRT) → MP4 H.264.
- [ ] Draft 720p + Final 1080p.
- [ ] Progress tăng thực theo stderr FFmpeg.
- [ ] Cancel dừng FFmpeg → status='cancelled', không mark completed.
- [ ] 1 scene/asset lỗi → error_code rõ + retry được.
- [ ] Output verify trước khi trả download URL.
- [ ] 1 project chỉ 1 draft active.

## 2. Non-functional
- [ ] Cancel latency < 3s.
- [ ] Per-project concurrency ≤ 1 draft, ≤ 1 final.
- [ ] R2 signed URL download TTL ≤ 5 phút.

## 3. Coverage
- ≥80% cho `render_planner`, `ffmpeg_runner`, `render_video`.
- 100% cho `schemas/render.py`.

## 4. Manual Verify
```powershell
.\venv\Scripts\Activate.ps1
# Render 1 project test, cancel mid-way, kiểm tra status='cancelled' và FFmpeg process không còn.
```

## 5. Done
- All checkboxes pass.
- AUDIT-REPORT nộp.
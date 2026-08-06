# PLAN: Phase 03 — Voice per Scene, SRT & Timeline

## 1. Mục tiêu
- **Mô tả:** Tạo voice track từ narration per scene, đo duration thật, sinh SRT, compile timeline model versioned.
- **Giá trị:** Timeline có dữ liệu thật; render Phase 04 có input chính xác; A/B thumbnail có voice hook.

## 2. Kiến trúc
- **Patterns:**
  - **Voice line = 1 row per scene per voice version** (cho rollback).
  - **Timeline = JSON versioned** với revision history.
  - **Idempotency = (project_id, scene_id, voice_version)**.
- **Flow:**
```text
Scene narration + voice profile
  → POST /api/projects/{id}/voice/start
  → enqueue tts_scene cho từng scene
  → OmniVoice synthesize → R2
  → ffprobe duration → update project_scenes.actual_duration
  → Generate SRT → R2
  → Compile timeline v1 → R2
```

## 3. Lý do chọn
- **Phương án A — WPM duration (ĐÃ LOẠI):** Sai số lớn, phá timing.
- **Phương án B — ffprobe actual duration (CHỌN):** Chính xác, idempotent.
- **Phương án C — Hybrid (đã cân nhắc):** Estimate = WPM, actual = ffprobe. Estimate chỉ dùng cho preview.

## 4. Rủi ro

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| OmniVoice timeout | Trung bình | Timeout per scene 60s, mark `failed` với error_code. |
| Partial failure (5/10 scene OK) | Trung bình | Track per-scene status; user retry scene lỗi, không chạy lại cả batch. |
| Timeline drift khi duration thật đổi | Trung bình | Tự động re-compile timeline version mới. |
| SRT timestamp sai so với audio | Thấp | Dùng ffprobe + word-boundary nếu OmniVoice trả timing. |

## 5. Nỗ lực
- ~800 LOC, 9 micro-steps, 4 ngày Tier 2.
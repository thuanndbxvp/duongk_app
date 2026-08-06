# Tier 1 Deliverables Index — Zero to Video Evolution

> Mỗi phase = 1 task Tier 2. Mỗi task có đủ 5 file theo template `.ai-pipeline/templates/`:
> 1. `CONTEXT-phase-XX.md` — bối cảnh + codebase analysis
> 2. `SKILL-ROUTING-phase-XX.md` — phân bổ skill
> 3. `PLAN-phase-XX.md` — kiến trúc + rủi ro + nỗ lực
> 4. `MSEW-phase-XX.md` — micro-steps chi tiết (Code cần viết, Verify command PowerShell)
> 5. `ACCEPTANCE-phase-XX.md` — tiêu chí nghiệm thu

## Thứ tự triển khai

| # | Phase | Task ID | Thư mục | Lệnh giao Tier 2 |
|---|---|---|---|---|
| 1 | Project foundation & Blank Onboarding | `phase-01-project-foundation` | `phase-01-project-foundation/` | `/code phase-01-project-foundation` |
| 2 | Scene Studio, Asset Management, Stock Search | `phase-02-scenes-assets-stock` | `phase-02-scenes-assets-stock/` | `/code phase-02-scenes-assets-stock` |
| 3 | Voice per Scene, SRT, Timeline Model | `phase-03-voice-timeline` | `phase-03-voice-timeline/` | `/code phase-03-voice-timeline` |
| 4 | FFmpeg Draft/Final Render & Export | `phase-04-ffmpeg-render-export` | `phase-04-ffmpeg-render-export/` | `/code phase-04-ffmpeg-render-export` |
| 5 | AI Media, Upscale, Thumbnail, Metadata | `phase-05-ai-media-thumbnail` | `phase-05-ai-media-thumbnail/` | `/code phase-05-ai-media-thumbnail` |
| 6 | Channel Intelligence Feedback Loop | `phase-06-feedback-and-batch` | `phase-06-feedback-and-batch/` | `/code phase-06-feedback-and-batch` |
| 7 | Hardening, Observability, Billing, Launch | `phase-07-hardening-launch` | `phase-07-hardening-launch/` | `/code phase-07-hardening-launch` |
| 8 | Channel Intelligence (chi tiết) | `phase-08-channel-intelligence` | `phase-08-channel-intelligence/` | `/code phase-08-channel-intelligence` |
| 9 | Style Bible & Character Reference | `phase-09-style-bible` | `phase-09-style-bible/` | `/code phase-09-style-bible` |
| 10 | Batch Production, Cost Estimation, Fallback | `phase-10-batch-and-pipeline` | `phase-10-batch-and-pipeline/` | `/code phase-10-batch-and-pipeline` |
| 11 | Character & Background Lab (presets trước batch) | `phase-11-character-background-lab` | `phase-11-character-background-lab/` | `/code phase-11-character-background-lab` |

## Quy trình bàn giao

```
Tier 1 (Planner / tôi)              Tier 2 (Coder)
─────────────────────               ──────────────
5 file Markdown per phase    →      /code <task>
                                  →  Đọc CONTEXT + SKILL-ROUTING + PLAN + MSEW + ACCEPTANCE
                                  →  Sinh Repomix bundle
                                  →  Code theo MSEW micro-steps
                                  →  Verify PowerShell
                                  →  Tests với coverage yêu cầu
                                  →  AUDIT-REPORT (template .ai-pipeline/templates/AUDIT-REPORT.template.md)
                                  →  Commit LOCAL (không push)
                                  →  Nộp AUDIT-REPORT cho Tier 1

Tier 1 duyệt AUDIT-REPORT:
- Section "Quyết định của Planner" trả lời các câu hỏi/lấn cấn
- Duyệt / yêu cầu sửa
- Sếp duyệt cuối → push remote
```

## Phụ thuộc giữa các phase

```
01 ──→ 02 ──→ 03 ──→ 04 ──→ 05 ──→ 06 ──→ 07 (release)
                     │       │       │
                     └──→ 09 ┘       │
                             │       │
                     └──→ 11 ←───────┘
                              │
                              ↓
                            10 (batch, gate 11)
```

## Ràng buộc chung mọi phase

- **Môi trường:** Windows 10/11 PowerShell. Mọi `Verify command` đều dùng PowerShell.
- **Line Ending:** CRLF cho mọi file mới.
- **KHÔNG push git** cho đến khi sếp duyệt (xem `\.claude\memory\no-git-push-until-done.md`).
- **Source immutable:** Asset/code KHÔNG BAO GIỜ bị ghi đè; mọi biến thể là row mới hoặc version mới.
- **RLS:** Mọi bảng mới đều có RLS theo `user_id` (qua join với `projects` / `channel_assistants`).
- **Idempotency:** Mọi Celery task / API write đều có idempotency key.
- **Forbidden:** Không sniff token, scrape session, CAPTCHA bypass, watermark cleanup mặc định, private endpoint không chính thức.
- **Coverage:** Module mới ≥80%, schema 100%.

## Quy ước đặt tên file

```
phase-XX-<slug>/
├── CONTEXT-phase-XX.md
├── SKILL-ROUTING-phase-XX.md
├── PLAN-phase-XX.md
├── MSEW-phase-XX.md
└── ACCEPTANCE-phase-XX.md
```

## Audit trail

Khi Tier 2 nộp AUDIT-REPORT, Tier 1 sẽ append "Quyết định của Planner" và commit duyệt vào file tương ứng trong thư mục `decisions/`.
# Phase 06 — Feedback loop, channel intelligence và batch production

## Mục tiêu

Kết hợp các tính năng Tool 1 + 11 học từ Ai86Studio với nền tảng channel DNA hiện có của appDK:

```text
Published/reference videos
  → transcript + comments + performance signals
  → evidence-backed insights
  → idea backlog
  → brief/script improvement
  → next video
```

## Channel profiles

Giữ `channel_assistants` cho channel cloning, nhưng bổ sung profile version:

- Audience.
- Editorial rules.
- Voice profile.
- Visual style bible.
- Thumbnail rules.
- SEO rules.
- Forbidden claims/phrases.
- Default duration/aspect ratio.

Blank project dùng `genre_profile`; clone project dùng `channel_assistant` + DNA.

## Comment intelligence

Implement qua provider hợp lệ:

1. Import video ID/URL.
2. Fetch comments/replies theo quota.
3. Normalize language, deduplicate và flag spam.
4. Lưu comment reference, likes, parent và fetched timestamp.
5. Cluster themes.
6. Tạo insight kèm evidence comment IDs.
7. Tạo opportunity/brief candidate.
8. Cho user approve trước khi đưa vào script job.

## Batch production

Chỉ triển khai sau khi render/cancel/idempotency ổn định:

- Batch tạo nhiều ideas.
- Batch approve scripts.
- Batch generate scene assets.
- Batch TTS.
- Batch draft render.
- Per-project concurrency limit.
- Global provider rate limit.
- Cost estimate trước khi submit.
- Partial success và retry item-level.

## Acceptance criteria

- Một insight có thể truy ngược đến evidence.
- User có thể tạo idea từ insight mà không copy thủ công.
- Batch failure không làm mất các item đã complete.
- Provider quota và credit cap ngăn batch vượt ngân sách.
- Nhiều channel profile không trộn dữ liệu RAG.

## Risks

- Comment data thiếu hoặc provider quota thay đổi: hiển thị freshness/confidence.
- Insight bias: luôn hiển thị sample evidence, không chỉ score.
- Batch jobs gây nghẽn render/TTS: queue riêng và concurrency limit.

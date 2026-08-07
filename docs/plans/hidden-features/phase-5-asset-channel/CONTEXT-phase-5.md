# Phase 5 — Context & Background

## 1. Why this phase exists

### Asset Library
User generate nhiều asset (image, video, audio) qua các project. Hiện asset chỉ accessible từ project cụ thể → khó reuse. Library global cho phép:
- Tìm kiếm toàn bộ assets
- Filter theo type/tag
- Reuse trong project mới

### Channel Collector
Tính năng competitor research từ Phase 6:
- Scrape channel YouTube
- Extract top videos, comments
- Analyze sentiment, topics
- Generate insights

Backend đã có. User cần UI để:
- Add channel mới
- Track scraping jobs
- Xem insights

## 2. Background: Asset types

3 types:
- **image** — JPG, PNG, WebP
- **video** — MP4, WebM
- **audio** — MP3, WAV, M4A

Mỗi asset có metadata: name, tags, source (pexels/gemini/upload), license, size, checksum.

## 3. Background: Channel scraping

Backend scraping flow:
1. User POST /api/channel-collector/scrape với channel URL
2. Backend enqueue Celery task
3. Task fetches channel data (videos, comments)
4. Backend stores data + generate insights
5. Frontend polls job status

Scrape job có thể mất 5-30 phút cho channel lớn.

## 4. What is NOT in this phase

- Channel analytics dashboard (deferred)
- Asset sharing với team
- Asset version history
- Channel comparison

## 5. References

- `apps/api/modules/assets/routes.py` (existing)
- `apps/api/modules/channel_collector/routes.py` (existing)
- `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` §3.1.D, §3.1.E
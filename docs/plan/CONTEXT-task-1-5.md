# Bối cảnh Hệ thống (CONTEXT): Task 1.5 - Module 2A & Transcript Engine

## 1. Tri thức Tổng hợp
- **Task:** Sprint 1 - Module 2A: Deep Collection + Transcript Engine
- **Mục tiêu:** Thu thập metadata videos và transcript từ YouTube
- **Tài liệu tham khảo:**
  - `docs/plan/PLAN-task-1-5.md` - Kiến trúc chi tiết
  - `docs/implementation_plan_v1_fixes.md` §1.5, §1.6

## 2. Dependencies mới cần cài

```bash
pip install youtube-transcript-api whisper yt-dlp
```

## 3. Các File liên quan và Vai trò

| File | Vai trò | Priority |
|------|---------|----------|
| `apps/api/modules/module_2a/__init__.py` | Module 2A package init | MEDIUM |
| `apps/api/modules/module_2a/formulas.py` | Formula A0, A2 (reuse from module_1) | HIGH |
| `apps/api/modules/module_2a/service.py` | YouTubeCollector service (NEW) | HIGH |
| `apps/api/modules/module_2a/routes.py` | API routes (NEW) | HIGH |
| `apps/api/modules/module_2a/schemas.py` | Pydantic schemas (NEW) | HIGH |
| `apps/api/modules/transcript/__init__.py` | Transcript package | MEDIUM |
| `apps/api/modules/transcript/engine.py` | TranscriptEngine 3-tier (NEW) | HIGH |
| `apps/api/modules/transcript/routes.py` | Transcript routes (NEW) | HIGH |
| `tests/test_module_2a/` | Test suite (NEW) | HIGH |
| `tests/test_transcript/` | Test suite (NEW) | HIGH |

## 4. Kiến trúc Module 2A

```
┌─────────────────────────────────────────────────────────────────┐
│                  MODULE 2A: DEEP COLLECTION                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input: channel_id                                              │
│      │                                                         │
│      ▼                                                         │
│  Step 1: Get video IDs (search.list) ──► max 200 videos       │
│      │                                                         │
│      ▼                                                         │
│  Step 2: Batch into groups of 50                               │
│      │                                                         │
│      ▼                                                         │
│  Step 3: Fetch metadata (videos.list) ──► Parallel (4 concurrent)│
│      │                                                         │
│      ▼                                                         │
│  Step 4: Formula A0 ──► Filter quality videos                  │
│      │                                                         │
│      ▼                                                         │
│  Step 5: Formula A2 ──► Detect viral videos (MAD)             │
│      │                                                         │
│      ▼                                                         │
│  Output: { all_videos, quality_videos, viral_videos }          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 5. Kiến trúc Transcript Engine

```
┌─────────────────────────────────────────────────────────────────┐
│                  TRANSCRIPT ENGINE (3-Tier)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input: video_id, preferred_languages                           │
│      │                                                         │
│      ▼                                                         │
│  TIER 1: youtube-transcript-api                                 │
│      │ [SUCCESS] ──► Return transcript                         │
│      │ [FAIL]                                                  │
│      ▼                                                         │
│  TIER 2: Supadata API                                          │
│      │ [SUCCESS] ──► Return transcript                         │
│      │ [FAIL]                                                  │
│      ▼                                                         │
│  TIER 3: yt-dlp + Whisper                                      │
│      │ [SUCCESS] ──► Return transcript                         │
│      │ [FAIL]                                                  │
│      ▼                                                         │
│  Output: transcript text OR None                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 6. Database Schema (Transcripts)

```sql
-- supabase/migrations/0011_transcripts_cron.sql

CREATE TABLE IF NOT EXISTS transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    language TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '90 days'),
    UNIQUE(video_id, language)
);

-- Indexes
CREATE INDEX idx_transcripts_expires ON transcripts(expires_at);
CREATE INDEX idx_transcripts_channel ON transcripts(channel_id);

-- Cron job (pg_cron)
SELECT cron.schedule(
    'cleanup-expired-transcripts',
    '0 3 * * *',
    $$DELETE FROM transcripts WHERE expires_at < NOW()$$
);
```

## 7. Ràng buộc (Constraints)

| Ràng buộc | Mô tả |
|-----------|--------|
| **Môi trường** | Windows 10/11 (PowerShell) |
| **YouTube API** | 10,000 units/day quota |
| **Batch Size** | 50 videos/request (API limit) |
| **Max Videos** | 200 videos/channel |
| **Transcript TTL** | 90 days |
| **yt-dlp** | Cần ffmpeg trong PATH |

## 8. Sample Output (Expected)

### Module 2A Response
```json
{
  "channel_id": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
  "total_videos_collected": 150,
  "quality_videos": 120,
  "viral_videos": 8,
  "videos": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "Sample Video",
      "views": 50000000,
      "is_viral": true
    }
  ]
}
```

### Transcript Response
```json
{
  "video_id": "dQw4w9WgXcQ",
  "transcript": "Đây là nội dung phụ đề...",
  "language": "vi",
  "tier_used": 1,
  "cached": false
}
```

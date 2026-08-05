# Tiêu chí Nghiệm thu (ACCEPTANCE): Task 1.5 - Module 2A & Transcript Engine

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### Module 2A - Deep Collection
- [ ] **YouTubeCollector** hoạt động:
  - [ ] Fetch được video IDs từ channel
  - [ ] Batch 50 videos/request đúng limit
  - [ ] Parallel fetch với max 4 concurrent
  - [ ] Trả về đúng structure

- [ ] **Formula A0 (reuse from Module 1)**:
  - [ ] Lọc Shorts, Live, low views, old videos
  - [ ] Giữ quality videos

- [ ] **Formula A2 (reuse from Module 1)**:
  - [ ] Phát hiện viral videos
  - [ ] MAD threshold = 3.5

- [ ] **API Routes**:
  - [ ] `POST /api/collect/channel` trả về 200
  - [ ] `GET /api/collect/health` trả về 200

### Transcript Engine - 3-Tier
- [ ] **Tier 1 (youtube-transcript-api)**:
  - [ ] Lấy transcript khi có sẵn
  - [ ] Thử multiple languages

- [ ] **Tier 2 (Supadata API)**:
  - [ ] Fallback khi Tier 1 fail
  - [ ] Cần valid API key

- [ ] **Tier 3 (Whisper)**:
  - [ ] Download audio với yt-dlp
  - [ ] Transcribe với Whisper model
  - [ ] Cleanup audio file sau khi xong

- [ ] **API Routes**:
  - [ ] `POST /api/transcript/` trả về 200 với transcript
  - [ ] `GET /api/transcript/health` trả về 200
  - [ ] 404 khi không lấy được transcript

### pg_cron Migration
- [ ] **Transcripts table**:
  - [ ] Table được tạo đúng schema
  - [ ] Indexes được tạo

- [ ] **Cron job**:
  - [ ] Job được schedule daily lúc 3 AM
  - [ ] DELETE query chạy đúng

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

| Tiêu chí | Yêu cầu | Verification |
|----------|---------|--------------|
| **YouTube API** | Không exceed quota | Monitor quota usage |
| **Batch Size** | Đúng 50 videos/request | Code review |
| **Concurrent** | Max 4 parallel requests | Log verification |
| **Audio** | yt-dlp cleanup sau transcribe | Check temp files |
| **Cron** | Chạy daily 3 AM | `SELECT * FROM cron.job` |

## 3. Mục tiêu Test Coverage

| Metric | Target | Priority |
|--------|--------|----------|
| Overall coverage | ≥80% | HIGH |
| YouTubeCollector coverage | ≥70% | HIGH |
| TranscriptEngine coverage | ≥70% | HIGH |
| Routes coverage | ≥60% | MEDIUM |

## 4. Các bước Manual Verification (Windows)

### Bước 1: Setup Dependencies
```powershell
pip install google-api-python-client youtube-transcript-api openai-whisper yt-dlp
```

### Bước 2: Run pg_cron Migration
```powershell
psql -h localhost -U postgres -d appdk -f supabase/migrations/0011_transcripts_cron.sql
```

### Bước 3: Khởi động API
```powershell
.\venv\Scripts\Activate.ps1
uvicorn apps.api.main:app --reload --port 8000
```

### Bước 4: Test Module 2A Health
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/collect/health" -Method Get
```

### Bước 5: Test Module 2A Collection (với test channel)
```powershell
$body = @{
    channel_id = "UC_x5XG1OV2P6uZZ5FSM9Ttw"  # Google Developers
    max_videos = 50
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/collect/channel" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Expected:** Response với `quality_videos_count`, `viral_videos_count`

### Bước 6: Test Transcript Health
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/transcript/health" -Method Get
```

### Bước 7: Test Transcript (Tier 1 - YouTube API)
```powershell
$body = @{
    video_id = "dQw4w9WgXcQ"
    languages = ["en", "vi"]
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/transcript/" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Expected:** Response với `tier_used: 1` hoặc fallback tiers

### Bước 8: Test pg_cron Job
```powershell
psql -h localhost -U postgres -d appdk -c "SELECT * FROM cron.job WHERE jobname = 'cleanup-expired-transcripts';"
```

### Bước 9: Manual Transcript Cleanup Test
```powershell
# Insert test transcript
psql -h localhost -U postgres -d appdk -c "
INSERT INTO transcripts (video_id, channel_id, language, content, expires_at)
VALUES ('test123', 'test_channel', 'en', 'Test content', NOW() - INTERVAL '1 day');
"

# Run cleanup manually
psql -h localhost -U postgres -d appdk -c "SELECT cron.job_call(1);"

# Verify cleanup
psql -h localhost -U postgres -d appdk -c "SELECT * FROM transcripts WHERE video_id = 'test123';"
```

**Expected:** No rows returned (deleted)

### Bước 10: Run Unit Tests
```powershell
pytest tests/test_module_2a/ tests/test_transcript/ -v --cov=apps/api/modules/module_2a --cov=apps/api/modules/transcript --cov-report=term-missing
```

## 5. Sign-off Checklist

```
TIER 2 SELF-CHECK:

Module 2A:
  [ ] YouTubeCollector works
  [ ] Batch 50 videos per request
  [ ] Formula A0/A2 applied
  [ ] API routes respond correctly

Transcript Engine:
  [ ] 3-tier fallback works
  [ ] Tier 1 youtube-transcript-api
  [ ] Tier 2 Supadata
  [ ] Tier 3 Whisper
  [ ] Cleanup temp files

pg_cron:
  [ ] Migration runs successfully
  [ ] Cron job scheduled
  [ ] Cleanup works

Testing:
  [ ] All unit tests pass
  [ ] Coverage ≥ 80%

Files Created/Modified:
  [ ] apps/api/modules/module_2a/ (NEW)
  [ ] apps/api/modules/transcript/ (NEW)
  [ ] supabase/migrations/0011_transcripts_cron.sql (NEW)
  [ ] tests/test_module_2a/ (NEW)
  [ ] tests/test_transcript/ (NEW)
```

## 6. Blocker Reporting

**Nếu gặp blocker, tạo file `BLOCKERS-task-1-5.md`:**

```markdown
# BLOCKERS: Task 1.5

## Blocker 1
**Mô tả:** <Mô tả lỗi>

**Ảnh hưởng:** <Impact>

**Đề xuất:** <Suggestion>

## ...
```

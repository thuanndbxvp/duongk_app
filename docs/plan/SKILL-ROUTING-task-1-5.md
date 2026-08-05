# Phân bổ Kỹ năng (SKILL-ROUTING): Task 1.5 - Module 2A & Transcript Engine

## 1. Chiến lược tổng thể (Overall Strategy)

Module 2A và Transcript Engine là các task backend tập trung vào:
- YouTube API integration
- Data processing với NumPy
- Async I/O cho API calls
- File I/O cho audio processing (yt-dlp)

Không cần UI. Tập trung vào backend skills.

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | Module 2A Package | `general-purpose` | - | - | Package init |
| Step 2 | YouTubeCollector Service | `backend-development` | `general-purpose` | `planning` | YouTube API integration |
| Step 3 | API Routes (2A) | `backend-development` | - | - | FastAPI routes |
| Step 4 | Transcript Package | `general-purpose` | - | - | Package init |
| Step 5 | TranscriptEngine 3-Tier | `general-purpose` | `backend-development` | `planning` | Complex async logic |
| Step 6 | Transcript Routes | `backend-development` | - | - | FastAPI routes |
| Step 7 | pg_cron Migration | `databases` | `general-purpose` | - | SQL migration |
| Step 8 | Unit Tests | `tester` | `general-purpose` | - | Pytest tests |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)

| Skill | Khi nào gọi | Mục đích |
|-------|--------------|----------|
| `general-purpose` | Most steps | Code generation |
| `backend-development` | API routes, async logic | FastAPI patterns |
| `databases` | Migration file | SQL syntax |
| `tester` | Unit tests | Pytest setup |
| `debugging` | Fail verification | Debug YouTube API |

## 4. Files KHÔNG được đụng (Do Not Touch)

| File | Lý do |
|------|-------|
| `apps/api/main.py` | Đã updated ở Task 1.4 |
| `apps/api/core/bulkhead.py` | Task 1.4 đã tạo |
| `apps/api/core/cache.py` | Task 1.4 đã tạo |
| `packages/shared-types/` | Models đã defined |
| `supabase/migrations/0001-0010/` | Đã có từ Task 1.1 |

## 5. Special Considerations

### YouTube API
- Batch 50 video IDs per request (API limit)
- Max 200 videos per channel
- Handle quota exceeded errors
- Implement retry với exponential backoff

### yt-dlp / Whisper
- Cần ffmpeg trong PATH cho yt-dlp
- Whisper model "base" tối ưu speed/accuracy
- Audio file tạm thời, xóa sau khi transcribe

### pg_cron
- Extension phải được enable trước
- Cron job chạy daily lúc 3 AM
- Test cleanup với DELETE query trước

## 6. Verification Strategy

| Step | Verify Command | Expected |
|------|----------------|----------|
| 1-3 | `python -c "from apps.api.modules.module_2a import router; print('OK')"` | OK |
| 4-6 | `python -c "from apps.api.modules.transcript import router; print('OK')"` | OK |
| 7 | `psql` test query | Rows affected |
| 8 | `pytest tests/test_module_2a/ tests/test_transcript/ -v` | All passed |

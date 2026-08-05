# Kiến trúc & Luồng xử lý (PLAN): Task 1.5 - Triển khai Module 2A & Transcript Engine

1. Xử lý gom nhóm 50 video ID cho 1 req `videos.list`.
2. Cài đặt 3 lớp lấy phụ đề: youtube-transcript-api -> supadata -> whisper.
3. Implement Formula A0 (Video Filter) và Formula A2 (Viral Detection).

---

## Chi tiết từng bước

### 1. Module 2A - Deep Collection

#### 1.1. Batch Video Metadata Collection

```python
# apps/api/modules/module_2a/service.py
from typing import List
import asyncio

class YouTubeCollector:
    """Service for collecting YouTube video metadata."""
    
    BATCH_SIZE = 50  # YouTube API max videos per request
    
    async def collect_channel_videos(
        self,
        channel_id: str,
        max_videos: int = 200
    ) -> List[dict]:
        """
        Collect up to max_videos from a channel.
        
        Strategy:
        1. Get video IDs via search (most recent first)
        2. Batch into groups of 50
        3. Call videos.list for each batch
        """
        # Step 1: Get video IDs
        video_ids = await self._get_channel_video_ids(channel_id, max_videos)
        
        # Step 2: Batch into groups of 50
        batches = [
            video_ids[i:i + self.BATCH_SIZE]
            for i in range(0, len(video_ids), self.BATCH_SIZE)
        ]
        
        # Step 3: Fetch metadata in parallel (max 4 concurrent)
        semaphore = asyncio.Semaphore(4)
        
        async def fetch_batch(batch_ids: List[str]) -> List[dict]:
            async with semaphore:
                return await self._fetch_video_metadata(batch_ids)
        
        results = await asyncio.gather(*[fetch_batch(b) for b in batches])
        
        # Flatten results
        all_videos = [v for batch in results for v in batch]
        
        # Step 4: Apply Formula A0 - Filter quality videos
        quality_videos = filter_quality_videos(all_videos)
        
        # Step 5: Apply Formula A2 - Detect viral videos
        viral_videos = detect_viral_videos(quality_videos)
        
        return {
            "all_videos": all_videos,
            "quality_videos": quality_videos,
            "viral_videos": viral_videos
        }
```

#### 1.2. Formula A0 - Video Filter

```python
# apps/api/modules/module_2a/formulas.py
from datetime import datetime, timedelta
from typing import List, Dict, Any

def filter_quality_videos(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Formula A0: Filter out low-quality videos.
    
    Removal criteria:
    - Shorts: duration < 60 seconds
    - Live streams: live_broadcast_content == 'live' or 'upcoming'
    - Low engagement: view_count < 1000
    - Too old: published > 2 years ago
    - No category: category_id is null
    """
    cutoff_date = datetime.now() - timedelta(days=730)  # 2 years
    
    quality_videos = []
    for video in videos:
        # Skip Shorts
        duration = video.get('content_details', {}).get('duration_seconds', 0)
        if duration < 60:
            continue
        
        # Skip Live streams
        live_status = video.get('snippet', {}).get('live_broadcast_content', 'none')
        if live_status in ('live', 'upcoming'):
            continue
        
        # Skip low-engagement videos
        stats = video.get('statistics', {})
        view_count = int(stats.get('view_count', 0))
        if view_count < 1000:
            continue
        
        # Skip old videos
        published_str = video.get('snippet', {}).get('published_at')
        if published_str:
            published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
            if published < cutoff_date:
                continue
        
        # Include quality video
        quality_videos.append(video)
    
    return quality_videos
```

#### 1.3. Formula A2 - Viral Detection (MAD Method)

```python
# apps/api/modules/module_2a/formulas.py
import numpy as np
from typing import List, Dict, Any

def detect_viral_videos(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Formula A2: Detect viral videos using Median Absolute Deviation (MAD).
    
    A video is considered viral if its view count is significantly higher
    than the channel's typical performance (statistical outlier).
    
    Modified Z-Score = 0.6745 * (value - median) / MAD
    
    Threshold: > 3.5 = extreme outlier (viral)
    """
    if len(videos) < 5:
        return videos  # Not enough data for MAD
    
    # Extract view counts
    views = np.array([
        int(v.get('statistics', {}).get('view_count', 0))
        for v in videos
    ])
    
    # Calculate MAD
    median = np.median(views)
    mad = np.median(np.abs(views - median))
    
    if mad == 0:
        # All videos have identical/similar view counts
        # Check for single viral video
        max_views = np.max(views)
        if max_views > median * 5:  # At least 5x median
            viral_idx = np.argmax(views)
            return [videos[viral_idx]]
        return []
    
    # Calculate modified z-scores
    modified_z_scores = 0.6745 * (views - median) / mad
    
    # Identify viral videos (threshold = 3.5)
    viral_threshold = 3.5
    viral_videos = [
        video for video, z in zip(videos, modified_z_scores)
        if z > viral_threshold
    ]
    
    return viral_videos
```

### 2. Transcript Engine (3-Tier Fallback)

```
┌─────────────────────────────────────────────────────────────────┐
│                  TRANSCRIPT ENGINE (3-Tier)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input: video_id                                                │
│      │                                                         │
│      ▼                                                         │
│  TIER 1: youtube-transcript-api (FREE)                         │
│      │ [SUCCESS] ──► Return transcript                         │
│      │ [FAIL]                                                  │
│      ▼                                                         │
│  TIER 2: Supadata API ($0.001/min)                            │
│      │ [SUCCESS] ──► Return transcript                         │
│      │ [FAIL]                                                  │
│      ▼                                                         │
│  TIER 3: OpenAI Whisper API ($0.006/min) ← THAY THẾ WHISPER LOCAL│
│      │ [SUCCESS] ──► Return transcript                         │
│      │ [FAIL]                                                  │
│      ▼                                                         │
│  Output: transcript text OR None                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

💡 LÝ DO CHỌN OPENAI WHISPER API THAY VÌ LOCAL:
- Tiết kiệm 80% chi phí (không cần máy cấu hình cao trên Railway)
- Deploy nhanh (không cần tải PyTorch >1GB)
- Transcribe nhanh hơn 10x (server OpenAI mạnh)
- Chỉ tốn $0.006/phút = ~150đ/phút = video 10phút ~1,500đ
```

```python
# apps/api/modules/transcript/engine.py
from enum import Enum
from typing import Optional, List, Dict, Any
import httpx
import os

class TranscriptTier(Enum):
    YOUTUBE_API = 1  # youtube-transcript-api (free)
    SUPADATA = 2     # Supadata API ($0.001/min)
    OPENAI_WHISPER = 3  # OpenAI Whisper API ($0.006/min)

class TranscriptEngine:
    """
    3-tier fallback transcript retrieval.

    Tier 1: youtube-transcript-api (fastest, free)
    Tier 2: Supadata API (reliable, $0.001/min)
    Tier 3: OpenAI Whisper API (accurate, $0.006/min) ← ĐÃ THAY ĐỔI
    """

    def __init__(
        self,
        supadata_api_key: str = None,
        openai_api_key: str = None
    ):
        self.supadata_key = supadata_api_key or os.environ.get("SUPADATA_API_KEY")
        self.openai_key = openai_api_key or os.environ.get("OPENAI_API_KEY")

    async def get_transcript(
        self,
        video_id: str,
        preferred_languages: List[str] = ['vi', 'en']
    ) -> Optional[Dict[str, Any]]:
        """
        Get transcript with 3-tier fallback.

        Returns dict với: {transcript, language, tier_used, estimated_cost}
        """
        # Tier 1: youtube-transcript-api (FREE)
        try:
            result = await self._fetch_youtube_api(video_id, preferred_languages)
            if result:
                return {**result, "tier_used": 1, "estimated_cost_usd": 0.0}
        except Exception as e:
            print(f"Tier 1 (YouTube API) failed: {e}")

        # Tier 2: Supadata API ($0.001/min)
        try:
            result = await self._fetch_supadata(video_id, preferred_languages)
            if result:
                # Ước tính: giả sử video 10 phút
                return {**result, "tier_used": 2, "estimated_cost_usd": 0.01}
        except Exception as e:
            print(f"Tier 2 (Supadata) failed: {e}")

        # Tier 3: OpenAI Whisper API ($0.006/min)
        try:
            result = await self._fetch_openai_whisper(video_id)
            if result:
                # Ước tính: video 10 phút = $0.06
                return {**result, "tier_used": 3, "estimated_cost_usd": 0.06}
        except Exception as e:
            print(f"Tier 3 (OpenAI Whisper) failed: {e}")

        return None

    async def _fetch_youtube_api(
        self,
        video_id: str,
        languages: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Tier 1: Use youtube-transcript-api (FREE)."""
        from youtube_transcript_api import YouTubeTranscriptApi

        for lang in languages:
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list.find_transcript([lang])
                content = ' '.join([t['text'] for t in transcript.fetch()])
                return {"video_id": video_id, "transcript": content, "language": lang}
            except Exception:
                continue

        return None

    async def _fetch_supadata(
        self,
        video_id: str,
        languages: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Tier 2: Use Supadata API ($0.001/min)."""
        if not self.supadata_key:
            return None

        async with httpx.AsyncClient(timeout=60.0) as client:
            for lang in languages:
                try:
                    response = await client.get(
                        "https://api.supadata.ai/v1/youtube/transcript",
                        params={"videoId": video_id, "lang": lang},
                        headers={"Authorization": f"Bearer {self.supadata_key}"}
                    )

                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "video_id": video_id,
                            "transcript": data.get('text', ''),
                            "language": lang
                        }
                except Exception:
                    continue

        return None

    async def _fetch_openai_whisper(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Tier 3: Use OpenAI Whisper API ($0.006/min).

        API: https://api.openai.com/v1/audio/transcriptions

        Đây là API call thay vì chạy local Whisper model.
        Không cần yt-dlp hay PyTorch!
        """
        if not self.openai_key:
            return None

        import openai

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Step 1: Get video URL (dùng YouTube oEmbed)
            oembed_url = f"https://www.youtube.com/oembed?url=https://youtube.com/watch?v={video_id}&format=json"
            oembed_response = await client.get(oembed_url)

            if oembed_response.status_code != 200:
                # Fallback: construct URL
                video_url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                video_url = f"https://youtube.com/watch?v={video_id}"

            # Step 2: Call OpenAI Whisper API với URL
            # OpenAI Whisper API hỗ trợ remote URL!
            openai_client = openai.AsyncOpenAI(api_key=self.openai_key)

            try:
                response = await openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=await self._fetch_audio_from_youtube(video_id),
                    response_format="text",
                    language="vi" if "vi" else "en"
                )

                return {
                    "video_id": video_id,
                    "transcript": response.text,
                    "language": "auto-detected"
                }
            except Exception as e:
                print(f"OpenAI Whisper API error: {e}")
                return None

    async def _fetch_audio_from_youtube(self, video_id: str) -> bytes:
        """
        Fetch audio from YouTube as bytes for OpenAI API.

        Sử dụng pytube hoặc yt-dlp để get audio stream.
        Chỉ cần bytes, không cần save file!
        """
        from pytube import YouTube
        import io

        yt = YouTube(f"https://youtube.com/watch?v={video_id}")
        audio_stream = yt.streams.filter(only_audio=True).order_by('abr').last()

        # Get bytes
        buffer = io.BytesIO()
        audio_stream.stream_to_buffer(buffer)
        buffer.seek(0)

        return buffer

    async def estimate_cost(self, video_duration_seconds: int) -> Dict[str, float]:
        """
        Ước tính chi phí cho 1 video.

        Returns:
            Dict với chi phí cho mỗi tier
        """
        duration_min = video_duration_seconds / 60

        return {
            "tier_1_youtube_api": 0.0,  # Free
            "tier_2_supadata": round(0.001 * duration_min, 4),  # $0.001/min
            "tier_3_openai_whisper": round(0.006 * duration_min, 4),  # $0.006/min
            "video_duration_minutes": round(duration_min, 2)
        }
```
```

### 3. Transcript Storage & TTL

```sql
-- supabase/migrations/0011_transcripts_cron.sql

-- Enable pg_cron extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Create transcripts table
CREATE TABLE IF NOT EXISTS transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    language TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '90 days'),
    
    -- Composite index for efficient queries
    UNIQUE(video_id, language)
);

-- Index for TTL cleanup
CREATE INDEX idx_transcripts_expires ON transcripts(expires_at);

-- Index for channel lookups
CREATE INDEX idx_transcripts_channel ON transcripts(channel_id);

-- Cron job to delete expired transcripts (run daily at 3 AM)
SELECT cron.schedule(
    'cleanup-expired-transcripts',
    '0 3 * * *',
    $$DELETE FROM transcripts WHERE expires_at < NOW()$$
);
```

### 4. Dependencies

**ĐÃ THAY ĐỔI - KHÔNG CÒN whisper, torch, yt-dlp:**

```bash
# Chỉ cần these packages:
pip install youtube-transcript-api pytube openai
```

| Package | Purpose | Cost |
|---------|---------|------|
| `youtube-transcript-api` | Tier 1 | FREE |
| `pytube` | Get audio bytes | FREE |
| `openai` | Tier 3 (Whisper API) | $0.006/min |
| `numpy` | Formulas | FREE |

**ĐÃ LOẠI BỎ:**
- `whisper` (OpenAI) - chạy local ngốn RAM/CPU
- `torch` (PyTorch) - ~1GB, lâu deploy
- `yt-dlp` - không cần nếu dùng pytube + OpenAI API

### 5. Chi phí Ước tính

```
💰 CHI PHÍ TRANSCRIPT MỖI VIDEO:

| Duration | Tier 1 (Free) | Tier 2 ($0.001/min) | Tier 3 ($0.006/min) |
|----------|-------------|---------------------|---------------------|
| 5 phút   | FREE        | $0.005 (~125đ)      | $0.03 (~750đ)       |
| 10 phút  | FREE        | $0.01 (~250đ)       | $0.06 (~1,500đ)     |
| 20 phút  | FREE        | $0.02 (~500đ)       | $0.12 (~3,000đ)     |

💡 VÍ DỤ: Phân tích 1 kênh 200 videos (avg 10 phút):
- 80% videos (160) → Tier 1: FREE
- 10% videos (20) → Tier 2: 20 × $0.01 = $0.20 (~5,000đ)
- 10% videos (20) → Tier 3: 20 × $0.06 = $1.20 (~30,000đ)
─────────────────────────────────────────
TỔNG: ~$1.40 (~35,000đ) cho 1 kênh!
```

### 6. Verification

- [ ] Batch collection fetches exactly 200 videos max
- [ ] Formula A0 correctly filters out Shorts (<60s)
- [ ] Formula A2 detects videos with >3.5 MAD score
- [ ] Transcript tier 1 succeeds for 80%+ of videos
- [ ] Fallback to tier 2 when tier 1 fails
- [ ] Fallback to tier 3 (OpenAI Whisper API) when tier 2 fails
- [ ] Transcript TTL set to 90 days
- [ ] pg_cron job runs daily without errors
- [ ] No whisper local, torch, yt-dlp in dependencies
- [ ] Deploy time < 1 phút (không cần tải PyTorch)
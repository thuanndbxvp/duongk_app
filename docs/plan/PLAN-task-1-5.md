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

```python
# apps/api/modules/transcript/engine.py
from enum import Enum
from typing import Optional, List
import asyncio

class TranscriptTier(Enum):
    YOUTUBE_API = 1  # youtube-transcript-api
    SUPADATA = 2     # Supadata API
    WHISPER = 3      # yt-dlp + Whisper

class TranscriptEngine:
    """
    3-tier fallback transcript retrieval.
    
    Tier 1: youtube-transcript-api (fastest, free)
    Tier 2: Supadata API (reliable, paid)
    Tier 3: yt-dlp + Whisper (slowest, most expensive)
    """
    
    def __init__(self, supadata_api_key: str, whisper_model: str = "base"):
        self.supadata_key = supadata_api_key
        self.whisper_model = whisper_model
    
    async def get_transcript(
        self,
        video_id: str,
        preferred_languages: List[str] = ['vi', 'en']
    ) -> Optional[str]:
        """
        Get transcript with 3-tier fallback.
        
        Args:
            video_id: YouTube video ID
            preferred_languages: Preferred transcript languages (priority order)
        
        Returns:
            Transcript text or None if all tiers fail
        """
        # Tier 1: youtube-transcript-api
        try:
            transcript = await self._fetch_youtube_api(video_id, preferred_languages)
            if transcript:
                return transcript
        except Exception as e:
            print(f"Tier 1 failed: {e}")
        
        # Tier 2: Supadata API
        try:
            transcript = await self._fetch_supadata(video_id, preferred_languages)
            if transcript:
                return transcript
        except Exception as e:
            print(f"Tier 2 failed: {e}")
        
        # Tier 3: yt-dlp + Whisper
        try:
            transcript = await self._transcribe_whisper(video_id)
            if transcript:
                return transcript
        except Exception as e:
            print(f"Tier 3 failed: {e}")
        
        return None
    
    async def _fetch_youtube_api(
        self,
        video_id: str,
        languages: List[str]
    ) -> Optional[str]:
        """Tier 1: Use youtube-transcript-api."""
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Try each language
        for lang in languages:
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list.find_transcript([lang])
                return ' '.join([t['text'] for t in transcript.fetch()])
            except Exception:
                continue
        
        # Try any available transcript
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_generated_transcript(languages)
            return ' '.join([t['text'] for t in transcript.fetch()])
        except Exception:
            return None
    
    async def _fetch_supadata(
        self,
        video_id: str,
        languages: List[str]
    ) -> Optional[str]:
        """Tier 2: Use Supadata API."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            for lang in languages:
                response = await client.get(
                    "https://api.supadata.ai/v1/youtube/transcript",
                    params={
                        "videoId": video_id,
                        "lang": lang
                    },
                    headers={"Authorization": f"Bearer {self.supadata_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('text', '')
            
            return None
    
    async def _transcribe_whisper(self, video_id: str) -> Optional[str]:
        """Tier 3: Download audio and transcribe with Whisper."""
        import whisper
        import subprocess
        import tempfile
        import os
        
        # Load Whisper model (singleton)
        if not hasattr(self, '_whisper_model'):
            self._whisper_model = whisper.load_model(self.whisper_model)
        
        # Download audio with yt-dlp
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, f"{video_id}.mp3")
            
            # yt-dlp command
            cmd = [
                'yt-dlp',
                '-x',  # Extract audio
                '--audio-format', 'mp3',
                '-o', audio_path,
                f'https://youtube.com/watch?v={video_id}'
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Transcribe
            result = self._whisper_model.transcribe(audio_path)
            return result.get('text', '')
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

- `youtube-transcript-api`
- `whisper` (OpenAI)
- `yt-dlp`
- `numpy`

## 5. Verification

- [ ] Batch collection fetches exactly 200 videos max
- [ ] Formula A0 correctly filters out Shorts (<60s)
- [ ] Formula A2 detects videos with >3.5 MAD score
- [ ] Transcript tier 1 succeeds for 80%+ of videos
- [ ] Fallback to tier 2 when tier 1 fails
- [ ] Transcript TTL set to 90 days
- [ ] pg_cron job runs daily without errors
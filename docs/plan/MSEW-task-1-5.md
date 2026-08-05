# MSEW: Task 1.5 - Module 2A & Transcript Engine

> **Prerequisites:**
> - **Repomix bundle:** `.\CONTEXT_BUNDLE.md`
> - **Python venv activated:** `.\venv\Scripts\Activate.ps1`
> - **Dependencies:** `pip install youtube-transcript-api whisper yt-dlp openai-whisper`

---

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | Module 2A Package Setup | `general-purpose` | - | - |
| 2 | YouTubeCollector Service | `backend-development` | `general-purpose` | `planning` |
| 3 | API Routes (Module 2A) | `backend-development` | - | - |
| 4 | Transcript Package Setup | `general-purpose` | - | - |
| 5 | TranscriptEngine 3-Tier | `general-purpose` | `backend-development` | `planning` |
| 6 | Transcript Routes & Schemas | `backend-development` | - | - |
| 7 | pg_cron Migration | `databases` | `general-purpose` | - |
| 8 | Unit Tests | `tester` | `general-purpose` | - |

---

## Files KHÔNG được đụng (Do Not Touch)
- `supabase/migrations/0001-0010/` — Đã tạo ở Task 1.1
- `apps/api/core/` — Task 1.4 đã tạo
- `packages/shared-types/` — Models đã defined

---

## Micro-Steps

### Step 1: Tạo Module 2A Package

**File:** `apps/api/modules/module_2a/__init__.py`
**Vị trí:** Tạo file mới

**Code cần viết:**
```python
"""
Module 2A: Deep Collection.

Collects YouTube video metadata and applies filtering formulas.
"""
from apps.api.modules.module_2a.service import YouTubeCollector
from apps.api.modules.module_2a.routes import router

__all__ = ["YouTubeCollector", "router"]
```

---

### Step 2: Tạo YouTubeCollector Service

**File:** `apps/api/modules/module_2a/service.py`
**Vị trí:** Tạo file mới

**Import cần thêm:**
```python
import os
import asyncio
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from apps.api.modules.module_1.formulas import filter_quality_videos, detect_viral_videos
```

**Code cần viết:**
```python
"""
Module 2A - YouTubeCollector Service.
Collects video metadata from YouTube channels.
"""
import os
import asyncio
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeCollector:
    """Service for collecting YouTube video metadata."""
    
    BATCH_SIZE = 50  # YouTube API max videos per request
    MAX_VIDEOS = 200  # Max videos per channel
    MAX_CONCURRENT = 4  # Max concurrent API calls
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("YOUTUBE_API_KEY_1")
        self._client = None
    
    async def get_client(self):
        """Lazy initialization of YouTube client."""
        if self._client is None:
            self._client = build('youtube', 'v3', developerKey=self.api_key)
        return self._client
    
    async def collect_channel_videos(
        self,
        channel_id: str,
        max_videos: int = MAX_VIDEOS
    ) -> Dict[str, Any]:
        """
        Collect videos from a YouTube channel.
        
        Args:
            channel_id: YouTube channel ID
            max_videos: Maximum number of videos to collect
        
        Returns:
            Dict with all_videos, quality_videos, viral_videos
        """
        # Step 1: Get video IDs
        video_ids = await self._get_channel_video_ids(channel_id, max_videos)
        
        # Step 2: Batch into groups of 50
        batches = [
            video_ids[i:i + self.BATCH_SIZE]
            for i in range(0, len(video_ids), self.BATCH_SIZE)
        ]
        
        # Step 3: Fetch metadata in parallel (max 4 concurrent)
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
        
        async def fetch_batch(batch_ids: List[str]) -> List[Dict[str, Any]]:
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
            "channel_id": channel_id,
            "total_videos_collected": len(all_videos),
            "quality_videos_count": len(quality_videos),
            "viral_videos_count": len(viral_videos),
            "all_videos": all_videos,
            "quality_videos": quality_videos,
            "viral_videos": viral_videos
        }
    
    async def _get_channel_video_ids(
        self,
        channel_id: str,
        max_videos: int
    ) -> List[str]:
        """Get video IDs from a channel using search."""
        client = await self.get_client()
        video_ids = []
        next_page_token = None
        
        while len(video_ids) < max_videos:
            remaining = max_videos - len(video_ids)
            
            try:
                # Use search to get videos (sorted by date)
                response = await asyncio.to_thread(
                    client.search().list(
                        part='id',
                        channelId=channel_id,
                        type='video',
                        order='date',
                        maxResults=min(50, remaining),
                        pageToken=next_page_token
                    ).execute
                )
                
                for item in response.get('items', []):
                    if item['id']['kind'] == 'youtube#video':
                        video_ids.append(item['id']['videoId'])
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except HttpError as e:
                print(f"YouTube API error: {e}")
                break
            except Exception as e:
                print(f"Error getting video IDs: {e}")
                break
        
        return video_ids
    
    async def _fetch_video_metadata(
        self,
        video_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Fetch metadata for a batch of videos."""
        client = await self.get_client()
        
        try:
            response = await asyncio.to_thread(
                client.videos().list(
                    part='snippet,contentDetails,statistics',
                    id=','.join(video_ids)
                ).execute
            )
            
            return response.get('items', [])
            
        except HttpError as e:
            print(f"YouTube API error: {e}")
            return []
        except Exception as e:
            print(f"Error fetching metadata: {e}")
            return []
```

**Verify command (PowerShell):**
```powershell
python -c "from apps.api.modules.module_2a.service import YouTubeCollector; print('OK')"
```

**Expected output:**
```
OK
```

---

### Step 3: Tạo Module 2A Schemas

**File:** `apps/api/modules/module_2a/schemas.py`
**Vị trí:** Tạo file mới

**Code cần viết:**
```python
"""
Module 2A Pydantic Schemas.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class VideoMetadata(BaseModel):
    """Video metadata schema."""
    video_id: str
    title: Optional[str] = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    duration_seconds: int = 0
    published_at: Optional[str] = None


class ChannelCollectionRequest(BaseModel):
    """Request to collect channel videos."""
    channel_id: str = Field(..., description="YouTube channel ID")
    max_videos: int = Field(default=200, ge=1, le=200)


class ChannelCollectionResponse(BaseModel):
    """Response for channel collection."""
    channel_id: str
    total_videos_collected: int
    quality_videos_count: int
    viral_videos_count: int
    quality_videos: List[VideoMetadata]
    viral_videos: List[VideoMetadata]
```

---

### Step 4: Tạo Module 2A Routes

**File:** `apps/api/modules/module_2a/routes.py`
**Vị trí:** Tạo file mới

**Code cần viết:**
```python
"""
Module 2A API Routes - Deep Collection.
"""
from fastapi import APIRouter, HTTPException, Depends
from apps.api.modules.module_2a.schemas import (
    ChannelCollectionRequest,
    ChannelCollectionResponse,
    HealthResponse
)
from apps.api.modules.module_2a.service import YouTubeCollector


router = APIRouter(prefix="/api/collect", tags=["Module 2A - Deep Collection"])


def get_collector() -> YouTubeCollector:
    """Get YouTubeCollector instance."""
    return YouTubeCollector()


@router.post("/channel", response_model=ChannelCollectionResponse)
async def collect_channel_videos(
    request: ChannelCollectionRequest,
    collector: YouTubeCollector = Depends(get_collector)
):
    """
    Collect videos from a YouTube channel.
    
    - Fetches up to max_videos (default 200)
    - Filters out Shorts, Live streams, low-engagement videos
    - Detects viral videos using MAD algorithm
    """
    try:
        result = await collector.collect_channel_videos(
            channel_id=request.channel_id,
            max_videos=request.max_videos
        )
        
        # Convert to response schema
        from apps.api.modules.module_2a.schemas import VideoMetadata
        
        quality_videos = [
            VideoMetadata(
                video_id=v['id'],
                title=v.get('snippet', {}).get('title'),
                views=int(v.get('statistics', {}).get('viewCount', 0)),
                likes=int(v.get('statistics', {}).get('likeCount', 0)),
                comments=int(v.get('statistics', {}).get('commentCount', 0)),
                duration_seconds=_parse_duration(v.get('contentDetails', {}).get('duration', 'PT0S')),
                published_at=v.get('snippet', {}).get('publishedAt')
            )
            for v in result['quality_videos']
        ]
        
        viral_videos = [
            VideoMetadata(
                video_id=v['id'],
                title=v.get('snippet', {}).get('title'),
                views=int(v.get('statistics', {}).get('viewCount', 0)),
                likes=int(v.get('statistics', {}).get('likeCount', 0)),
                comments=int(v.get('statistics', {}).get('commentCount', 0)),
                duration_seconds=_parse_duration(v.get('contentDetails', {}).get('duration', 'PT0S')),
                published_at=v.get('snippet', {}).get('publishedAt')
            )
            for v in result['viral_videos']
        ]
        
        return ChannelCollectionResponse(
            channel_id=result['channel_id'],
            total_videos_collected=result['total_videos_collected'],
            quality_videos_count=result['quality_videos_count'],
            viral_videos_count=result['viral_videos_count'],
            quality_videos=quality_videos,
            viral_videos=viral_videos
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection failed: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check for Module 2A."""
    return HealthResponse(
        status="healthy",
        module="deep_collection",
        version="1.0.0"
    )


def _parse_duration(duration: str) -> int:
    """Parse ISO 8601 duration to seconds."""
    import re
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds
```

---

### Step 5: Tạo Transcript Package

**File:** `apps/api/modules/transcript/__init__.py`
**Vị trí:** Tạo file mới

**Code cần viết:**
```python
"""
Transcript Engine - 3-Tier Fallback.

Tier 1: youtube-transcript-api (FREE)
Tier 2: Supadata API ($0.001/min)
Tier 3: OpenAI Whisper API ($0.006/min) ← ĐÃ THAY ĐỔI
"""
from apps.api.modules.transcript.engine import TranscriptEngine, TranscriptTier

__all__ = ["TranscriptEngine", "TranscriptTier"]
```

---

### Step 6: Tạo TranscriptEngine 3-Tier (OpenAI Whisper API)

**File:** `apps/api/modules/transcript/engine.py`
**Vị trí:** Tạo file mới

**Code cần viết:**
```python
"""
Transcript Engine - 3-Tier Fallback Strategy.

Tier 1: youtube-transcript-api (FREE)
Tier 2: Supadata API ($0.001/min)
Tier 3: OpenAI Whisper API ($0.006/min) ← ĐÃ THAY ĐỔI
"""
import os
import io
from enum import Enum
from typing import Optional, List, Dict, Any
import httpx
import openai


class TranscriptTier(Enum):
    YOUTUBE_API = 1      # youtube-transcript-api (FREE)
    SUPADATA = 2         # Supadata API ($0.001/min)
    OPENAI_WHISPER = 3   # OpenAI Whisper API ($0.006/min)


class TranscriptEngine:
    """
    3-tier fallback transcript retrieval.

    Tier 1: youtube-transcript-api (fastest, free)
    Tier 2: Supadata API ($0.001/min)
    Tier 3: OpenAI Whisper API ($0.006/min) ← ĐÃ THAY ĐỔI
    """

    def __init__(
        self,
        supadata_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        self.supadata_key = supadata_api_key or os.environ.get("SUPADATA_API_KEY")
        self.openai_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self._openai_client = None

    async def get_transcript(
        self,
        video_id: str,
        preferred_languages: List[str] = ['vi', 'en']
    ) -> Optional[Dict[str, Any]]:
        """
        Get transcript with 3-tier fallback.
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
                return {**result, "tier_used": 2, "estimated_cost_usd": 0.01}
        except Exception as e:
            print(f"Tier 2 (Supadata) failed: {e}")

        # Tier 3: OpenAI Whisper API ($0.006/min)
        try:
            result = await self._fetch_openai_whisper(video_id)
            if result:
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

        async with httpx.AsyncClient(timeout=30.0) as client:
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

        KHÔNG cần chạy Whisper local!
        Chỉ cần gọi OpenAI API.
        """
        if not self.openai_key:
            return None

        # Get audio bytes from YouTube
        audio_bytes = await self._get_audio_bytes(video_id)
        if not audio_bytes:
            return None

        # Initialize OpenAI client
        if self._openai_client is None:
            self._openai_client = openai.AsyncOpenAI(api_key=self.openai_key)

        # Create file-like object
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = f"{video_id}.mp3"

        try:
            response = await self._openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )

            return {
                "video_id": video_id,
                "transcript": response.text,
                "language": "auto"
            }
        except Exception as e:
            print(f"OpenAI Whisper API error: {e}")
            return None

    async def _get_audio_bytes(self, video_id: str) -> Optional[bytes]:
        """
        Get audio from YouTube as bytes.
        """
        from pytube import YouTube

        try:
            yt = YouTube(f"https://youtube.com/watch?v={video_id}")
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').last()

            buffer = io.BytesIO()
            audio_stream.stream_to_buffer(buffer)
            buffer.seek(0)

            return buffer.getvalue()
        except Exception as e:
            print(f"Error fetching audio: {e}")
            return None
```

---

### Step 7: Tạo Transcript Routes

**File:** `apps/api/modules/transcript/routes.py`
**Vị trí:** Tạo file mới

**Code cần viết:**
```python
"""
Transcript API Routes.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from apps.api.modules.transcript.engine import TranscriptEngine


router = APIRouter(prefix="/api/transcript", tags=["Transcript Engine"])


def get_engine() -> TranscriptEngine:
    """Get TranscriptEngine instance."""
    return TranscriptEngine()


class TranscriptRequest(BaseModel):
    video_id: str = Field(..., description="YouTube video ID")
    languages: List[str] = Field(default=['vi', 'en'], description="Preferred languages")


class TranscriptResponse(BaseModel):
    video_id: str
    transcript: str
    language: str
    tier_used: int
    cached: bool


class HealthResponse(BaseModel):
    status: str
    module: str
    version: str


@router.post("/", response_model=TranscriptResponse)
async def get_transcript(
    request: TranscriptRequest,
    engine: TranscriptEngine = Depends(get_engine)
):
    """
    Get transcript for a YouTube video using 3-tier fallback.
    
    Tier 1: youtube-transcript-api (fastest, free)
    Tier 2: Supadata API (reliable, paid)
    Tier 3: yt-dlp + Whisper (slowest, most expensive)
    """
    try:
        result = await engine.get_transcript(
            video_id=request.video_id,
            preferred_languages=request.languages
        )
        
        if result:
            return TranscriptResponse(**result)
        else:
            raise HTTPException(
                status_code=404,
                detail="Transcript not available for this video"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcript fetch failed: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check for Transcript Engine."""
    return HealthResponse(
        status="healthy",
        module="transcript_engine",
        version="1.0.0"
    )
```

---

### Step 7: Dependencies (ĐÃ THAY ĐỔI - KHÔNG còn whisper local)

```bash
pip install youtube-transcript-api pytube openai
```

| Package | Purpose | Status |
|---------|---------|--------|
| `youtube-transcript-api` | Tier 1 (FREE) | ✅ Keep |
| `pytube` | Get audio bytes | ✅ Add |
| `openai` | Tier 3 (Whisper API) | ✅ Add |
| ~~`whisper`~~ | Local transcription | ❌ REMOVE |
| ~~`torch`~~ | PyTorch (1GB) | ❌ REMOVE |
| ~~`yt-dlp`~~ | Audio download | ❌ REMOVE |

---

### Step 8: Tạo pg_cron Migration

**File:** `supabase/migrations/0011_transcripts_cron.sql`
**Vị trí:** Tạo file mới

**Code cần viết:**
```sql
-- Migration: 0011_transcripts_cron
-- Description: Create transcripts table and setup pg_cron cleanup

-- Enable pg_cron extension (must be superuser)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Grant pg_cron permissions if needed
-- GRANT USAGE ON SCHEMA cron TO your_service_role;

-- Create transcripts table
CREATE TABLE IF NOT EXISTS transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    language TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '90 days'),
    
    -- Composite unique constraint
    UNIQUE(video_id, language)
);

-- Index for TTL cleanup (expired transcripts)
CREATE INDEX IF NOT EXISTS idx_transcripts_expires 
    ON transcripts(expires_at);

-- Index for channel lookups
CREATE INDEX IF NOT EXISTS idx_transcripts_channel 
    ON transcripts(channel_id);

-- Index for video lookups
CREATE INDEX IF NOT EXISTS idx_transcripts_video 
    ON transcripts(video_id);

-- Schedule cron job to delete expired transcripts (run daily at 3 AM)
-- This ensures ToS compliance by removing data older than 90 days
SELECT cron.schedule(
    'cleanup-expired-transcripts',
    '0 3 * * *',
    $$DELETE FROM transcripts WHERE expires_at < NOW()$$
);

-- Optional: Unschedule job (for testing)
-- SELECT cron.unschedule('cleanup-expired-transcripts');
```

**Verify command (PowerShell):**
```powershell
psql -h localhost -U postgres -d appdk -c "SELECT * FROM cron.job WHERE jobname = 'cleanup-expired-transcripts';"
```

**Expected output:**
```
 jobid | schedule   | command                                      | nodename  | database | owner  | active | jobname
-------+------------+----------------------------------------------+-----------+----------+--------+--------+---------------------------
     1 | 0 3 * * *  | DELETE FROM transcripts WHERE expires_at... | localhost | appdk    | ...    | t      | cleanup-expired-transcripts
```

---

### Step 9: Tạo Test Files

**File:** `tests/test_module_2a/__init__.py`
```python
"""Test suite for Module 2A."""
```

**File:** `tests/test_module_2a/test_service.py`
```python
"""
Unit tests for Module 2A YouTubeCollector.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from apps.api.modules.module_2a.service import YouTubeCollector


class TestYouTubeCollector:
    """Tests for YouTubeCollector service."""
    
    @pytest.fixture
    def collector(self):
        return YouTubeCollector(api_key="test_key")
    
    def test_initialization(self, collector):
        """Test collector initialization."""
        assert collector.api_key == "test_key"
        assert collector.BATCH_SIZE == 50
        assert collector.MAX_VIDEOS == 200
    
    @pytest.mark.asyncio
    async def test_collect_channel_videos(self, collector):
        """Test video collection from channel."""
        # Mock YouTube API responses
        with patch.object(collector, '_get_channel_video_ids', new_callable=AsyncMock) as mock_ids, \
             patch.object(collector, '_fetch_video_metadata', new_callable=AsyncMock) as mock_meta:
            
            mock_ids.return_value = ['video1', 'video2']
            mock_meta.return_value = [
                {
                    'id': 'video1',
                    'snippet': {'title': 'Test', 'publishedAt': '2024-01-01T00:00:00Z'},
                    'contentDetails': {'duration': 'PT10M'},
                    'statistics': {'viewCount': '50000'}
                }
            ]
            
            result = await collector.collect_channel_videos('channel123')
            
            assert result['channel_id'] == 'channel123'
            assert 'quality_videos' in result
            assert 'viral_videos' in result
```

---

**File:** `tests/test_transcript/__init__.py`
```python
"""Test suite for Transcript Engine."""
```

**File:** `tests/test_transcript/test_engine.py`
```python
"""
Unit tests for Transcript Engine.
"""
import pytest
from unittest.mock import patch, AsyncMock
from apps.api.modules.transcript.engine import TranscriptEngine, TranscriptTier


class TestTranscriptEngine:
    """Tests for TranscriptEngine."""
    
    @pytest.fixture
    def engine(self):
        return TranscriptEngine(supadata_api_key="test_key")
    
    def test_initialization(self, engine):
        """Test engine initialization."""
        assert engine.supadata_key == "test_key"
        assert engine.whisper_model == "base"
    
    @pytest.mark.asyncio
    async def test_get_transcript_tier1_success(self, engine):
        """Test successful Tier 1 transcript fetch."""
        with patch.object(engine, '_fetch_youtube_api', new_callable=AsyncMock) as mock:
            mock.return_value = {
                'video_id': 'test123',
                'transcript': 'Test transcript content',
                'language': 'vi'
            }
            
            result = await engine.get_transcript('test123')
            
            assert result is not None
            assert result['tier_used'] == 1
            assert result['transcript'] == 'Test transcript content'
    
    @pytest.mark.asyncio
    async def test_get_transcript_all_tiers_fail(self, engine):
        """Test when all tiers fail."""
        with patch.object(engine, '_fetch_youtube_api', new_callable=AsyncMock) as mock1, \
             patch.object(engine, '_fetch_supadata', new_callable=AsyncMock) as mock2, \
             patch.object(engine, '_transcribe_whisper', new_callable=AsyncMock) as mock3:
            
            mock1.return_value = None
            mock2.return_value = None
            mock3.side_effect = Exception("Whisper failed")
            
            result = await engine.get_transcript('test123')
            
            assert result is None
```

---

**Verify command (PowerShell):**
```powershell
pytest tests/test_module_2a/ tests/test_transcript/ -v
```

**Expected output:**
```
tests/test_module_2a/test_service.py::TestYouTubeCollector::test_initialization PASSED
tests/test_module_2a/test_service.py::TestYouTubeCollector::test_collect_channel_videos PASSED
tests/test_transcript/test_engine.py::TestTranscriptEngine::test_initialization PASSED
tests/test_transcript/test_engine.py::TestTranscriptEngine::test_get_transcript_tier1_success PASSED
tests/test_transcript/test_engine.py::TestTranscriptEngine::test_get_transcript_all_tiers_fail PASSED

========================= 5 passed in 1.5s =========================
```

---

**Nếu fail:** 
- Invoke skill `debugging`.
- Báo cáo vào file `BLOCKERS.md`.
- **CẤM TỰ SỬA CODE KHÁC.**

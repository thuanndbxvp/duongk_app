# Quy trình thực thi chi tiết (MSEW): Task 1.5 - Triển khai Module 2A & Transcript Engine

## BƯỚC 1: Lọc Video & MAD
Code chuẩn theo Formula A0 (loại Shorts < 60s) và A2 (Median Absolute Deviation):
```python
import numpy as np

def flag_viral_videos(videos: list[dict]):
    views = [v['viewCount'] for v in videos if v['duration_sec'] >= 60]
    median = np.median(views)
    mad = np.median([abs(v - median) for v in views])
    for v in videos:
        v['is_viral'] = v['viewCount'] > (median + 2*mad)
```

## BƯỚC 2: Transcript 3-Tier Fallback
```python
from youtube_transcript_api import YouTubeTranscriptApi

async def get_transcript(video_id: str):
    # Tier 1
    try:
        return YouTubeTranscriptApi.get_transcript(video_id, languages=['vi', 'en'])
    except Exception:
        pass
    
    # Tier 2: Supadata API (mock for now)
    # Tier 3: yt-dlp + whisper (celery task fallback)
    return None
```

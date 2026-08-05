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

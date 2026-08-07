"""
Celery Task: Scrape YouTube Channel
Tier 1 P0 — Channel Collector feature

Task này scrape YouTube channel và lưu recent videos vào collector_channels.
"""
from __future__ import annotations
import re
import uuid
import logging
from datetime import datetime
from celery import Task
from celery_app import celery_app


@celery_app.task(
    bind=True,
    name='apps.worker.tasks.scrape_channel.scrape_channel_task',
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def scrape_channel_task(
    self: Task,
    job_id: str,
    channel_id: str,
    user_id: str,
) -> dict:
    """
    Scrape recent videos from a YouTube channel.
    
    Args:
        job_id: UUID of collector_scrape_jobs record
        channel_id: UUID of collector_channels record
        user_id: User ID for ownership verification
        
    Returns:
        {
            "videos_found": int,
            "status": str,
        }
    """
    import httpx
    import os
    from apps.api.dependencies.supabase import get_supabase_admin
    
    logger = logging.getLogger(__name__)
    logger.info(f"[scrape_channel] Starting job={job_id}, channel={channel_id}")
    
    admin = get_supabase_admin()
    
    try:
        # Update job status to running
        admin.rpc('update_scrape_job_status', {
            'p_job_id': job_id,
            'p_status': 'running',
        }).execute()
        
        # Get channel info
        channel_res = admin.table('collector_channels').select('*').eq('id', channel_id).execute()
        if not channel_res.data:
            raise ValueError(f"Channel not found: {channel_id}")
        
        channel = channel_res.data[0]
        channel_url = channel['url']
        
        # Extract channel identifier
        channel_identifier = _extract_channel_id(channel_url)
        if not channel_identifier:
            raise ValueError(f"Invalid YouTube URL: {channel_url}")
        
        # Scrape YouTube channel
        videos = _scrape_youtube_channel(channel_identifier)
        
        # Update channel with new data
        admin.table('collector_channels').update({
            'recent_videos': videos,
            'video_count': len(videos),
            'last_scraped_at': datetime.utcnow().isoformat(),
            'status': 'active',
        }).eq('id', channel_id).execute()
        
        # Update job status to completed
        admin.rpc('update_scrape_job_status', {
            'p_job_id': job_id,
            'p_status': 'completed',
            'p_videos_found': len(videos),
        }).execute()
        
        logger.info(f"[scrape_channel] Success: {len(videos)} videos")
        
        return {
            "videos_found": len(videos),
            "status": "completed",
        }
        
    except Exception as e:
        logger.error(f"[scrape_channel] Failed: {e}")
        
        # Update job status to failed
        try:
            admin.rpc('update_scrape_job_status', {
                'p_job_id': job_id,
                'p_status': 'failed',
                'p_error_message': str(e),
            }).execute()
        except Exception:
            pass
        
        raise


def _extract_channel_id(url: str) -> str:
    """Extract YouTube channel ID/handle from URL."""
    patterns = [
        r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
        r'youtube\.com/@([a-zA-Z0-9_-]+)',
        r'youtube\.com/c/([a-zA-Z0-9_-]+)',
        r'youtu\.be/(@[a-zA-Z0-9_-]+)',
        r'^([a-zA-Z0-9_-]+)$',  # Already a channel ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def _scrape_youtube_channel(channel_identifier: str) -> list:
    """
    Scrape recent videos from YouTube channel.
    Uses YouTube Data API v3 if available, otherwise web scraping.
    """
    import httpx
    import os
    import time
    
    api_key = os.getenv('YOUTUBE_DATA_API_KEY', '')
    videos = []
    
    if api_key:
        # Use YouTube Data API v3
        videos = _scrape_via_api(api_key, channel_identifier)
    else:
        # Fallback: Web scraping (less reliable)
        videos = _scrape_via_web(channel_identifier)
    
    return videos


def _scrape_via_api(api_key: str, channel_identifier: str) -> list:
    """Scrape using YouTube Data API v3."""
    import httpx
    
    videos = []
    
    try:
        # First, get channel ID if we have a handle
        if '@' in channel_identifier:
            channel_url = f"https://www.googleapis.com/youtube/v3/channels?part=id&forHandle={channel_identifier}&key={api_key}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(channel_url)
                data = resp.json()
                items = data.get('items', [])
                if items:
                    channel_id = items[0]['id']
                else:
                    return []
        else:
            channel_id = channel_identifier
        
        # Get recent uploads playlist
        channel_url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails& id={channel_id}&key={api_key}"
        
        with httpx.SyncClient() as client:
            resp = client.get(channel_url)
            data = resp.json()
            items = data.get('items', [])
            
            if not items:
                return []
            
            uploads_playlist_id = items[0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get playlist items (recent videos)
            playlist_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_playlist_id}&maxResults=20&key={api_key}"
            resp = client.get(playlist_url)
            data = resp.json()
            
            for item in data.get('items', []):
                snippet = item.get('snippet', {})
                videos.append({
                    'id': snippet.get('resourceId', {}).get('videoId', ''),
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', '')[:200],
                    'published_at': snippet.get('publishedAt', ''),
                    'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                })
                
    except Exception as e:
        pass
    
    return videos


def _scrape_via_web(channel_identifier: str) -> list:
    """Fallback: Web scraping YouTube channel page."""
    import httpx
    import re
    from datetime import datetime
    
    videos = []
    
    try:
        # Normalize URL
        if '@' in channel_identifier:
            url = f"https://www.youtube.com/{channel_identifier}/videos"
        else:
            url = f"https://www.youtube.com/channel/{channel_identifier}/videos"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        with httpx.SyncClient() as client:
            resp = client.get(url, headers=headers, timeout=30)
            
            # Extract video data from page
            # Simple regex for demonstration - in production use ytInitialData parsing
            video_pattern = r'"videoId":"([^"]+)","title":"([^"]+)","descriptionSnip'
            matches = re.findall(video_pattern, resp.text)
            
            for i, (video_id, title) in enumerate(matches[:20]):
                videos.append({
                    'id': video_id,
                    'title': title.encode().decode('unicode_escape'),
                    'description': '',
                    'published_at': datetime.utcnow().isoformat(),
                    'thumbnail': f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
                })
                
    except Exception as e:
        pass
    
    return videos

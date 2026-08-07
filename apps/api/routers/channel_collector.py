"""
Channel Collector API — Tier 1 Fix for P0 Drift.
Allows users to track YouTube channels and scrape their content.
Prefix: /api/channel-collector
"""
from __future__ import annotations
from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin


router = APIRouter(prefix="/api/channel-collector", tags=["Channel Collector"])


# =============================================================================
# Schemas
# =============================================================================

class ChannelResponse(BaseModel):
    """Channel data shape matching frontend expectations."""
    id: str
    name: Optional[str] = None
    url: str
    thumbnail_url: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    recent_videos: list = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ChannelListResponse(BaseModel):
    """List of channels."""
    channels: list[ChannelResponse]


class ChannelCreateRequest(BaseModel):
    """Request to add a new channel."""
    url: str
    name: Optional[str] = None


class ChannelCreateResponse(BaseModel):
    """Response after creating a channel."""
    id: str
    name: str
    url: str


class ScrapeJobResponse(BaseModel):
    """Scrape job data."""
    id: str
    channel_id: str
    status: str
    videos_found: int = 0
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class ScrapeJobListResponse(BaseModel):
    """List of scrape jobs."""
    jobs: list[ScrapeJobResponse]


class ScrapeRequest(BaseModel):
    """Request to trigger a new scrape."""
    channel_id: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================

def _parse_youtube_channel_id(url: str) -> Optional[str]:
    """Extract channel ID/handle from YouTube URL."""
    import re
    
    # Handle various YouTube URL formats
    patterns = [
        r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
        r'youtube\.com/@([a-zA-Z0-9_-]+)',
        r'youtube\.com/c/([a-zA-Z0-9_-]+)',
        r'youtu\.be/(@[a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


# =============================================================================
# Channel Endpoints
# =============================================================================

@router.get("/channels", response_model=ChannelListResponse)
async def list_channels(user_id: str = Depends(get_supabase_user)):
    """
    List all tracked channels for current user.
    GET /api/channel-collector/channels
    """
    db = get_supabase_admin()
    
    try:
        result = db.table('collector_channels').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        
        channels = []
        for row in (result.data or []):
            channels.append(ChannelResponse(
                id=row.get('id', ''),
                name=row.get('name'),
                url=row.get('url', ''),
                thumbnail_url=row.get('thumbnail_url'),
                subscriber_count=row.get('subscriber_count'),
                video_count=row.get('video_count'),
                recent_videos=row.get('recent_videos') or [],
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at'),
            ))
        
        return ChannelListResponse(channels=channels)
    except Exception as e:
        # Table might not exist — return empty
        return ChannelListResponse(channels=[])


@router.post("/channels", response_model=ChannelCreateResponse, status_code=201)
async def create_channel(
    req: ChannelCreateRequest,
    user_id: str = Depends(get_supabase_user),
):
    """
    Add a new YouTube channel to track.
    POST /api/channel-collector/channels
    """
    db = get_supabase_admin()
    
    # Validate URL
    if not req.url or 'youtube.com' not in req.url.lower():
        raise HTTPException(400, "Invalid YouTube channel URL")
    
    # Check if already tracked
    existing = db.table('collector_channels').select('id').eq('url', req.url).eq('user_id', user_id).maybe_single().execute()
    if existing.data:
        raise HTTPException(400, "Channel already tracked")
    
    # Extract channel identifier
    channel_id = _parse_youtube_channel_id(req.url)
    
    # Build channel data
    channel_data = {
        'user_id': user_id,
        'url': req.url,
        'name': req.name or f"Channel {channel_id or 'Unknown'}",
        'channel_identifier': channel_id,
        'status': 'active',
    }
    
    try:
        result = db.table('collector_channels').insert(channel_data).execute()
        
        if not result.data:
            raise HTTPException(500, "Failed to create channel")
        
        row = result.data[0]
        
        # Trigger initial scrape via Celery
        try:
            from apps.worker.tasks.scrape_channel import scrape_channel_task
            scrape_channel_task.delay(
                job_id=result.data[0]['id'],
                channel_id=row['id'],
                user_id=user_id,
            )
        except Exception:
            pass  # Celery may not be available

        return ChannelCreateResponse(
            id=row['id'],
            name=row.get('name', ''),
            url=row.get('url', ''),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@router.get("/channels/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    """
    Get a single channel by ID.
    GET /api/channel-collector/channels/{channel_id}
    """
    db = get_supabase_admin()
    
    result = db.table('collector_channels').select('*').eq('id', str(channel_id)).eq('user_id', user_id).maybe_single().execute()
    
    if not result.data:
        raise HTTPException(404, "Channel not found")
    
    row = result.data
    return ChannelResponse(
        id=row.get('id', ''),
        name=row.get('name'),
        url=row.get('url', ''),
        thumbnail_url=row.get('thumbnail_url'),
        subscriber_count=row.get('subscriber_count'),
        video_count=row.get('video_count'),
        recent_videos=row.get('recent_videos') or [],
        created_at=row.get('created_at'),
        updated_at=row.get('updated_at'),
    )


@router.delete("/channels/{channel_id}", status_code=204)
async def delete_channel(
    channel_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    """
    Delete a tracked channel.
    DELETE /api/channel-collector/channels/{channel_id}
    """
    db = get_supabase_admin()
    
    # Verify ownership
    result = db.table('collector_channels').select('id').eq('id', str(channel_id)).eq('user_id', user_id).maybe_single().execute()
    
    if not result.data:
        raise HTTPException(404, "Channel not found")
    
    # Delete channel and related jobs
    db.table('collector_scrape_jobs').delete().eq('channel_id', str(channel_id)).execute()
    db.table('collector_channels').delete().eq('id', str(channel_id)).execute()
    
    return None


# =============================================================================
# Scrape Job Endpoints
# =============================================================================

@router.get("/jobs", response_model=ScrapeJobListResponse)
async def list_scrape_jobs(
    limit: int = 20,
    user_id: str = Depends(get_supabase_user),
):
    """
    List recent scrape jobs.
    GET /api/channel-collector/jobs
    """
    db = get_supabase_admin()
    
    try:
        # Get jobs for user's channels
        result = db.table('collector_scrape_jobs').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
        
        jobs = []
        for row in (result.data or []):
            jobs.append(ScrapeJobResponse(
                id=row.get('id', ''),
                channel_id=row.get('channel_id', ''),
                status=row.get('status', 'pending'),
                videos_found=row.get('videos_found', 0),
                created_at=row.get('created_at'),
                completed_at=row.get('completed_at'),
                error_message=row.get('error_message'),
            ))
        
        return ScrapeJobListResponse(jobs=jobs)
    except Exception as e:
        # Table might not exist — return empty
        return ScrapeJobListResponse(jobs=[])


@router.post("/scrape", response_model=ScrapeJobResponse, status_code=201)
async def trigger_scrape(
    req: ScrapeRequest,
    user_id: str = Depends(get_supabase_user),
):
    """
    Trigger a new scrape job for a channel.
    POST /api/channel-collector/scrape
    
    Body: { "channel_id": "uuid" }
    """
    db = get_supabase_admin()
    
    if not req.channel_id:
        raise HTTPException(400, "channel_id is required")
    
    # Verify channel ownership
    channel = db.table('collector_channels').select('id, name').eq('id', req.channel_id).eq('user_id', user_id).maybe_single().execute()
    
    if not channel.data:
        raise HTTPException(404, "Channel not found")
    
    # Create scrape job
    job_data = {
        'channel_id': req.channel_id,
        'user_id': user_id,
        'status': 'pending',
        'videos_found': 0,
    }
    
    try:
        result = db.table('collector_scrape_jobs').insert(job_data).execute()
        
        if not result.data:
            raise HTTPException(500, "Failed to create scrape job")
        
        row = result.data[0]

        # Trigger Celery task for actual scraping
        try:
            from apps.worker.tasks.scrape_channel import scrape_channel_task
            scrape_channel_task.delay(
                job_id=row['id'],
                channel_id=req.channel_id,
                user_id=user_id,
            )
        except Exception as e:
            # If Celery not available, the task will be picked up later
            import logging
            logging.warning(f"[channel_collector] Celery trigger failed: {e}")

        return ScrapeJobResponse(
            id=row['id'],
            channel_id=row['channel_id'],
            status='pending',
            videos_found=0,
            created_at=row.get('created_at'),
            completed_at=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


# =============================================================================
# Internal Helpers
# =============================================================================

def _trigger_scrape(db, channel_id: str, user_id: str = None):
    """Trigger initial scrape when channel is added."""
    if not user_id:
        try:
            ch = db.table('collector_channels').select('user_id').eq('id', channel_id).maybe_single().execute()
            user_id = ch.data.get('user_id', '') if ch.data else ''
        except Exception:
            user_id = ''
    
    try:
        job_data = {
            'channel_id': channel_id,
            'user_id': user_id,
            'status': 'pending',
            'videos_found': 0,
        }
        result = db.table('collector_scrape_jobs').insert(job_data).execute()
        
        if result.data:
            job_id = result.data[0]['id']
            # Trigger Celery task
            try:
                from apps.worker.tasks.scrape_channel import scrape_channel_task
                scrape_channel_task.delay(
                    job_id=job_id,
                    channel_id=channel_id,
                    user_id=user_id,
                )
            except Exception:
                pass  # Celery may not be available
                
    except Exception:
        pass  # Ignore if table doesn't exist

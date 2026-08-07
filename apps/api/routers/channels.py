"""
Routers cho Channel Collection.
FIXED: No Celery imports - using FastAPI BackgroundTasks
Mounted dưới /api/channels.
"""
from __future__ import annotations
import uuid
import re

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin


router = APIRouter(prefix="/api/channels", tags=["Channels"])


# =============================================================================
# Async Task (Background)
# =============================================================================

async def _collect_channel_async(assistant_id: str, channel_id: str, user_id: str):
    """
    Async task to collect channel videos.
    Called by BackgroundTasks - no Celery needed.
    """
    db = get_supabase_admin()
    
    try:
        db.table('channel_assistants').update({
            'status': 'collecting',
        }).eq('id', assistant_id).execute()
        
        # Placeholder: implement actual channel collection
        # For now, just mark as ready
        
        db.table('channel_assistants').update({
            'status': 'ready',
        }).eq('id', assistant_id).execute()
        
    except Exception as e:
        import logging
        logging.error(f"[channels] Collection failed for {assistant_id}: {e}")
        
        db.table('channel_assistants').update({
            'status': 'failed',
        }).eq('id', assistant_id).execute()


# =============================================================================
# Schemas & Routes
# =============================================================================

class CollectChannelRequest(BaseModel):
    youtube_url: str = Field(..., description="URL hoặc channel ID")


def parse_channel_id(url: str) -> str:
    """Parse channel ID từ URL hoặc trả raw nếu đã là ID."""
    patterns = [
        r'youtube\.com/channel/(UC[A-Za-z0-9_-]+)',
        r'youtube\.com/@([A-Za-z0-9_-]+)',
        r'youtube\.com/c/([A-Za-z0-9_-]+)',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return url


@router.post("/collect")
async def collect_channel(
    request: CollectChannelRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_supabase_user),
):
    """Trigger collect channel videos via BackgroundTasks."""
    admin = get_supabase_admin()
    channel_id = parse_channel_id(request.youtube_url)
    assistant_id = str(uuid.uuid4())
    
    # Insert channel_assistants
    admin.table('channel_assistants').insert({
        'id': assistant_id,
        'user_id': user_id,
        'youtube_url': request.youtube_url,
        'channel_id': channel_id,
        'status': 'collecting',
    }).execute()
    
    # Queue via BackgroundTasks
    background_tasks.add_task(_collect_channel_async, assistant_id, channel_id, user_id)
    
    return {
        'assistant_id': assistant_id,
        'status': 'collecting',
    }

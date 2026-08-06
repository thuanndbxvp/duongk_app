"""
Routers cho Channel Collection.
Mounted dưới /api/channels.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.worker.tasks.collect_channel_task import collect_channel_task
import uuid
import re


router = APIRouter(prefix="/api/channels", tags=["Channels"])


class CollectChannelRequest(BaseModel):
    youtube_url: str = Field(..., description="URL hoặc channel ID")


def parse_channel_id(url: str) -> str:
    """Parse channel ID từ URL hoặc trả raw nếu đã là ID."""
    # Match @handle, /channel/UC..., /c/handle
    patterns = [
        r'youtube\.com/channel/(UC[A-Za-z0-9_-]+)',
        r'youtube\.com/@([A-Za-z0-9_-]+)',
        r'youtube\.com/c/([A-Za-z0-9_-]+)',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return url  # assume already ID


@router.post("/collect")
async def collect_channel(
    request: CollectChannelRequest,
    user_id: str = Depends(get_supabase_user),
):
    """
    Trigger collect channel videos: insert assistant + enqueue collect_channel_task.
    
    Args:
        request: {youtube_url}.
    
    Returns:
        {assistant_id, status: 'collecting'}.
    """
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
    
    # Enqueue Celery task
    collect_channel_task.delay(assistant_id, channel_id)
    
    return {
        'assistant_id': assistant_id,
        'status': 'collecting',
    }
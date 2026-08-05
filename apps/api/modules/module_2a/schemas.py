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

class HealthResponse(BaseModel):
    status: str
    module: str
    version: str

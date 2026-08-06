"""
Pydantic v2 schemas for voice — Phase 03.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field

VoiceStatus = Literal["pending", "running", "success", "failed", "cancelled"]


class VoiceStartRequest(BaseModel):
    """Request to start TTS for project scenes."""
    voice_profile_id: UUID
    voice_version: int = Field(default=1, ge=1)
    scene_ids: Optional[list[UUID]] = None  # None = all scenes

    model_config = {"extra": "forbid"}


class VoiceStartResponse(BaseModel):
    """Response after enqueuing TTS tasks."""
    project_id: UUID
    total_scenes: int
    voice_lines: list[UUID]
    status: str = "enqueued"


class VoiceLineResponse(BaseModel):
    """Voice line status returned in API."""
    id: UUID
    scene_id: UUID
    voice_version: int
    text: str = ""
    duration_seconds: Optional[float] = None
    provider: str = "omnivoice"
    status: VoiceStatus
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class VoiceStatusResponse(BaseModel):
    """Aggregated status for all voice lines of a project."""
    project_id: UUID
    lines: list[VoiceLineResponse]
    total: int
    succeeded: int
    failed: int
    pending: int
    running: int


class VoiceRetryResponse(BaseModel):
    """Response after retrying a single scene."""
    voice_line_id: UUID
    scene_id: UUID
    status: str


class SubtitleTrackResponse(BaseModel):
    """Subtitle track info."""
    id: UUID
    project_id: UUID
    format: str
    version: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TimelineResponse(BaseModel):
    """Timeline model info."""
    id: UUID
    project_id: UUID
    version: int
    schema_version: int
    model: dict = Field(default_factory=dict)
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TimelineCompileResponse(BaseModel):
    """Response after compiling timeline."""
    timeline_id: UUID
    version: int
    status: str

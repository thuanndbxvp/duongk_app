"""
Pydantic v2 schemas for projects — Phase 01.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


# ============================================================
# Brief schemas
# ============================================================

class BriefPayload(BaseModel):
    """Creative brief payload (input from wizard)."""
    topic: str = Field(..., min_length=3, max_length=500)
    audience: str = Field(default="general", max_length=200)
    language: str = Field(default="vi", max_length=10)
    duration_target_seconds: int = Field(default=600, ge=1, le=3600)
    aspect_ratio: str = Field(default="16:9", max_length=10)
    tone: str = Field(default="casual", max_length=50)
    visual_style: str = Field(default="cinematic", max_length=50)
    voice_profile_id: Optional[UUID] = None
    music_mood: Optional[str] = Field(default=None, max_length=100)
    extra: dict = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class BriefResponse(BaseModel):
    """Brief data returned in API responses."""
    id: UUID
    project_id: UUID
    version: int
    topic: str
    audience: str
    language: str
    duration_target_seconds: int
    aspect_ratio: str
    tone: str
    visual_style: str
    voice_profile_id: Optional[UUID] = None
    music_mood: Optional[str] = None
    extra: dict = Field(default_factory=dict)
    schema_version: int = 1
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Project schemas
# ============================================================

class CreateProjectRequest(BaseModel):
    """Request body for POST /api/projects."""
    mode: Literal["blank", "clone_channel"]
    channel_assistant_id: Optional[UUID] = None
    brief: BriefPayload

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def check_clone_requires_assistant(self) -> "CreateProjectRequest":
        if self.mode == "clone_channel" and self.channel_assistant_id is None:
            raise ValueError("clone_channel mode requires channel_assistant_id")
        return self


class ProjectResponse(BaseModel):
    """Project data returned in API responses."""
    id: UUID
    user_id: UUID
    channel_assistant_id: Optional[UUID] = None
    mode: str
    status: str
    approval_state: str
    brief_hash: str
    schema_version: int = 1
    brief: Optional[BriefResponse] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """Cursor-paginated list of projects."""
    data: list[ProjectResponse]
    next_cursor: Optional[str] = None
    total: int = 0


# ============================================================
# Approval schemas
# ============================================================

class ApprovalRequest(BaseModel):
    """Request body for POST /api/projects/{id}/approve."""
    decision: Literal["approved", "rejected"]
    comment: Optional[str] = Field(default=None, max_length=1000)

    model_config = {"extra": "forbid"}


class ApprovalResponse(BaseModel):
    """Approval result returned after decision."""
    project_id: UUID
    approval_state: str
    decision: str
    comment: Optional[str] = None
    updated_at: datetime


# ============================================================
# Stage event schema
# ============================================================

class StageEventResponse(BaseModel):
    """Stage transition event."""
    id: UUID
    project_id: UUID
    stage: str
    event_type: str
    payload: dict = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}

"""
Pydantic schemas for channel intelligence — Phase 06.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class InsightItemResponse(BaseModel):
    """Insight item with evidence."""
    id: UUID
    channel_assistant_id: UUID
    title: str
    body: str
    evidence_comment_ids: list[str] = Field(default_factory=list)
    opportunity_score: Optional[float] = None
    status: str
    source_project_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InsightApproveRequest(BaseModel):
    """Approve/reject an insight."""
    decision: str = Field(..., pattern="^(approved|rejected)$")

    model_config = {"extra": "forbid"}


class InsightToProjectResponse(BaseModel):
    """Result of converting insight to project."""
    insight_id: UUID
    project_id: UUID
    status: str


class IngestCommentsRequest(BaseModel):
    """Request to ingest comments for videos."""
    video_ids: list[str] = Field(..., min_length=1, max_length=50)

    model_config = {"extra": "forbid"}


class IngestCommentsResponse(BaseModel):
    """Ingest result."""
    batch_id: UUID
    video_count: int
    status: str


class ChannelProfileVersionResponse(BaseModel):
    """Versioned channel profile."""
    id: UUID
    channel_assistant_id: UUID
    version: int
    audience: str
    visual_style: str
    created_at: datetime

    model_config = {"from_attributes": True}

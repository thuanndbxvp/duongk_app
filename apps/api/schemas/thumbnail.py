"""
Pydantic v2 schemas for thumbnail & metadata — Phase 05.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ThumbnailGenerateRequest(BaseModel):
    """Request to generate thumbnail candidates."""
    provider: str = Field(default="gemini")
    count: int = Field(default=3, ge=1, le=5)

    model_config = {"extra": "forbid"}


class ThumbnailCandidateResponse(BaseModel):
    """Thumbnail candidate data."""
    id: UUID
    project_id: UUID
    asset_id: UUID
    score: Optional[float] = None
    provider: str
    selected: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ThumbnailSelectRequest(BaseModel):
    """Select a thumbnail candidate."""
    candidate_id: UUID

    model_config = {"extra": "forbid"}


class MetadataBuildResponse(BaseModel):
    """Metadata package build result."""
    id: UUID
    project_id: UUID
    version: int
    title: str
    description: str
    tags: list[str]
    hashtags: list[str]
    thumbnail_asset_id: Optional[UUID] = None

    model_config = {"from_attributes": True}


class CleanupPreviewResponse(BaseModel):
    """Watermark cleanup preview."""
    preview_asset_id: UUID
    consent_id: UUID
    status: str = "preview_ready"


class CleanupApproveRequest(BaseModel):
    """Approve watermark cleanup."""
    consent_id: UUID

    model_config = {"extra": "forbid"}

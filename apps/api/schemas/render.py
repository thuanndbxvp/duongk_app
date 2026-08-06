"""
Pydantic v2 schemas for render — Phase 04.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field

RenderKind = Literal["draft", "final"]


class RenderStartRequest(BaseModel):
    """Request to start a render job."""
    kind: RenderKind = "draft"
    timeline_id: UUID

    model_config = {"extra": "forbid"}


class RenderStartResponse(BaseModel):
    """Response after enqueuing render."""
    render_job_id: UUID
    job_type: RenderKind
    status: str = "enqueued"


class RenderJobResponse(BaseModel):
    """Render job status."""
    id: UUID
    project_id: UUID
    job_type: RenderKind
    status: str
    progress: float = Field(default=0.0, ge=0, le=1)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    output_asset_id: Optional[UUID] = None
    retry_count: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ExportResponse(BaseModel):
    """Download URL for rendered video."""
    id: UUID
    job_id: UUID
    download_url: str
    expires_at: datetime

    model_config = {"from_attributes": True}

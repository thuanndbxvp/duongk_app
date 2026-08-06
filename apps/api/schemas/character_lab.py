"""
Pydantic schemas for character lab — Phase 11.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class LabStartRequest(BaseModel):
    """Start a character lab session."""
    style_bible_id: Optional[UUID] = None

    model_config = {"extra": "forbid"}


class LabResponse(BaseModel):
    id: UUID
    project_id: UUID
    status: str
    cost_estimate: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CharacterAnchorResponse(BaseModel):
    id: UUID
    lab_run_id: UUID
    character_name: str
    asset_id: Optional[UUID] = None
    provider: str
    anchor_strength: float
    regenerate_count: int
    is_approved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BackgroundAnchorResponse(BaseModel):
    id: UUID
    lab_run_id: UUID
    background_name: str
    asset_id: Optional[UUID] = None
    provider: str
    is_approved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CoverageReport(BaseModel):
    total_scenes: int
    scenes_with_character: int
    scenes_with_background: int
    coverage_pct: float
    missing_scenes: list[UUID] = Field(default_factory=list)

"""
Pydantic v2 schemas for style bible — Phase 09.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class StyleBibleCreate(BaseModel):
    """Create a new style bible."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    visual_palette: dict = Field(default_factory=dict)
    lens_preference: str = ""
    motion_style: str = ""
    negative_prompt: str = ""

    model_config = {"extra": "forbid"}


class StyleBibleUpdate(BaseModel):
    """Update an existing style bible."""
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    visual_palette: Optional[dict] = None
    lens_preference: Optional[str] = None
    motion_style: Optional[str] = None
    negative_prompt: Optional[str] = None

    model_config = {"extra": "forbid"}


class StyleBibleResponse(BaseModel):
    """Style bible response."""
    id: UUID
    owner_id: UUID
    name: str
    description: str
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StyleBibleApplyRequest(BaseModel):
    """Apply a style bible to a project/scene."""
    bible_id: UUID
    bible_version: Optional[int] = None
    scene_ids: Optional[list[UUID]] = None

    model_config = {"extra": "forbid"}


class CharacterRef(BaseModel):
    """Character reference in style bible."""
    asset_id: UUID
    label: str = ""
    anchor_strength: float = Field(default=0.5, ge=0, le=1)


class BackgroundRef(BaseModel):
    """Background reference in style bible."""
    asset_id: UUID
    label: str = ""

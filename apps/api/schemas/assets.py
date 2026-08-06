"""
Pydantic v2 schemas for assets — Phase 02.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml",
    "video/mp4", "video/webm", "video/quicktime",
    "audio/mpeg", "audio/wav", "audio/ogg",
}

MAX_SIZE_BYTES = {
    "image": 20 * 1024 * 1024,   # 20 MB
    "video": 200 * 1024 * 1024,  # 200 MB
    "audio": 50 * 1024 * 1024,   # 50 MB
}


def _category_from_mime(mime: str) -> str:
    if mime.startswith("image/"): return "image"
    if mime.startswith("video/"): return "video"
    if mime.startswith("audio/"): return "audio"
    return "other"


# ============================================================
# Upload schemas
# ============================================================

class UploadInitRequest(BaseModel):
    """Request to initialize an upload."""
    filename: str = Field(..., max_length=255)
    mime_type: str
    size_bytes: int = Field(..., gt=0)
    checksum: str = Field(..., min_length=8)

    model_config = {"extra": "forbid"}

    @field_validator("mime_type")
    @classmethod
    def validate_mime(cls, v: str) -> str:
        if v not in ALLOWED_MIME_TYPES:
            raise ValueError(f"Unsupported MIME type: {v}")
        return v

    @field_validator("size_bytes")
    @classmethod
    def validate_size(cls, v: int, info) -> int:
        mime = info.data.get("mime_type", "")
        cat = _category_from_mime(mime)
        limit = MAX_SIZE_BYTES.get(cat, MAX_SIZE_BYTES["image"])
        if v > limit:
            raise ValueError(f"File too large: {v} > {limit} bytes (max for {cat})")
        return v


class UploadInitResponse(BaseModel):
    """Response with upload URL and asset ID."""
    asset_id: UUID
    upload_url: str
    storage_key: str
    expires_at: datetime


class UploadCompleteRequest(BaseModel):
    """Confirm upload with final checksum verification."""
    asset_id: UUID
    checksum: str = Field(..., min_length=8)

    model_config = {"extra": "forbid"}


# ============================================================
# Asset schemas
# ============================================================

class AssetResponse(BaseModel):
    """Asset data returned in API responses."""
    id: UUID
    owner_id: UUID
    source: str
    provider_id: Optional[str] = None
    storage_key: str
    mime_type: str
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    checksum: str
    license: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetListResponse(BaseModel):
    """Paginated list of assets."""
    data: list[AssetResponse]
    next_cursor: Optional[str] = None
    total: int = 0


# ============================================================
# Search schemas
# ============================================================

class AssetSearchRequest(BaseModel):
    """Search for stock assets."""
    provider: Literal["pexels", "local_placeholder"] = "pexels"
    query: str = Field(..., min_length=1, max_length=200)
    media_type: Literal["image", "video"] = "image"
    orientation: Optional[Literal["landscape", "portrait", "square"]] = None
    page: int = Field(default=1, ge=1, le=50)

    model_config = {"extra": "forbid"}


class AssetSearchResult(BaseModel):
    """Single search result from a provider."""
    provider: str
    provider_id: str
    thumbnail_url: str
    description: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    photographer: Optional[str] = None
    pexels_url: Optional[str] = None


class AssetSearchResponse(BaseModel):
    """Search results wrapper."""
    results: list[AssetSearchResult]
    page: int
    total_results: int
    next_page: Optional[int] = None


# ============================================================
# Materialize schemas
# ============================================================

class MaterializeRequest(BaseModel):
    """Request to materialize a stock asset into user's library."""
    provider: Literal["pexels", "local_placeholder"]
    provider_id: str = Field(..., min_length=1)

    model_config = {"extra": "forbid"}


# ============================================================
# Scene-Asset binding schemas
# ============================================================

class SceneAssetBindRequest(BaseModel):
    """Bind an asset to a scene."""
    asset_id: UUID
    position: int = Field(default=0, ge=0)

    model_config = {"extra": "forbid"}


class SceneAssetResponse(BaseModel):
    """Scene-asset binding response."""
    id: UUID
    scene_id: UUID
    asset_id: UUID
    position: int
    asset: Optional[AssetResponse] = None
    created_at: datetime

    model_config = {"from_attributes": True}

"""
Module 1 Pydantic Schemas.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class NicheValidationRequest(BaseModel):
    """Request schema for niche validation."""
    
    keyword: str = Field(..., min_length=2, max_length=100, description="Keyword to validate")
    user_id: str = Field(default="system", description="User ID for testing")
    use_cache: bool = Field(default=True, description="Use cached results")


class NicheValidationResponse(BaseModel):
    """Response schema for niche validation."""
    
    keyword: str = Field(..., description="Original keyword")
    total_monthly_views: int = Field(..., ge=0, description="Estimated monthly views")
    total_channels: int = Field(..., ge=0, description="Number of competing channels")
    avg_views_per_video: int = Field(..., ge=0, description="Average views per video")
    google_trends_interest: int = Field(..., ge=0, le=100, description="Google Trends interest score")
    is_viable: bool = Field(..., description="Whether niche is viable")
    suggested_titles: List[str] = Field(..., min_length=1, max_length=10, description="Suggested video titles")


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    module: str
    version: str

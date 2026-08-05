"""
Module 1 API Routes - Niche Validation.
"""
from fastapi import APIRouter, HTTPException, Depends
from apps.api.modules.module_1.schemas import (
    NicheValidationRequest,
    NicheValidationResponse,
    HealthResponse
)
from apps.api.modules.module_1.service import NicheValidator


router = APIRouter(prefix="/api/research", tags=["Module 1 - Niche Validate"])

# Redis URL from environment
import os
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Dependency for validator
async def get_validator() -> NicheValidator:
    """Get NicheValidator instance."""
    return NicheValidator(REDIS_URL)


@router.post("/validate", response_model=NicheValidationResponse)
async def validate_niche(
    request: NicheValidationRequest,
    validator: NicheValidator = Depends(get_validator)
):
    """
    Validate niche viability for YouTube content creation.
    
    - Checks Google Trends data
    - Analyzes competitor landscape
    - Estimates potential views
    
    **Note:** This endpoint uses Redis caching. Subsequent calls
    for the same keyword return cached results.
    """
    try:
        result = await validator.validate(
            keyword=request.keyword,
            use_cache=request.use_cache
        )
        return NicheValidationResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Module 1."""
    return HealthResponse(
        status="healthy",
        module="niche_validate",
        version="1.0.0"
    )

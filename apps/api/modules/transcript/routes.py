"""
Transcript API Routes.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from apps.api.modules.transcript.engine import TranscriptEngine


router = APIRouter(prefix="/api/transcript", tags=["Transcript Engine"])


def get_engine() -> TranscriptEngine:
    """Get TranscriptEngine instance."""
    return TranscriptEngine()


class TranscriptRequest(BaseModel):
    video_id: str = Field(..., description="YouTube video ID")
    languages: List[str] = Field(default=['vi', 'en'], description="Preferred languages")


class TranscriptResponse(BaseModel):
    video_id: str
    transcript: str
    language: str
    tier_used: int
    cached: bool


class HealthResponse(BaseModel):
    status: str
    module: str
    version: str


@router.post("/", response_model=TranscriptResponse)
async def get_transcript(
    request: TranscriptRequest,
    engine: TranscriptEngine = Depends(get_engine)
):
    """
    Get transcript for a YouTube video using 3-tier fallback.
    
    Tier 1: youtube-transcript-api (fastest, free)
    Tier 2: Supadata API (reliable, paid)
    Tier 3: yt-dlp + Whisper (slowest, most expensive)
    """
    try:
        result = await engine.get_transcript(
            video_id=request.video_id,
            preferred_languages=request.languages
        )
        
        if result:
            return TranscriptResponse(**result)
        else:
            raise HTTPException(
                status_code=404,
                detail="Transcript not available for this video"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcript fetch failed: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check for Transcript Engine."""
    return HealthResponse(
        status="healthy",
        module="transcript_engine",
        version="1.0.0"
    )

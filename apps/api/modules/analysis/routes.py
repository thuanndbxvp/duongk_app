"""API Routes for Analysis Module."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Any

router = APIRouter(prefix="/api/analysis", tags=["Module 3 - Deterministic Layer"])

class AnalyzeRequest(BaseModel):
    videos: List[dict]

class AnalysisResponse(BaseModel):
    output_1: dict
    output_2: dict
    output_3: dict
    output_4: dict

@router.post("/channel", response_model=AnalysisResponse)
async def analyze_channel(request: AnalyzeRequest):
    """
    Generate deterministic output analysis for a batch of videos.
    """
    from .outputs import generate_output_1, generate_output_2, generate_output_3, generate_output_4
    return AnalysisResponse(
        output_1=generate_output_1(request.videos),
        output_2=generate_output_2(request.videos),
        output_3=generate_output_3(request.videos),
        output_4=generate_output_4(request.videos)
    )

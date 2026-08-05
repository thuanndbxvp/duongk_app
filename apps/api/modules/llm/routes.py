"""LLM API Routes."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/llm", tags=["LLM Analysis"])

class LLMRequest(BaseModel):
    transcripts: List[str]
    titles: List[str] = []
    thumbnail_urls: List[str] = []

@router.post("/analyze")
async def analyze_llm(request: LLMRequest):
    from ..llm.analyzer import LLMAnalyzer
    from ..vision.thumbnail_analyzer import ThumbnailAnalyzer
    
    llm = LLMAnalyzer()
    vision = ThumbnailAnalyzer()
    
    return {
        'output_8_hooks': await llm.analyze_hooks(request.transcripts, request.titles),
        'output_9_structure': await llm.extract_structure(request.transcripts),
        'output_11_mimic_rules': await llm.generate_mimic_rules(request.transcripts),
        'output_14_thumbnail': await vision.analyze_thumbnails(request.thumbnail_urls)
    }

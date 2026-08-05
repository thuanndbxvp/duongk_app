"""NLP API Routes."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/nlp", tags=["NLP"])

class NLPRequest(BaseModel):
    transcripts: List[str]
    titles: List[str] = []

class NLPResponse(BaseModel):
    output_5_emotions: dict
    output_6_pacing: dict
    output_7_category: dict
    output_10_hook_strength: dict

@router.post("/analyze", response_model=NLPResponse)
async def analyze_nlp(request: NLPRequest):
    """Analyze all NLP outputs using GPT-4o."""
    from .gpt_analyzer import GPTNLPAnalyzer

    analyzer = GPTNLPAnalyzer()
    result = await analyzer.analyze_all(request.transcripts, request.titles)

    return NLPResponse(
        output_5_emotions=result.get('emotions', {}),
        output_6_pacing=result.get('pacing', {}),
        output_7_category=result.get('category', {}),
        output_10_hook_strength=result.get('hooks', {})
    )

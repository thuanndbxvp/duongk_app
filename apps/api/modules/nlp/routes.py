"""NLP API Routes."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/nlp", tags=["NLP"])

class NLPPRequest(BaseModel):
    transcripts: List[str]
    titles: List[str] = []

@router.post("/analyze")
async def analyze_nlp(request: NLPPRequest):
    from .emotions import analyze_emotions
    from .pacing import calculate_pacing
    from .category import classify_category
    from .hooks import analyze_hook_strength
    
    avg_pacing = calculate_pacing(' '.join(request.transcripts)) if request.transcripts else {}
    
    return {
        'output_5_emotions': analyze_emotions(request.transcripts),
        'output_6_pacing': avg_pacing,
        'output_7_category': classify_category(request.transcripts, request.titles),
        'output_10_hook_strength': analyze_hook_strength(request.transcripts, request.titles)
    }

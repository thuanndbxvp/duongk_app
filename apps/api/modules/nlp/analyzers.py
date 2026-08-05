"""Individual NLP analyzers."""
from typing import List
from .gpt_analyzer import GPTNLPAnalyzer

async def analyze_emotions(transcripts: List[str]) -> dict:
    """Output 5: Emotional Tone Analysis."""
    analyzer = GPTNLPAnalyzer()
    result = await analyzer.analyze_all(transcripts, [])
    return result.get('output_5_emotions', {})

async def analyze_pacing(transcript: str) -> dict:
    """Output 6: Pacing Profile."""
    analyzer = GPTNLPAnalyzer()
    result = await analyzer.analyze_all([transcript], [])
    return result.get('output_6_pacing', {})

async def classify_category(transcripts: List[str], titles: List[str]) -> dict:
    """Output 7: Content Category."""
    analyzer = GPTNLPAnalyzer()
    result = await analyzer.analyze_all(transcripts, titles)
    return result.get('output_7_category', {})

async def analyze_hooks(titles: List[str], transcripts: List[str]) -> dict:
    """Output 10: Hook Strength."""
    analyzer = GPTNLPAnalyzer()
    result = await analyzer.analyze_all(transcripts, titles)
    return result.get('output_10_hook_strength', {})

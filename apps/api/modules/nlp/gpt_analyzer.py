"""GPT-4o NLP Analyzer - No local ML models needed!"""
import os
import json
from typing import List, Dict, Any
import openai

class GPTNLPAnalyzer:
    """All NLP tasks via GPT-4o API."""

    def __init__(self, api_key: str = None):
        self.client = openai.AsyncOpenAI(api_key=api_key or os.environ.get('OPENAI_API_KEY'))

    async def analyze_all(
        self,
        transcripts: List[str],
        titles: List[str]
    ) -> Dict[str, Any]:
        """Phân tích tất cả 4 outputs bằng GPT-4o."""
        sample_transcripts = transcripts[:5] if len(transcripts) > 5 else transcripts
        sample_titles = titles[:10] if len(titles) > 10 else titles

        transcript_text = "\n---\n".join([f"[Video {i+1}]: {t[:500]}..." for i, t in enumerate(sample_transcripts)])
        titles_text = "\n".join([f"- {t}" for t in sample_titles])

        prompt = f"""Analyze these YouTube video transcripts and titles.

**Titles:**
{titles_text}

**Transcripts (sample):**
{transcript_text}

Return JSON with ALL 4 analyses:

1. **Emotional Tone** (Output 5):
{{"dominant_emotions": [...], "emotion_distribution": {{}}, "emotion_consistency": 0.0-1.0}}

2. **Pacing Profile** (Output 6):
{{"avg_wpm": 120-180, "avg_sentence_length": 10-20, "pacing_type": "string", "pacing_variation": 0.0-1.0, "silence_ratio": 0.0-1.0}}

3. **Content Category** (Output 7):
{{"primary_category": "string", "secondary_categories": [...], "category_confidence": 0.0-1.0}}

4. **Hook Strength** (Output 10):
{{"avg_hook_score": 0.0-1.0, "hook_types_detected": [...], "hook_effectiveness_by_type": {{}}}}"""

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

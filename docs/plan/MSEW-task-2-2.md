# MSEW: Task 2.2 - NLP & Local ML Layer

> ⚠️ **ĐÃ THAY ĐỔI:** Thay local ML (torch/transformers) bằng OpenAI GPT-4o API

---

## Micro-Steps

### Step 1: GPT NLP Analyzer
**File:** `apps/api/modules/nlp/gpt_analyzer.py`

```python
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
```

---

### Step 2: Individual Analyzers (Optional)
**File:** `apps/api/modules/nlp/analyzers.py`

```python
"""Individual NLP analyzers."""
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
```

---

### Step 3: Routes
**File:** `apps/api/modules/nlp/routes.py`

```python
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
```

---

### Step 4: Unit Tests
**File:** `tests/test_nlp/test_gpt_analyzer.py`

```python
"""Test GPT NLP Analyzer."""
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_analyze_all():
    """Test GPT-4o analysis."""
    with patch('openai.AsyncOpenAI') as mock_client:
        mock_client.return_value.chat.completions.create = AsyncMock(
            return_value=type('obj', (object,), {
                'choices': [type('obj', (object,), {
                    'message': type('obj', (object,), {
                        'content': '{"emotions": {}, "pacing": {}, "category": {}, "hooks": {}}'
                    })()
                })()]
            })()
        )

        from apps.api.modules.nlp.gpt_analyzer import GPTNLPAnalyzer
        analyzer = GPTNLPAnalyzer(api_key="test-key")
        result = await analyzer.analyze_all(["test transcript"], ["Test Title"])

        assert 'emotions' in result or 'pacing' in result
```

---

## Dependencies (ĐÃ LOẠI BỎ TORCH!)

```bash
pip install openai underthesea
```

**ĐÃ LOẠI BỎ:**
- ❌ `transformers`
- ❌ `torch`
- ❌ `j-hartmann/emotion-english-distilroberta-base`
- ❌ `wonrax/phobert-base-vietnamese-emotion`

---

**Verify:** `pytest tests/test_nlp/ -v`

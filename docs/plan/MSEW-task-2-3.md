# MSEW: Task 2.3 - LLM & Vision Layer

> Prerequisites: `pip install openai`

---

## Micro-Steps

### Step 1: LLM Analyzer
**File:** `apps/api/modules/llm/analyzer.py`

```python
"""LLM-powered analysis using GPT-4o."""
import os
import json
from typing import List, Dict, Any
import openai

class LLMAnalyzer:
    """GPT-4o for analysis."""
    
    def __init__(self, api_key: str = None):
        self.client = openai.OpenAI(api_key=api_key or os.environ.get('OPENAI_API_KEY'))
    
    async def analyze_hooks(self, transcripts: List[str], titles: List[str]) -> dict:
        """Output 8: Hook Analysis."""
        prompt = f"""Analyze these video titles and transcripts to identify hook patterns.
        
Titles: {chr(10).join(titles[:10])}
        
Transcripts (first 30s): {chr(10).join([t[:200] for t in transcripts[:10]])}
        
Return JSON: {{"hook_patterns": [{{"type": "string", "example": "string", "effectiveness_score": 0.0}}], "hook_framework": "string"}}"""
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    
    async def extract_structure(self, transcripts: List[str]) -> dict:
        """Output 9: Structural Formula."""
        prompt = f"""Analyze these transcripts to find the structural pattern.
        
Transcripts: {chr(10).join([t[:500] for t in transcripts[:5]])}
        
Return JSON: {{"typical_structure": {{"opening": {{"seconds": 15}}, "main_content": {{"seconds": 600}}}}, "structure_type": "string"}}"""
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    
    async def generate_mimic_rules(self, transcripts: List[str]) -> dict:
        """Output 11: Mimic Rules."""
        prompt = f"""Analyze these transcripts to create mimic rules.
        
Transcripts: {chr(10).join([t[:500] for t in transcripts[:5]])}
        
Return JSON: {{"mimic_guidelines": {{"vocabulary_level": "string", "common_phrases": ["string"]}}, "tone": "string"}}"""
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
```

---

### Step 2: Vision Analyzer
**File:** `apps/api/modules/vision/thumbnail_analyzer.py`

```python
"""GPT-4o Vision for thumbnail analysis."""
import os
import json
from typing import List
import openai

class ThumbnailAnalyzer:
    """GPT-4o Vision for thumbnails."""
    
    def __init__(self, api_key: str = None):
        self.client = openai.OpenAI(api_key=api_key or os.environ.get('OPENAI_API_KEY'))
    
    async def analyze_thumbnails(self, thumbnail_urls: List[str]) -> dict:
        """Output 14: Thumbnail Analysis."""
        if not thumbnail_urls:
            return {'avg_thumbnail_style': {}, 'thumbnail_effectiveness': {}}
        
        content = [{"type": "text", "text": "Analyze these YouTube thumbnails. Return JSON: {\"avg_thumbnail_style\": {\"text_presence\": true, \"face_presence\": true}, \"thumbnail_effectiveness\": {\"avg_ctr_correlation\": 0.5}}}"}]
        
        for url in thumbnail_urls[:20]:
            content.append({"type": "image_url", "image_url": {"url": url}})
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}]
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            return {'avg_thumbnail_style': {}, 'thumbnail_effectiveness': {}}
```

---

### Step 3: Routes
**File:** `apps/api/modules/llm/routes.py`

```python
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
```

---

### Step 4: Versioning Migration (E7)
**File:** `supabase/migrations/0012_analysis_versions.sql`

```sql
-- E7 FIX: Versioning for channel_deep_analysis

ALTER TABLE channel_deep_analysis 
    ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1,
    ADD COLUMN IF NOT EXISTS parent_version INTEGER,
    ADD COLUMN IF NOT EXISTS version_note TEXT;

CREATE OR REPLACE FUNCTION create_analysis_version()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM channel_deep_analysis WHERE channel_id = NEW.channel_id) THEN
        SELECT MAX(version) INTO NEW.version FROM channel_deep_analysis WHERE channel_id = NEW.channel_id;
        NEW.version = COALESCE(NEW.version, 0) + 1;
        NEW.parent_version = NEW.version - 1;
    ELSE
        NEW.version = 1;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_analysis_version
    BEFORE INSERT ON channel_deep_analysis
    FOR EACH ROW
    EXECUTE FUNCTION create_analysis_version();
```

---

**Verify:** `pytest tests/test_llm/ -v`

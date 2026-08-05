# Kiến trúc & Luồng xử lý (PLAN): Task 2.3 - LLM & Vision Layer (Outputs 8, 9, 11, 14)

## 1. Mục tiêu

Xây dựng tầng LLM và Vision để tạo 4 outputs:
- **Output 8**: Hook Analysis (detailed)
- **Output 9**: Structural Formula
- **Output 11**: Mimic Rules
- **Output 14**: Thumbnail Analysis (Vision)

## 2. Outputs

### Output 8: Hook Analysis (LLM-powered)
```python
{
    "hook_patterns": [
        {
            "type": "question",
            "example": "Bạn có biết...",
            "effectiveness_score": 0.85,
            "frequency": 0.4
        }
    ],
    "hook_framework": "PAS",  # Problem-Agitate-Solution
    "recommended_hook_formula": "Start with [question/promise] + [agitation] + [promise]"
}
```

### Output 9: Structural Formula
```python
{
    "typical_structure": {
        "opening": {"seconds": 15, "purpose": "hook"},
        "intro": {"seconds": 30, "purpose": "context"},
        "main_content": {"seconds": 600, "purpose": "value"},
        "conclusion": {"seconds": 45, "purpose": "cta"}
    },
    "structure_type": "linear",  # or "modular", "storytelling"
    "segments_per_video_avg": 8,
    "recommended_template": {...}
}
```

### Output 11: Mimic Rules
```python
{
    "mimic_guidelines": {
        "vocabulary_level": "conversational",
        "sentence_starts": ["Bạn", "Hôm nay", "Mình"],
        "common_phrases": ["cực kỳ", "tuyệt vời", "nên xem"],
        "tone": "friendly_expert",
        "cta_style": "direct"
    },
    "language_patterns": {...},
    "content_blueprint": {...}
}
```

### Output 14: Thumbnail Analysis (Vision)
```python
{
    "avg_thumbnail_style": {
        "text_presence": True,
        "text_position": "center_bottom",
        "face_presence": True,
        "emotion": "excited",
        "color_scheme": "warm",
        "contrast": "high"
    },
    "thumbnail_effectiveness": {
        "avg_ctr_correlation": 0.65,
        "best_practices": [...]
    },
    "recommended_thumbnail_template": {...}
}
```

## 3. LLM Integration

### OpenAI GPT-4o
```python
# apps/api/modules/llm/analyzer.py
import openai
from typing import List

class LLMAnalyzer:
    """LLM-powered analysis using GPT-4o."""
    
    def __init__(self, api_key: str = None):
        self.client = openai.OpenAI(api_key=api_key)
    
    async def analyze_hook_patterns(
        self,
        transcripts: List[str],
        titles: List[str]
    ) -> dict:
        """
        GPT-4o analyzes hook patterns from transcripts.
        """
        prompt = f"""Analyze the following video transcripts and titles
        to identify hook patterns and their effectiveness.
        
        Transcripts (first 30 seconds each):
        {self._format_transcripts(transcripts)}
        
        Titles:
        {chr(10).join(titles)}
        
        Return JSON with:
        - hook_patterns: array of {type, example, effectiveness_score, frequency}
        - hook_framework: PAS|Story|Question|Bold Statement
        - recommended_hook_formula
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def extract_structural_formula(
        self,
        transcripts: List[str]
    ) -> dict:
        """
        Extract structural formula from transcripts.
        """
        prompt = f"""Analyze these transcripts to find the structural pattern:
        
        {self._format_transcripts(transcripts)}
        
        Return JSON with:
        - typical_structure: {{segment: {{seconds, purpose}}}}
        - structure_type: linear|modular|storytelling
        - segments_per_video_avg
        - recommended_template
        """
        
        # ... similar implementation
```

### GPT-4o Vision for Thumbnails
```python
# apps/api/modules/vision/thumbnail_analyzer.py
import openai
from typing import List

class ThumbnailAnalyzer:
    """GPT-4o Vision for thumbnail analysis."""
    
    def __init__(self, api_key: str = None):
        self.client = openai.OpenAI(api_key=api_key)
    
    async def analyze_thumbnails(
        self,
        thumbnail_urls: List[str]
    ) -> dict:
        """
        Use GPT-4o Vision to analyze thumbnails.
        """
        # Download thumbnails (or use stored URLs)
        # Must be JPEG/PNG, <20MB
        
        content = []
        for url in thumbnail_urls[:20]:  # Analyze 20 thumbnails
            content.append({
                "type": "image_url",
                "image_url": {"url": url}
            })
        
        prompt = """Analyze these YouTube thumbnails and return JSON with:
        - avg_thumbnail_style: {{text_presence, text_position, face_presence, emotion, color_scheme, contrast}}
        - thumbnail_effectiveness: {{avg_ctr_correlation, best_practices}}
        - recommended_thumbnail_template
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}] + content}]
        )
        
        return json.loads(response.choices[0].message.content)
```

## 4. E7 FIX - Versioning

```sql
-- supabase/migrations/0012_analysis_versions.sql

ALTER TABLE channel_deep_analysis ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
ALTER TABLE channel_deep_analysis ADD COLUMN IF NOT EXISTS parent_version INTEGER;
ALTER TABLE channel_deep_analysis ADD COLUMN IF NOT EXISTS version_note TEXT;

-- Create version trigger
CREATE OR REPLACE FUNCTION create_analysis_version()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.channel_id = OLD.channel_id THEN
        -- Same channel, increment version
        NEW.version = OLD.version + 1;
        NEW.parent_version = OLD.version;
    ELSE
        -- New channel
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

## 5. Dependencies

```bash
pip install openai
```

## 6. Files cần tạo

| File | Mô tả |
|------|--------|
| `apps/api/modules/llm/__init__.py` | Package init |
| `apps/api/modules/llm/analyzer.py` | LLM Analyzer (GPT-4o) |
| `apps/api/modules/llm/prompts.py` | Prompt templates |
| `apps/api/modules/vision/__init__.py` | Package init |
| `apps/api/modules/vision/thumbnail_analyzer.py` | GPT-4o Vision |
| `supabase/migrations/0012_analysis_versions.sql` | E7 versioning |

## 7. Verification

- [ ] GPT-4o returns structured JSON
- [ ] Hook patterns identified correctly
- [ ] Structural formula extracted
- [ ] Mimic rules generated
- [ ] Vision analyzes thumbnails
- [ ] Versioning works on re-analysis
- [ ] Cost tracking in place

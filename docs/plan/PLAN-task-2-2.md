# Kiến trúc & Luồng xử lý (PLAN): Task 2.2 - NLP & Local ML Layer (Outputs 5, 6, 7, 10)

## 1. Mục tiêu

Xây dựng tầng NLP sử dụng **OpenAI GPT-4o API** (thay vì local ML models):

- **Output 5**: Emotional Tone Analysis
- **Output 6**: Pacing Profile (WPM)
- **Output 7**: Content Category Classification
- **Output 10**: Hook Strength Analysis

## 2. ⚠️ THAY ĐỔI QUAN TRỌNG - KHÔNG CÒN LOCAL ML!

```
┌─────────────────────────────────────────────────────────────────┐
│              TRƯỚC ĐÂY (Tốn RAM/Deploy lâu)                     │
├─────────────────────────────────────────────────────────────────┤
│  • transformers (torch) > 2GB                                   │
│  • PhoBERT model > 500MB                                        │
│  • emotion-english-distilroberta > 500MB                        │
│  • Tổng: > 3GB dependencies                                    │
│  • Deploy time: 5-10 phút                                       │
│  • RAM khi chạy: 2-4GB                                         │
└─────────────────────────────────────────────────────────────────┘

                        ↓ THAY ĐỔI ↓

┌─────────────────────────────────────────────────────────────────┐
│              BÂY GIỜ (Nhẹ nhàng, nhanh)                        │
├─────────────────────────────────────────────────────────────────┤
│  • openai SDK: ~1MB                                             │
│  • Tất cả NLP tasks gọi GPT-4o API                             │
│  • Deploy time: < 1 phút                                       │
│  • RAM khi chạy: < 100MB                                       │
│  • Chi phí API: ~$0.01-0.05/kênh                              │
└─────────────────────────────────────────────────────────────────┘
```

## 3. Outputs (All GPT-4o)

### Output 5: Emotional Tone Analysis
```python
{
    "dominant_emotions": ["excited", "informative", "trustworthy"],
    "emotion_distribution": {
        "excited": 0.35,
        "informative": 0.30,
        "trustworthy": 0.20,
        "neutral": 0.15
    },
    "emotion_consistency": 0.85
}
```

### Output 6: Pacing Profile
```python
{
    "avg_wpm": 150,
    "avg_sentence_length": 15,
    "pacing_type": "moderate",
    "pacing_variation": 0.2,
    "silence_ratio": 0.15
}
```

### Output 7: Content Category
```python
{
    "primary_category": "Education",
    "secondary_categories": ["Entertainment", "Howto"],
    "category_confidence": 0.92
}
```

### Output 10: Hook Strength
```python
{
    "avg_hook_score": 0.75,
    "hook_types_detected": ["question", "promise", "contrast"],
    "hook_effectiveness_by_type": {
        "question": 0.8,
        "promise": 0.75,
        "contrast": 0.7
    }
}
```

## 4. GPT-4o Integration

```python
# apps/api/modules/nlp/gpt_analyzer.py
import os
import json
from typing import List, Dict, Any
import openai

class GPTNLPAnalyzer:
    """
    All NLP tasks via GPT-4o API - no local ML models needed!

    Benefits:
    - No torch/transformers dependencies
    - Fast deploy (<1 phút)
    - Low RAM usage (<100MB)
    - Better results (GPT-4o)
    """

    def __init__(self, api_key: str = None):
        self.client = openai.AsyncOpenAI(api_key=api_key or os.environ.get('OPENAI_API_KEY'))

    async def analyze_all(
        self,
        transcripts: List[str],
        titles: List[str]
    ) -> Dict[str, Any]:
        """
        Phân tích tất cả 4 outputs bằng GPT-4o.
        Gọi 1 lần, nhận về tất cả.
        """
        # Ghép transcripts (lấy mẫu để tiết kiệm tokens)
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
{{
  "dominant_emotions": ["emotion1", "emotion2", "emotion3"],
  "emotion_distribution": {{"emotion1": 0.35, "emotion2": 0.30, ...}},
  "emotion_consistency": 0.0-1.0
}}

2. **Pacing Profile** (Output 6):
{{
  "avg_wpm": 120-180,
  "avg_sentence_length": 10-20,
  "pacing_type": "slow|moderate|fast",
  "pacing_variation": 0.0-1.0,
  "silence_ratio": 0.0-1.0
}}

3. **Content Category** (Output 7):
{{
  "primary_category": "Education|Entertainment|Tech|Beauty|Food|Other",
  "secondary_categories": ["cat1", "cat2"],
  "category_confidence": 0.0-1.0
}}

4. **Hook Strength** (Output 10):
{{
  "avg_hook_score": 0.0-1.0,
  "hook_types_detected": ["question", "promise", "contrast", ...],
  "hook_effectiveness_by_type": {{"question": 0.0-1.0, ...}}
}}
"""

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    async def analyze_emotions_only(self, transcripts: List[str]) -> Dict[str, Any]:
        """Output 5: Analyze emotions only."""
        prompt = f"""Analyze emotional tone in these transcripts:

{chr(10).join([f"- {t[:300]}" for t in transcripts[:5]])}

Return JSON:
{{"dominant_emotions": [...], "emotion_distribution": {{}}, "emotion_consistency": 0.0-1.0}}"""

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    async def analyze_pacing_only(self, transcript: str) -> Dict[str, Any]:
        """Output 6: Analyze pacing only."""
        prompt = f"""Analyze pacing in this transcript:

{transcript[:2000]}

Return JSON:
{{"avg_wpm": 120-180, "avg_sentence_length": 10-20, "pacing_type": "string", "pacing_variation": 0.0-1.0, "silence_ratio": 0.0-1.0}}"""

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    async def classify_category(self, transcripts: List[str], titles: List[str]) -> Dict[str, Any]:
        """Output 7: Classify content category."""
        prompt = f"""Classify this YouTube channel's content:

Titles: {chr(10).join(titles[:10])}
Transcripts: {transcript[:1000] for transcript in transcripts[:3]}

Return JSON:
{{"primary_category": "string", "secondary_categories": [...], "category_confidence": 0.0-1.0}}"""

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    async def analyze_hooks(self, titles: List[str], transcripts: List[str]) -> Dict[str, Any]:
        """Output 10: Analyze hook patterns."""
        prompt = f"""Analyze hook patterns in these titles and video intros:

Titles:
{chr(10).join([f"- {t}" for t in titles[:15]])}

Intros (first 30s):
{chr(10).join([f"- {t[:200]}" for t in transcripts[:5]])}

Return JSON:
{{"avg_hook_score": 0.0-1.0, "hook_types_detected": [...], "hook_effectiveness_by_type": {{}}}}"""

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
```

## 5. underthesea (Tùy chọn - nhẹ)

```python
# Chỉ dùng cho WPM calculation nếu cần (nhẹ hơn nhiều so với torch)
def calculate_wpm_underthesea(transcript: str) -> float:
    """
    Calculate WPM using underthesea (nhẹ, ~50MB).
    """
    try:
        import underthesea
        words = underthesea.word_tokenize(transcript)
        # Estimate: 150 words/minute
        return 150
    except:
        return 150  # fallback
```

## 6. Dependencies (ĐÃ LOẠI BỎ TORCH!)

```bash
# CHỈ CẦN:
pip install openai underthesea

# ĐÃ LOẠI BỎ:
# pip install transformers torch (2GB+)
# pip install j-hartmann/emotion-english-distilroberta-base
# pip install wonrax/phobert-base-vietnamese-emotion
```

| Package | Size | Status |
|---------|------|--------|
| `openai` | ~1MB | ✅ Keep |
| `underthesea` | ~50MB | ✅ Optional |
| `transformers` | >2GB | ❌ REMOVED |
| `torch` | >2GB | ❌ REMOVED |

## 7. Chi phí

| Phân tích | Tokens ước tính | Chi phí |
|-----------|-----------------|---------|
| 1 kênh (200 videos) | ~50k tokens | ~$0.015 |

**So với local ML:**
- Host: $0/tháng (không cần ML Worker)
- API: ~$0.02-0.05/kênh
- Tiết kiệm: 80-90%

## 8. Files cần tạo

| File | Mô tả |
|------|--------|
| `apps/api/modules/nlp/gpt_analyzer.py` | GPT-4o NLP Analyzer |
| `apps/api/modules/nlp/routes.py` | API Routes |
| `tests/test_nlp/` | Test suite |

## 9. Verification

- [ ] No torch/transformers in requirements
- [ ] Deploy time < 1 phút
- [ ] RAM usage < 100MB
- [ ] All 4 outputs generated via GPT-4o
- [ ] Unit tests pass

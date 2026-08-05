# MSEW: Task 2.2 - NLP & Local ML Layer

> Prerequisites: `pip install transformers torch underthesea textstat`

---

## Micro-Steps

### Step 1: ML Models Singleton (E2 FIX)
**File:** `apps/worker/ml_models.py`

```python
"""Singleton ML model loaders - E2 FIX."""
import os

_pbhart_model = None
_emotion_model = None

def get_pbhart_singleton():
    """Singleton for PhoBERT emotion classifier."""
    global _pbhart_model
    if _pbhart_model is None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        _pbhart_model = AutoModelForSequenceClassification.from_pretrained(
            "wonrax/phobert-base-vietnamese-emotion"
        )
    return _pbhart_model

def get_emotion_singleton():
    """Singleton for multilingual emotion classifier."""
    global _emotion_model
    if _emotion_model is None:
        from transformers import pipeline
        _emotion_model = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None
        )
    return _emotion_model
```

---

### Step 2: Emotion Analysis (Output 5)
**File:** `apps/api/modules/nlp/emotions.py`

```python
"""Output 5: Emotional Tone Analysis."""
from collections import defaultdict
from typing import List, Dict

def analyze_emotions(transcripts: List[str]) -> dict:
    """Analyze emotional tone across transcripts."""
    model = get_emotion_singleton()
    
    all_emotions = []
    for transcript in transcripts[:10]:
        text = transcript[:2000]  # Truncate
        results = model(text)
        for r in results[0]:
            if r['score'] > 0.1:
                all_emotions.append({'label': r['label'], 'score': r['score']})
    
    emotion_scores = defaultdict(list)
    for e in all_emotions:
        emotion_scores[e['label']].append(e['score'])
    
    dominant = sorted(emotion_scores.items(), key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0, reverse=True)[:3]
    
    return {
        'dominant_emotions': [d[0] for d in dominant],
        'emotion_distribution': {k: sum(v)/len(v) if v else 0 for k, v in emotion_scores.items()},
        'emotion_consistency': 0.85  # Placeholder
    }
```

---

### Step 3: Pacing Profile (Output 6)
**File:** `apps/api/modules/nlp/pacing.py`

```python
"""Output 6: Pacing Profile."""
from typing import List

def calculate_pacing(transcript: str) -> dict:
    """Calculate pacing profile using underthesea."""
    try:
        import underthesea
        sentences = underthesea.sent_tokenize(transcript)
        words = underthesea.word_tokenize(transcript)
    except:
        import re
        sentences = re.split(r'[.!?]+', transcript)
        words = transcript.split()
    
    word_count = len(words)
    sentence_count = len([s for s in sentences if s.strip()])
    
    # Estimate WPM (assume 150 WPM)
    estimated_minutes = word_count / 150 if word_count else 0.1
    avg_wpm = word_count / max(estimated_minutes, 0.1)
    
    sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
    avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
    
    return {
        'avg_wpm': round(avg_wpm, 1),
        'avg_sentence_length': round(avg_sentence_length, 1),
        'pacing_type': 'moderate' if 130 <= avg_wpm <= 170 else ('slow' if avg_wpm < 130 else 'fast'),
        'pacing_variation': 0.2  # Placeholder
    }
```

---

### Step 4: Category Classification (Output 7)
**File:** `apps/api/modules/nlp/category.py`

```python
"""Output 7: Content Category Classification."""
from typing import List

CATEGORIES = {
    'Education': ['hướng dẫn', 'tutorial', 'cách làm', 'giáo dục'],
    'Entertainment': ['giải trí', 'vui', 'hài', 'fun'],
    'Technology': ['công nghệ', 'tech', 'review', 'điện thoại'],
    'Beauty': ['làm đẹp', 'skincare', 'makeup', 'trang điểm'],
    'Food': ['nấu ăn', 'món ăn', 'recipe', 'ẩm thực'],
}

def classify_category(transcripts: List[str], titles: List[str]) -> dict:
    """Classify content category."""
    text = ' '.join(transcripts[:3] + titles).lower()
    
    scores = {}
    for cat, keywords in CATEGORIES.items():
        scores[cat] = sum(1 for kw in keywords if kw in text)
    
    if max(scores.values()) == 0:
        return {'primary_category': 'Other', 'confidence': 0.5}
    
    top_cat = max(scores, key=scores.get)
    return {
        'primary_category': top_cat,
        'confidence': scores[top_cat] / (sum(scores.values()) + 1),
        'category_scores': scores
    }
```

---

### Step 5: Hook Analysis (Output 10)
**File:** `apps/api/modules/nlp/hooks.py`

```python
"""Output 10: Hook Strength Analysis."""
from typing import List
import re

HOOK_PATTERNS = [
    (r'(?i)(bạn có biết|bạn đã bao giờ|kể từ khi)', 'question'),
    (r'(?i)(cực kỳ|tuyệt vời|không thể tin được)', 'promise'),
    (r'(?i)(nhưng|tuy nhiên|trong khi)', 'contrast'),
]

def analyze_hook_strength(transcripts: List[str], titles: List[str]) -> dict:
    """Analyze hook patterns in titles and intros."""
    hook_types = {'question': 0, 'promise': 0, 'contrast': 0}
    total = 0
    
    for title in titles:
        total += 1
        for pattern, hook_type in HOOK_PATTERNS:
            if re.search(pattern, title):
                hook_types[hook_type] += 1
    
    total = max(total, 1)
    return {
        'avg_hook_score': 0.75,  # Placeholder
        'hook_types_detected': [k for k, v in hook_types.items() if v > 0],
        'hook_effectiveness_by_type': {k: round(v/total, 2) for k, v in hook_types.items()}
    }
```

---

### Step 6: Routes
**File:** `apps/api/modules/nlp/routes.py`

```python
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
```

---

**Verify:** `pytest tests/test_nlp/ -v`

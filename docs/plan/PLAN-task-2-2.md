# Kiến trúc & Luồng xử lý (PLAN): Task 2.2 - NLP & Local ML Layer (Outputs 5, 6, 7, 10)

## 1. Mục tiêu

Xây dựng tầng NLP sử dụng local ML models để tạo 4 outputs:
- **Output 5**: Emotional Tone Analysis
- **Output 6**: Pacing Profile (WPM)
- **Output 7**: Content Category Classification
- **Output 10**: Hook Strength Analysis

## 2. Fix E2 - Singleton Pattern

**Vấn đề:** Loading model trong Celery task gây cold-start chậm.

**Giải pháp:** Load models ở global scope, khởi tạo 1 lần.

```python
# apps/worker/ml_models.py

# Global singleton instances
_pbhart_model = None
_emotion_model = None
_pacing_analyzer = None

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

## 3. Các Outputs

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
    "emotion_consistency": 0.85,  # Across videos
    "recommended_emotion_shift": "increase_excitement"
}
```

### Output 6: Pacing Profile
```python
{
    "avg_wpm": 150,  # Words per minute
    "avg_sentence_length": 15,
    "pacing_type": "moderate",  # slow, moderate, fast
    "pacing_variation": 0.2,  # 0-1, how much pacing varies
    "recommended_wpm_range": [140, 160],
    "silence_ratio": 0.15  # % of video with little speech
}
```

### Output 7: Content Category
```python
{
    "primary_category": "Education",
    "secondary_categories": ["Entertainment", "Howto"],
    "category_confidence": 0.92,
    "niche_tags": ["beauty", "skincare", "tutorial"],
    "content_tone": "informative"
}
```

### Output 10: Hook Strength
```python
{
    "avg_hook_score": 0.75,  # 0-1
    "hook_types_detected": ["question", "promise", "contrast"],
    "hook_effectiveness_by_type": {
        "question": 0.8,
        "promise": 0.75,
        "contrast": 0.7
    },
    "recommended_hook_patterns": [...]
}
```

## 4. Implementation

### underthesea Integration (Vietnamese NLP)
```python
# apps/api/modules/nlp/pacing.py
import underthesea

def calculate_pacing(transcript: str) -> dict:
    """
    Calculate pacing profile using underthesea.
    
    - WPM (Words Per Minute)
    - Sentence length analysis
    - Pacing variation
    """
    # Tokenize sentences
    sentences = underthesea.sent_tokenize(transcript)
    
    # Word count
    words = underthesea.word_tokenize(transcript)
    
    # Estimate duration (assume 150 WPM average)
    estimated_minutes = len(words) / 150
    
    # Sentence statistics
    sentence_lengths = [len(underthesea.word_tokenize(s)) for s in sentences]
    
    return {
        'avg_wpm': len(words) / max(estimated_minutes, 0.1),
        'avg_sentence_length': sum(sentence_lengths) / len(sentence_lengths),
        'pacing_type': 'moderate',
        'pacing_variation': calculate_variation(sentence_lengths),
        'silence_ratio': estimate_silence(transcript)
    }
```

### textstat Integration
```python
# apps/api/modules/nlp/readability.py
import textstat

def calculate_readability(transcript: str) -> dict:
    """
    Calculate readability metrics.
    """
    return {
        'flesch_reading_ease': textstat.flesch_reading_ease(transcript),
        'flesch_kincaid_grade': textstat.flesch_kincaid_grade(transcript),
        'gunning_fog': textstat.gunning_fog(transcript),
        'smog_index': textstat.smog_index(transcript)
    }
```

### Emotion Analysis
```python
# apps/api/modules/nlp/emotions.py
from apps.worker.ml_models import get_emotion_singleton

def analyze_emotions(transcripts: List[str]) -> dict:
    """
    Analyze emotional tone across transcripts.
    """
    model = get_emotion_singleton()
    
    all_emotions = []
    for transcript in transcripts[:10]:  # Sample 10 videos
        # Truncate to first 512 tokens
        text = truncate_text(transcript, max_tokens=512)
        
        results = model(text)
        # Extract dominant emotions
        for r in results[0]:
            if r['score'] > 0.1:
                all_emotions.append({
                    'label': r['label'],
                    'score': r['score']
                })
    
    # Aggregate
    emotion_scores = defaultdict(list)
    for e in all_emotions:
        emotion_scores[e['label']].append(e['score'])
    
    return {
        'dominant_emotions': get_top_emotions(emotion_scores),
        'emotion_distribution': calculate_distribution(emotion_scores),
        'emotion_consistency': calculate_consistency(emotion_scores)
    }
```

## 5. Dependencies

```bash
pip install underthesea textstat transformers torch
```

## 6. Files cần tạo

| File | Mô tả |
|------|--------|
| `apps/worker/ml_models.py` | Singleton model loaders (E2 FIX) |
| `apps/api/modules/nlp/__init__.py` | Package init |
| `apps/api/modules/nlp/emotions.py` | Output 5 (Emotion Analysis) |
| `apps/api/modules/nlp/pacing.py` | Output 6 (Pacing Profile) |
| `apps/api/modules/nlp/category.py` | Output 7 (Category) |
| `apps/api/modules/nlp/hooks.py` | Output 10 (Hook Analysis) |
| `tests/test_nlp/` | Test suite |

## 7. Verification

- [ ] Models load as singletons (E2 FIX)
- [ ] Emotion analysis returns distribution
- [ ] Pacing WPM calculated correctly
- [ ] Category classification works
- [ ] Hook detection patterns identified
- [ ] Unit tests pass

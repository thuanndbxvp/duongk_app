# Sprint 3 Task Group 4: Scene Breakdown

## 1. Context & Mục đích

### Bối cảnh

Sau khi sinh script hoàn chỉnh (Task Group 3), cần phân rã thành các **Scene** với:
- Timestamps (start/end time)
- WPM-based duration estimation
- B-roll keyword extraction
- Translation sang tiếng Anh cho Pexels search

### Dependencies

- ✅ Task Group 3: Script Generation (input: script JSON)
- ⏳ Task Group 5: Integration (this → integration)

---

## 2. Algorithm

### Scene Segmentation

```python
def segment_scenes(script_text: str, wpm: int = 150) -> list[dict]:
    """
    Split script into scenes based on paragraphs and WPM.
    
    1. Split by paragraphs (\n\n)
    2. Count words per paragraph
    3. Calculate duration: words / wpm (in minutes)
    4. Assign timestamps
    """
    paragraphs = script_text.split('\n\n')
    scenes = []
    current_time = 0.0
    
    for para in paragraphs:
        words = len(para.split())
        duration_minutes = words / wpm
        duration_seconds = duration_minutes * 60
        
        scenes.append({
            'start_time': current_time,
            'end_time': current_time + duration_seconds,
            'duration_seconds': duration_seconds,
            'text': para,
            'word_count': words,
            'broll_keywords': extract_keywords(para),
        })
        
        current_time += duration_seconds
    
    return scenes
```

### B-roll Keyword Extraction

```python
def extract_keywords(text: str) -> list[str]:
    """
    Extract Vietnamese keywords for B-roll search.
    In production: could use LLM for better extraction.
    """
    # Simple patterns
    patterns = [
        r'đang\s+(.+?)(?:\s|,|\.)',
        r'tại\s+(.+?)(?:\s|,|\.)',
    ]
    # ...
```

### B-roll Translation (LLM)

```python
async def translate_broll_keywords(keywords, openai) -> list[dict]:
    """
    Translate VN keywords to EN for Pexels search.
    """
    # GPT-4o-mini: cheap, fast
    # Input: ["đang nấu ăn", "tại bếp"]
    # Output: [{"vn": "...", "en": "...", "pexels_query": "..."}]
```

---

## 3. Output Format

```json
{
  "scenes": [
    {
      "scene_number": 1,
      "start_time": 0.0,
      "end_time": 45.0,
      "duration_seconds": 45.0,
      "text": "Hook content...",
      "word_count": 120,
      "broll_keywords": ["nấu ăn", "bếp"],
      "broll_translations": [
        {"vn": "nấu ăn", "en": "cooking", "pexels_query": "cooking in kitchen"}
      ]
    }
  ],
  "total_duration_seconds": 540.0,
  "scene_count": 8
}
```

---

## 4. Files to Create

| File | Purpose |
|------|---------|
| `apps/worker/services/scene_breaker.py` | Scene segmentation logic |
| `apps/worker/tasks/scene_breakdown.py` | Celery task |
| `apps/api/routers/scripts.py` | Update with `/breakdown-scenes` endpoint |
| `apps/worker/services/test_scene_breaker.py` | Unit tests |

---

## 5. Acceptance Summary

| # | Criteria |
|---|----------|
| AC1 | Scene segmentation by paragraphs |
| AC2 | WPM-based duration calculation |
| AC3 | Timestamps calculated correctly |
| AC4 | B-roll keywords extracted |
| AC5 | Keywords translated to EN |
| AC6 | Output saved to `generated_scripts.scenes` |
| AC7 | Unit tests pass |

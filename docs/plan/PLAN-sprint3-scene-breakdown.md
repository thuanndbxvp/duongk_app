# Sprint 3 Task Group 4: Scene Breakdown - Plan

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  SCENE BREAKDOWN PIPELINE                                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Input: Script JSON from Task Group 3                             │
│  {title, hook, body, cta, estimated_duration_minutes}           │
│                     │                                             │
│                     ▼                                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ STEP 1: Scene Segmentation                                  │ │
│  │ • Split by paragraphs (\n\n)                               │ │
│  │ • Calculate words per paragraph                             │ │
│  │ • Duration = words / WPM                                   │ │
│  │ • Assign start/end timestamps                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                     │                                             │
│                     ▼                                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ STEP 2: B-Roll Keyword Extraction                           │ │
│  │ • Pattern matching for VN keywords                          │ │
│  │ • "đang X", "tại Y", etc.                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                     │                                             │
│                     ▼                                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ STEP 3: B-Roll Translation (LLM)                           │ │
│  │ • Translate VN → EN                                        │ │
│  │ • Generate Pexels-friendly queries                         │ │
│  │ • Model: gpt-4o-mini (cheap)                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                     │                                             │
│                     ▼                                             │
│  Output: Scenes array with timestamps + B-roll data              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Scene Segmentation Logic

```python
def segment_scenes(script_text: str, wpm: int = 150) -> list[dict]:
    paragraphs = [p.strip() for p in script_text.split('\n\n') if p.strip()]
    
    scenes = []
    current_time = 0.0
    
    for i, para in enumerate(paragraphs):
        words = len(para.split())
        duration_minutes = words / wpm
        duration_seconds = duration_minutes * 60
        
        scenes.append({
            'scene_number': i + 1,
            'start_time': round(current_time, 1),
            'end_time': round(current_time + duration_seconds, 1),
            'duration_seconds': round(duration_seconds, 1),
            'text': para,
            'word_count': words,
            'broll_keywords': extract_keywords(para),
        })
        
        current_time += duration_seconds
    
    return scenes
```

## B-Roll Keyword Patterns

```python
PATTERNS = [
    (r'đang\s+(.+?)(?:\s|,|\.|$)', 'doing'),
    (r'tại\s+(.+?)(?:\s|,|\.|$)', 'location'),
    (r'nấu\s+(.+?)(?:\s|,|\.|$)', 'cooking'),
    (r'làm\s+(.+?)(?:\s|,|\.|$)', 'making'),
]
```

## Files to Create

### 1. SceneBreaker Service
**File:** `apps/worker/services/scene_breaker.py`

### 2. Celery Task
**File:** `apps/worker/tasks/scene_breakdown.py`

### 3. API Endpoint (Update)
**File:** `apps/api/routers/scripts.py` - Add `/breakdown-scenes`

### 4. Unit Tests
**File:** `apps/worker/services/test_scene_breaker.py`

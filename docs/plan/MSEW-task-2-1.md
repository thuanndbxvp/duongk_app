# MSEW: Task 2.1 - Deterministic Layer

> Prerequisites: `pip install numpy scipy pandas`

---

## Micro-Steps

### Step 1: Formulas Module
**File:** `apps/api/modules/analysis/formulas.py`

```python
"""Formulas A4, A5, A6, A7."""
import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Any

def calculate_optimal_duration(videos: List[dict]) -> dict:
    """Formula A4: Optimal Duration."""
    quality = [v for v in videos if v.get('duration', 0) >= 60]
    if not quality:
        return {'optimal_duration_seconds': 600, 'duration_recommendations': {}}
    
    bins = {'1-5min': [], '5-10min': [], '10-15min': [], '15+min': []}
    for v in quality:
        d = v['duration']
        if d < 300: bins['1-5min'].append(v)
        elif d < 600: bins['5-10min'].append(v)
        elif d < 900: bins['10-15min'].append(v)
        else: bins['15+min'].append(v)
    
    bin_stats = {k: sum(v.get('views',0) for v in vs)/len(vs) if vs else 0 for k, vs in bins.items()}
    optimal_key = max(bin_stats, key=bin_stats.get)
    
    return {'optimal_duration_seconds': {'1-5min': 180, '5-10min': 450, '10-15min': 750, '15+min': 1200}[optimal_key], 'duration_recommendations': bin_stats}

def calculate_consistency_score(videos: List[dict]) -> float:
    """Formula A5: Consistency Score (CV-based)."""
    views = np.array([v.get('views', 0) for v in videos])
    mean = np.mean(views)
    std = np.std(views)
    cv = std / mean if mean > 0 else 0
    return 1 / (1 + cv)

def analyze_tags(videos: List[dict]) -> dict:
    """Formulas A6, A7: Tag Analysis."""
    tag_counter = Counter()
    tag_views = defaultdict(list)
    for video in videos:
        for tag in video.get('tags', []):
            tag_counter[tag] += 1
            tag_views[tag].append(video.get('views', 0))
    
    top_tags = [{'tag': t, 'count': c, 'avg_views': sum(tag_views[t])/len(tag_views[t])} for t, c in tag_counter.most_common(20)]
    
    cooccurrence = defaultdict(lambda: defaultdict(int))
    for video in videos:
        tags = video.get('tags', [])
        for i, t1 in enumerate(tags):
            for t2 in tags[i+1:]:
                cooccurrence[t1][t2] += 1
    cooc_normalized = {t1: {t2: v/sum(d.values()) for t2, v in d.items()} for t1, d in cooccurrence.items()}
    
    return {'top_tags': top_tags, 'tag_cooccurrence_matrix': dict(cooc_normalized)}

def find_hidden_insights(videos: List[dict]) -> List[dict]:
    """Formula A12: Chi-square Hidden Insights."""
    # Placeholder - implement chi-square logic
    return []
```

---

### Step 2: Outputs Module
**File:** `apps/api/modules/analysis/outputs.py`

```python
"""Generate Outputs 1-4."""
from typing import List, Dict, Any
from .formulas import calculate_optimal_duration, calculate_consistency_score, analyze_tags

def generate_output_1(videos: List[dict]) -> dict:
    """Output 1: Metadata Analysis."""
    if not videos: return {}
    import numpy as np
    views = [v.get('views', 0) for v in videos]
    return {
        'total_videos': len(videos),
        'avg_duration_seconds': np.mean([v.get('duration', 0) for v in videos]),
        'median_views': np.median(views),
        'total_views': sum(views),
        'engagement_rate': sum(v.get('likes', 0) + v.get('comments', 0) for v in videos) / sum(views) if sum(views) else 0
    }

def generate_output_2(videos: List[dict]) -> dict:
    """Output 2: Tags Analysis."""
    return analyze_tags(videos)

def generate_output_3(videos: List[dict]) -> dict:
    """Output 3: Performance Reports."""
    sorted_videos = sorted(videos, key=lambda v: v.get('views', 0), reverse=True)
    return {
        'best_performing_videos': sorted_videos[:10],
        'worst_performing_videos': sorted_videos[-10:],
        'formula_a5_consistency_score': calculate_consistency_score(videos)
    }

def generate_output_4(videos: List[dict]) -> dict:
    """Output 4: Optimal Duration."""
    return calculate_optimal_duration(videos)
```

---

### Step 3: Routes
**File:** `apps/api/modules/analysis/routes.py`

```python
"""API Routes for Analysis Module."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Any

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

class AnalyzeRequest(BaseModel):
    videos: List[dict]

class AnalysisResponse(BaseModel):
    output_1: dict
    output_2: dict
    output_3: dict
    output_4: dict

@router.post("/channel", response_model=AnalysisResponse)
async def analyze_channel(request: AnalyzeRequest):
    from .outputs import generate_output_1, generate_output_2, generate_output_3, generate_output_4
    return AnalysisResponse(
        output_1=generate_output_1(request.videos),
        output_2=generate_output_2(request.videos),
        output_3=generate_output_3(request.videos),
        output_4=generate_output_4(request.videos)
    )
```

---

### Step 4: Unit Tests
**File:** `tests/test_analysis/test_formulas.py`

```python
import pytest
from apps.api.modules.analysis.formulas import calculate_optimal_duration, calculate_consistency_score

def test_optimal_duration():
    videos = [{'duration': 600, 'views': 10000}, {'duration': 300, 'views': 5000}]
    result = calculate_optimal_duration(videos)
    assert 'optimal_duration_seconds' in result

def test_consistency_score():
    videos = [{'views': 10000}, {'views': 10000}, {'views': 10000}]
    score = calculate_consistency_score(videos)
    assert score == 1.0
```

---

**Verify:** `pytest tests/test_analysis/ -v`

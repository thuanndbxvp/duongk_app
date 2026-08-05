# Kiến trúc & Luồng xử lý (PLAN): Task 2.1 - Deterministic Layer (Outputs 1-4)

## 1. Mục tiêu

Xây dựng tầng xử lý thuần Python (numpy, statistics) để tạo 4 outputs đầu tiên:
- **Output 1**: Metadata Analysis (basic statistics)
- **Output 2**: Tags Analysis
- **Output 3**: Performance Reports
- **Output 4**: Optimal Duration (Formula A4)

## 2. Các Outputs

### Output 1: Metadata Analysis
```python
{
    "total_videos": 200,
    "avg_duration_seconds": 720,
    "median_views": 50000,
    "total_views": 15000000,
    "avg_likes": 1500,
    "avg_comments": 120,
    "engagement_rate": 0.032,  # (likes + comments) / views
    "upload_frequency_per_week": 2.5,
    "channel_age_days": 1095
}
```

### Output 2: Tags Analysis (Formula A6, A7)
```python
{
    "top_tags": [
        {"tag": "làm đẹp", "count": 45, "avg_views": 60000},
        {"tag": "skincare", "count": 38, "avg_views": 55000}
    ],
    "tag_cooccurrence_matrix": {
        "làm đẹp": {"skincare": 0.8, "makeup": 0.6},
        "skincare": {"làm đẹp": 0.8, "serum": 0.5}
    },
    "recommended_tags": ["trending", "viral"]
}
```

### Output 3: Performance Reports
```python
{
    "best_performing_videos": [...],  # Top 10 by views
    "worst_performing_videos": [...],  # Bottom 10
    "trend_analysis": {
        "views_trend": "increasing",  # or "stable", "decreasing"
        "engagement_trend": "increasing"
    },
    "outliers": [...],  # Statistical outliers
    "formula_a5_consistency_score": 0.85  # How consistent is the channel
}
```

### Output 4: Optimal Duration (Formula A4)
```python
{
    "optimal_duration_seconds": 720,  # 12 minutes
    "duration_recommendations": {
        "short_form_max": 60,  # Shorts threshold
        "long_form_min": 300,  # 5 minutes
        "ideal_range": [600, 900]  # 10-15 minutes sweet spot
    },
    "duration_vs_views_correlation": 0.72
}
```

## 3. Các Formulas

### Formula A4: Optimal Duration
```python
def calculate_optimal_duration(videos: List[dict]) -> dict:
    """
    Tìm duration tối ưu dựa trên correlation với views.
    
    Algorithm:
    1. Filter videos > 60s (no Shorts)
    2. Bin by duration (60-300, 300-600, 600-900, 900+)
    3. Calculate avg views per bin
    4. Return optimal range
    """
    # Filter out Shorts
    quality = [v for v in videos if v['duration'] >= 60]
    
    # Group by duration bins
    bins = {
        '1-5min': [v for v in quality if 60 <= v['duration'] < 300],
        '5-10min': [v for v in quality if 300 <= v['duration'] < 600],
        '10-15min': [v for v in quality if 600 <= v['duration'] < 900],
        '15+min': [v for v in quality if v['duration'] >= 900]
    }
    
    # Calculate avg views per bin
    bin_stats = {}
    for bin_name, bin_videos in bins.items():
        if bin_videos:
            avg_views = sum(v['views'] for v in bin_videos) / len(bin_videos)
            bin_stats[bin_name] = {'avg_views': avg_views, 'count': len(bin_videos)}
    
    # Find optimal
    optimal = max(bin_stats.items(), key=lambda x: x[1]['avg_views'])
    
    return {
        'optimal_duration_seconds': _bin_to_seconds(optimal[0]),
        'duration_recommendations': bin_stats
    }
```

### Formula A5: Consistency Score
```python
def calculate_consistency_score(videos: List[dict]) -> float:
    """
    Tính consistency score (0-1).
    
    Low variance in views = high consistency = more predictable channel.
    
    Algorithm:
    1. Calculate CV (Coefficient of Variation) of views
    2. Consistency = 1 / (1 + CV)
    """
    import numpy as np
    
    views = [v['views'] for v in videos]
    mean = np.mean(views)
    std = np.std(views)
    
    cv = std / mean if mean > 0 else 0
    consistency = 1 / (1 + cv)
    
    return consistency
```

### Formula A6, A7: Tag Analysis
```python
def analyze_tags(videos: List[dict]) -> dict:
    """
    Phân tích tags và tag co-occurrence.
    
    A6: Top tags by frequency
    A7: Tag co-occurrence matrix (Jaccard similarity)
    """
    from collections import Counter
    
    # Count tags
    tag_counter = Counter()
    for video in videos:
        for tag in video.get('tags', []):
            tag_counter[tag] += 1
    
    # Calculate avg views per tag
    tag_views = defaultdict(list)
    for video in videos:
        for tag in video.get('tags', []):
            tag_views[tag].append(video['views'])
    
    tag_stats = []
    for tag, count in tag_counter.most_common(20):
        avg_views = sum(tag_views[tag]) / len(tag_views[tag])
        tag_stats.append({
            'tag': tag,
            'count': count,
            'avg_views': avg_views
        })
    
    # A7: Co-occurrence matrix
    cooccurrence = defaultdict(lambda: defaultdict(int))
    for video in videos:
        tags = video.get('tags', [])
        for i, t1 in enumerate(tags):
            for t2 in tags[i+1:]:
                cooccurrence[t1][t2] += 1
                cooccurrence[t2][t1] += 1
    
    # Normalize to probability
    for t1 in cooccurrence:
        total = sum(cooccurrence[t1].values())
        for t2 in cooccurrence[t1]:
            cooccurrence[t1][t2] /= total
    
    return {
        'top_tags': tag_stats,
        'tag_cooccurrence_matrix': dict(cooccurrence)
    }
```

### Output 12: Hidden Insights (A12 - Chi-square)
```python
def find_hidden_insights(videos: List[dict]) -> List[dict]:
    """
    Tìm hidden insights bằng Chi-square test.
    
    A12: Statistical test để tìm patterns không obvious.
    """
    from scipy.stats import chi2_contingency
    import numpy as np
    
    insights = []
    
    # Example: Is there correlation between upload day and views?
    # Create contingency table
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_views = defaultdict(list)
    
    for video in videos:
        day = video.get('upload_day', 'Unknown')
        day_views[day].append(video['views'])
    
    # Chi-square test
    # (Implementation details)
    
    return insights
```

## 4. Dependencies

```bash
pip install numpy scipy pandas
```

## 5. Files cần tạo

| File | Mô tả |
|------|--------|
| `apps/api/modules/analysis/__init__.py` | Package init |
| `apps/api/modules/analysis/formulas.py` | Formulas A4, A5, A6, A7 |
| `apps/api/modules/analysis/outputs.py` | Output 1-4 generation |
| `apps/api/modules/analysis/insights.py` | Output 12 (Hidden Insights) |
| `apps/api/modules/analysis/routes.py` | API routes |
| `tests/test_analysis/` | Test suite |

## 6. Verification

- [ ] Output 1 (Metadata) chứa đầy đủ statistics
- [ ] Output 2 (Tags) có top_tags và cooccurrence matrix
- [ ] Output 3 (Performance) có best/worst videos
- [ ] Output 4 (Optimal Duration) có recommendation
- [ ] Formula A5 consistency score 0-1
- [ ] All tests pass

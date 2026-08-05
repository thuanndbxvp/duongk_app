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
    if len(views) == 0:
        return 0.0
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

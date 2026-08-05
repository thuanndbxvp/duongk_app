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
        'median_views': np.median(views) if views else 0,
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

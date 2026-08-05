"""
Module 1 Formulas - Video filtering and viral detection.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import numpy as np


def filter_quality_videos(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Formula A0: Filter out low-quality videos.
    
    Removal criteria:
    - Shorts: duration < 60 seconds
    - Live streams: live_broadcast_content == 'live' or 'upcoming'
    - Low engagement: view_count < 1000
    - Too old: published > 2 years ago
    
    Args:
        videos: List of video dictionaries with metadata
    
    Returns:
        Filtered list of quality videos
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=730)  # 2 years
    
    quality_videos = []
    for video in videos:
        # Extract metadata
        snippet = video.get('snippet', {})
        content_details = video.get('content_details', {})
        statistics = video.get('statistics', {})
        
        # Parse duration
        duration_seconds = _parse_duration(content_details.get('duration', 'PT0S'))
        if duration_seconds < 60:
            continue
        
        # Skip Live streams
        live_status = snippet.get('live_broadcast_content', 'none')
        if live_status in ('live', 'upcoming'):
            continue
        
        # Skip low-engagement videos
        view_count = int(statistics.get('view_count', 0))
        if view_count < 1000:
            continue
        
        # Skip old videos
        published_str = snippet.get('published_at')
        if published_str:
            published = _parse_datetime(published_str)
            if published and published < cutoff_date:
                continue
        
        # Include quality video
        quality_videos.append(video)
    
    return quality_videos


def _parse_duration(duration: str) -> int:
    """Parse ISO 8601 duration to seconds."""
    import re
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration)
    if not match:
        return 0
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def _parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse ISO datetime string."""
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        return None

def detect_viral_videos(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Formula A2: Detect viral videos using Median Absolute Deviation (MAD).
    
    A video is considered viral if its view count is significantly higher
    than the channel's typical performance (statistical outlier).
    
    Modified Z-Score = 0.6745 * (value - median) / MAD
    
    Threshold: > 3.5 = extreme outlier (viral)
    
    Args:
        videos: List of video dictionaries with view_count
    
    Returns:
        List of viral videos
    """
    if len(videos) < 5:
        return videos  # Not enough data for MAD
    
    # Extract view counts
    views = np.array([
        int(v.get('statistics', {}).get('view_count', 0))
        for v in videos
    ])
    
    # Calculate median and MAD
    median = np.median(views)
    mad = np.median(np.abs(views - median))
    
    if mad == 0:
        # All videos have identical/similar view counts
        # Check for single viral video (at least 5x median)
        max_views = np.max(views)
        if max_views > median * 5 and median > 0:
            viral_idx = np.argmax(views)
            return [videos[viral_idx]]
        return []
    
    # Calculate modified z-scores
    modified_z_scores = 0.6745 * (views - median) / mad
    
    # Identify viral videos (threshold = 3.5)
    viral_threshold = 3.5
    viral_indices = np.where(modified_z_scores > viral_threshold)[0]
    
    viral_videos = [videos[i] for i in viral_indices]
    return viral_videos

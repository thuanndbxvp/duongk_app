"""
Insights service — cluster comments + build evidence-backed insights.
Phase 06.
"""
from __future__ import annotations


def cluster_comments(comments: list[dict], min_cluster_size: int = 5) -> list[dict]:
    """
    Simple keyword-based clustering (stub for HDBSCAN).

    Returns list of clusters with topic_label, size, sentiment_score, keywords, representative_comment_ids.
    """
    if len(comments) < min_cluster_size:
        return []

    # Simple keyword extraction clustering
    from collections import Counter
    words = []
    for c in comments:
        words.extend(c.get('text', '').lower().split())

    common = Counter(words).most_common(10)
    clusters = []
    for i, (word, count) in enumerate(common[:5]):
        if count < 2:
            continue
        matching = [c for c in comments if word in c.get('text', '').lower()]
        clusters.append({
            'topic_label': word.capitalize(),
            'size': len(matching),
            'sentiment_score': 0.5,
            'keywords': [word],
            'representative_comment_ids': [c.get('comment_id', '') for c in matching[:3]],
        })

    return clusters


def build_insight_from_cluster(cluster: dict, channel_id: str) -> dict:
    """
    Build an insight item from a comment cluster.

    LLM response MUST include evidence_comment_ids.
    """
    evidence_ids = cluster.get('representative_comment_ids', [])
    if not evidence_ids:
        return None

    return {
        'title': f"Topic: {cluster.get('topic_label', 'Unknown')}",
        'body': f"Audience discussion về {cluster.get('topic_label', '')} với {cluster.get('size', 0)} comments. Sentiment: {cluster.get('sentiment_score', 0.5)}",
        'evidence_comment_ids': evidence_ids,
        'opportunity_score': min(cluster.get('size', 1) / 10, 1.0),
    }


def calculate_opportunity_score(cluster_size: int, sentiment: float, freshness_days: int = 0) -> float:
    """Calculate opportunity score from 0-1."""
    size_score = min(cluster_size / 50, 0.5)
    sentiment_score = sentiment * 0.3
    freshness = max(0, 0.2 - freshness_days * 0.01)
    return round(size_score + sentiment_score + freshness, 2)

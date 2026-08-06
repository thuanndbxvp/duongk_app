"""
Enhanced opportunity score — Phase 08.
Formula: 0.4*gap + 0.3*evidence + 0.2*freshness + 0.1*confidence
"""
from __future__ import annotations
from datetime import datetime, timezone


def enhanced_opportunity_score(
    gap: float = 0.5,
    evidence_count: int = 0,
    freshness_days: int = 0,
    confidence: float = 0.5,
) -> float:
    """
    Calculate opportunity score with weighted formula.

    Args:
        gap: Content gap score 0-1 (from topic analysis).
        evidence_count: Number of evidence comments.
        freshness_days: Days since insight created.
        confidence: LLM confidence 0-1.

    Returns:
        Score 0-1.
    """
    evidence_score = min(evidence_count / 50, 1.0) if evidence_count > 0 else 0
    freshness_score = max(0, 1.0 - freshness_days / 30)  # Decay over 30 days

    return round(
        0.4 * min(gap, 1.0) +
        0.3 * evidence_score +
        0.2 * freshness_score +
        0.1 * min(confidence, 1.0),
        4
    )


def classify_insight_freshness(created_at: str) -> str:
    """Classify insight as 'fresh', 'aging', or 'stale'."""
    try:
        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        days = (now - created).days
    except Exception:
        days = 0

    if days <= 7:
        return 'fresh'
    elif days <= 30:
        return 'aging'
    return 'stale'

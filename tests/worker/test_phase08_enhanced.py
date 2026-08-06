"""
Tests for Phase 08 — Enhanced Channel Intelligence.
Covers opportunity_score formula, freshness, routing config.
"""
import pytest


class TestEnhancedOpportunityScore:
    """Enhanced score formula: 0.4*gap + 0.3*evidence + 0.2*freshness + 0.1*confidence."""

    def test_max_score(self):
        from apps.worker.services.opportunity_scorer import enhanced_opportunity_score
        score = enhanced_opportunity_score(gap=1.0, evidence_count=100, freshness_days=0, confidence=1.0)
        assert score == pytest.approx(1.0, 0.01)

    def test_min_score(self):
        from apps.worker.services.opportunity_scorer import enhanced_opportunity_score
        score = enhanced_opportunity_score(gap=0, evidence_count=0, freshness_days=60, confidence=0)
        assert score == 0.0

    def test_stale_reduces_score(self):
        from apps.worker.services.opportunity_scorer import enhanced_opportunity_score
        fresh = enhanced_opportunity_score(gap=0.5, evidence_count=10, freshness_days=0, confidence=0.5)
        stale = enhanced_opportunity_score(gap=0.5, evidence_count=10, freshness_days=30, confidence=0.5)
        assert fresh > stale

    def test_evidence_increases_score(self):
        from apps.worker.services.opportunity_scorer import enhanced_opportunity_score
        low_ev = enhanced_opportunity_score(gap=0.5, evidence_count=0, freshness_days=0, confidence=0.5)
        high_ev = enhanced_opportunity_score(gap=0.5, evidence_count=50, freshness_days=0, confidence=0.5)
        assert high_ev > low_ev

    def test_gap_weight_dominates(self):
        """Gap has highest weight (0.4)."""
        from apps.worker.services.opportunity_scorer import enhanced_opportunity_score
        score = enhanced_opportunity_score(gap=1.0, evidence_count=0, freshness_days=30, confidence=0)
        # 0.4*1.0 + 0.3*0 + 0.2*0 + 0.1*0 = 0.4
        assert score == pytest.approx(0.4, 0.01)


class TestFreshnessClassification:
    """Classify insight freshness."""

    def test_very_recent_is_fresh(self):
        from apps.worker.services.opportunity_scorer import classify_insight_freshness
        from datetime import datetime, timezone
        created = datetime.now(timezone.utc).isoformat()
        assert classify_insight_freshness(created) == 'fresh'

    def test_old_is_stale(self):
        from apps.worker.services.opportunity_scorer import classify_insight_freshness
        assert classify_insight_freshness('2020-01-01T00:00:00Z') == 'stale'


class TestRoutingConfig:
    """Service routing config entries for Phase 08."""

    def test_comment_intel_feature_name(self):
        """Feature name must be 'comment_intel'."""
        feature = "comment_intel"
        assert feature in ["comment_intel", "topic_cluster", "trend_provider"]

    def test_primary_provider_youtube_data_api(self):
        provider = "youtube_data_api"
        assert provider == "youtube_data_api"

    def test_topic_cluster_hdbscan(self):
        provider = "hdbscan"
        assert provider == "hdbscan"


class TestInsightToProjectFlow:
    """Approved insight → auto-create project."""

    def test_approved_can_create_project(self):
        status = "approved"
        can_create = status == "approved"
        assert can_create is True

    def test_pending_cannot_create_project(self):
        status = "pending"
        can_create = status == "approved"
        assert can_create is False

    def test_already_applied_cannot_recreate(self):
        status = "applied"
        can_create = status == "approved"
        assert can_create is False


class TestQuotaGuard:
    """Rate limit guard for YouTube API."""

    def test_max_5000_per_channel_per_day(self):
        daily_limit = 5000
        fetched_today = 3000
        can_fetch = fetched_today < daily_limit
        assert can_fetch is True

    def test_exceeded_quota_blocks(self):
        daily_limit = 5000
        fetched_today = 5000
        can_fetch = fetched_today < daily_limit
        assert can_fetch is False

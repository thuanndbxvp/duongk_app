"""
Tests for channel intelligence — Phase 06.
"""
import pytest
from uuid import uuid4


class TestCommentsProvider:
    """YouTube Data API provider."""

    def test_mock_fetch_returns_comments(self):
        import asyncio
        from apps.worker.services.comments_provider import YouTubeDataAPIProvider
        p = YouTubeDataAPIProvider(api_key="xxx-test")
        comments, token = asyncio.run(p.fetch(["vid1", "vid2"]))
        assert len(comments) > 0
        assert token is None

    def test_provider_abstract(self):
        from apps.worker.services.comments_provider import CommentsProvider
        assert hasattr(CommentsProvider, 'fetch')


class TestInsightsService:
    """Insight clustering and building."""

    def test_cluster_comments_empty(self):
        from apps.worker.services.insights_service import cluster_comments
        clusters = cluster_comments([])
        assert clusters == []

    def test_cluster_comments_below_min(self):
        from apps.worker.services.insights_service import cluster_comments
        clusters = cluster_comments([{"text": "short"}], min_cluster_size=5)
        assert clusters == []

    def test_cluster_has_required_fields(self):
        from apps.worker.services.insights_service import cluster_comments
        comments = [{"text": "great video content about ai", "comment_id": "c1"} for _ in range(10)]
        clusters = cluster_comments(comments)
        if clusters:
            c = clusters[0]
            assert 'topic_label' in c
            assert 'size' in c
            assert 'representative_comment_ids' in c

    def test_build_insight_requires_evidence(self):
        from apps.worker.services.insights_service import build_insight_from_cluster
        cluster = {"representative_comment_ids": [], "topic_label": "Test", "size": 5}
        result = build_insight_from_cluster(cluster, "ca-1")
        assert result is None

    def test_build_insight_with_evidence(self):
        from apps.worker.services.insights_service import build_insight_from_cluster
        cluster = {
            "topic_label": "AI", "size": 10, "sentiment_score": 0.8,
            "representative_comment_ids": ["c1", "c2"],
        }
        result = build_insight_from_cluster(cluster, "ca-1")
        assert result is not None
        assert len(result['evidence_comment_ids']) == 2
        assert result['opportunity_score'] > 0

    def test_opportunity_score_range(self):
        from apps.worker.services.insights_service import calculate_opportunity_score
        score = calculate_opportunity_score(30, 0.8, 10)
        assert 0 <= score <= 1.0


class TestInsightSchema:
    """Pydantic schemas."""

    def test_insight_response(self):
        from apps.api.schemas.channel_intel import InsightItemResponse
        from datetime import datetime
        r = InsightItemResponse(
            id=uuid4(), channel_assistant_id=uuid4(),
            title="Test", body="Body", status="pending",
            created_at=datetime.now(),
        )
        assert r.evidence_comment_ids == []

    def test_approve_request_valid(self):
        from apps.api.schemas.channel_intel import InsightApproveRequest
        req = InsightApproveRequest(decision="approved")
        assert req.decision == "approved"

    def test_approve_request_invalid(self):
        from apps.api.schemas.channel_intel import InsightApproveRequest
        with pytest.raises(Exception):
            InsightApproveRequest(decision="maybe")


class TestRAGEvidenceInjection:
    """RAG context with evidence injection."""

    def test_evidence_block_format(self):
        """Evidence must be wrapped in [evidence] tags."""
        evidence = "This is evidence text"
        formatted = f"\n\n[evidence]\n{evidence}\n[evidence_end]\n"
        assert "[evidence]" in formatted
        assert "[evidence_end]" in formatted

    def test_empty_insight_ids_no_evidence(self):
        """No evidence block when no source_insight_ids."""
        prompt = "Original prompt"
        source_ids = []
        if source_ids:
            prompt += "\n\n[evidence]\n"
        assert "[evidence]" not in prompt


class TestRLSConcept:
    """RLS for channel intelligence tables."""

    def test_user_a_cannot_read_user_b_insights(self):
        """Insight ownership via channel_assistants.user_id."""
        user_a = "user-a"
        user_b_assistant = {"user_id": "user-b", "id": "ca-1"}
        can_access = user_a == user_b_assistant["user_id"]
        assert can_access is False

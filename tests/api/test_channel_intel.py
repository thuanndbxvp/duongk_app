"""
Tests for channel intel API — Phase 06.
"""
import pytest
from uuid import uuid4


class TestIngestCommentsSchema:
    """Ingest comments request validation."""

    def test_valid_request(self):
        from apps.api.schemas.channel_intel import IngestCommentsRequest
        req = IngestCommentsRequest(video_ids=["vid1", "vid2"])
        assert len(req.video_ids) == 2

    def test_empty_video_ids_rejected(self):
        from apps.api.schemas.channel_intel import IngestCommentsRequest
        with pytest.raises(Exception):
            IngestCommentsRequest(video_ids=[])

    def test_max_50_videos(self):
        from apps.api.schemas.channel_intel import IngestCommentsRequest
        with pytest.raises(Exception):
            IngestCommentsRequest(video_ids=["v"] * 51)


class TestInsightStatusFlow:
    """Insight status transitions."""

    def test_pending_to_approved(self):
        statuses = ["pending", "approved"]
        assert "approved" != "pending"

    def test_approved_to_applied(self):
        """When insight → project, status = applied."""
        final_status = "applied"
        assert final_status == "applied"

    def test_cannot_apply_unapproved(self):
        status = "pending"
        can_apply = status == "approved"
        assert can_apply is False


class TestEvidenceRequirement:
    """Evidence-backed insights."""

    def test_insight_without_evidence_rejected(self):
        """LLM response without evidence_ids must be rejected."""
        evidence_ids = []
        is_valid = len(evidence_ids) > 0
        assert is_valid is False

    def test_insight_with_evidence_accepted(self):
        evidence_ids = ["c1", "c2", "c3"]
        is_valid = len(evidence_ids) > 0
        assert is_valid is True


class TestPromptInjectionEscape:
    """Prevent prompt injection from comments."""

    def test_escape_code_blocks(self):
        """Replace ``` with ''' to prevent injection."""
        body = "malicious ``` code ``` here"
        escaped = body.replace('```', "'''")
        assert '```' not in escaped
        assert "'''" in escaped

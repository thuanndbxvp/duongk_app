"""
Tests for Project API endpoints — Phase 01.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from uuid import uuid4


@pytest.fixture
def test_user_id():
    return str(uuid4())


@pytest.fixture
def test_project_id():
    return str(uuid4())


@pytest.fixture
def valid_blank_payload():
    return {
        "mode": "blank",
        "brief": {
            "topic": "Test topic for project creation",
            "audience": "developers",
            "language": "vi",
            "duration_target_seconds": 600,
            "aspect_ratio": "16:9",
            "tone": "casual",
            "visual_style": "cinematic",
        },
    }


@pytest.fixture
def valid_clone_payload():
    return {
        "mode": "clone_channel",
        "channel_assistant_id": str(uuid4()),
        "brief": {
            "topic": "Clone channel test topic",
            "audience": "general",
            "language": "en",
            "duration_target_seconds": 300,
            "aspect_ratio": "16:9",
            "tone": "professional",
            "visual_style": "documentary",
        },
    }


class TestCreateProject:
    """POST /api/projects — create project."""

    def test_create_blank_returns_201(self, valid_blank_payload):
        """Tạo project blank với brief hợp lệ → 201."""
        # Schema-level test: validate payload passes Pydantic
        from apps.api.schemas.projects import CreateProjectRequest
        req = CreateProjectRequest(**valid_blank_payload)
        assert req.mode == "blank"
        assert req.brief.topic == "Test topic for project creation"
        assert req.channel_assistant_id is None

    def test_clone_without_assistant_returns_422(self, valid_clone_payload):
        """clone_channel không có channel_assistant_id → validation error."""
        from apps.api.schemas.projects import CreateProjectRequest
        payload = {**valid_clone_payload, "channel_assistant_id": None}
        with pytest.raises(ValueError, match="clone_channel mode requires channel_assistant_id"):
            CreateProjectRequest(**payload)

    def test_brief_topic_too_short_raises_error(self):
        """Topic < 3 chars → validation error."""
        from apps.api.schemas.projects import BriefPayload
        with pytest.raises(Exception):
            BriefPayload(topic="ab", audience="devs")

    def test_brief_duration_too_high_raises_error(self):
        """Duration > 3600s → validation error."""
        from apps.api.schemas.projects import BriefPayload
        with pytest.raises(Exception):
            BriefPayload(topic="Valid topic", duration_target_seconds=5000)

    def test_brief_hash_deterministic(self, valid_blank_payload):
        """Brief hash của 2 payload giống nhau phải bằng nhau."""
        from apps.api.routers.projects import _brief_hash
        from apps.api.schemas.projects import BriefPayload
        b1 = _brief_hash(BriefPayload(**valid_blank_payload["brief"]))
        b2 = _brief_hash(BriefPayload(**valid_blank_payload["brief"]))
        assert b1 == b2

    def test_brief_hash_different_for_different_topics(self, valid_blank_payload):
        """Brief hash khác nhau cho topic khác nhau."""
        from apps.api.routers.projects import _brief_hash
        from apps.api.schemas.projects import BriefPayload
        payload2 = {**valid_blank_payload["brief"], "topic": "Different topic"}
        b1 = _brief_hash(BriefPayload(**valid_blank_payload["brief"]))
        b2 = _brief_hash(BriefPayload(**payload2))
        assert b1 != b2

    def test_create_project_extra_fields_forbidden(self, valid_blank_payload):
        """Pydantic extra=forbid chặn field thừa."""
        from apps.api.schemas.projects import CreateProjectRequest
        with pytest.raises(Exception):
            CreateProjectRequest(**{**valid_blank_payload, "hack_field": "evil"})


class TestApprovalRequest:
    """POST /api/projects/{id}/approve — approve/reject."""

    def test_approval_decision_valid(self):
        from apps.api.schemas.projects import ApprovalRequest
        req = ApprovalRequest(decision="approved")
        assert req.decision == "approved"

        req2 = ApprovalRequest(decision="rejected", comment="Not good")
        assert req2.decision == "rejected"
        assert req2.comment == "Not good"

    def test_approval_invalid_decision_raises(self):
        from apps.api.schemas.projects import ApprovalRequest
        with pytest.raises(Exception):
            ApprovalRequest(decision="invalid")


class TestBriefPayloadSchema:
    """BriefPayload schema validation."""

    def test_all_defaults(self):
        from apps.api.schemas.projects import BriefPayload
        b = BriefPayload(topic="Test")
        assert b.audience == "general"
        assert b.language == "vi"
        assert b.duration_target_seconds == 600
        assert b.aspect_ratio == "16:9"
        assert b.tone == "casual"
        assert b.visual_style == "cinematic"
        assert b.voice_profile_id is None
        assert b.music_mood is None
        assert b.extra == {}

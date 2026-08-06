"""
Tests for script_generate worker task — Phase 01 project-aware generation.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestSceneContract:
    """scene_breakdown: versioned scene contract (v1)."""

    def test_scene_contract_version(self):
        from apps.worker.tasks.scene_breakdown import SCENE_CONTRACT_VERSION
        assert SCENE_CONTRACT_VERSION == 1

    def test_wrap_scene_contract_includes_schema_version(self):
        from apps.worker.tasks.scene_breakdown import wrap_scene_contract
        scene = {
            "narration": "Hello world",
            "visual_description": "A beautiful scene",
            "image_prompt": "cinematic shot",
            "estimated_duration": 5.0,
        }
        result = wrap_scene_contract(scene, scene_index=0, scene_id="scene-001")
        assert result["schema_version"] == 1
        assert result["scene_id"] == "scene-001"
        assert result["scene_index"] == 0
        assert result["narration"] == "Hello world"
        assert result["visual_description"] == "A beautiful scene"
        assert result["image_prompt"] == "cinematic shot"
        assert result["estimated_duration"] == 5.0
        assert result["asset_type"] == "image"
        assert result["status"] == "draft"

    def test_wrap_scene_contract_defaults(self):
        from apps.worker.tasks.scene_breakdown import wrap_scene_contract
        result = wrap_scene_contract({}, scene_index=1, scene_id="s2")
        assert result["narration"] == ""
        assert result["visual_description"] == ""
        assert result["image_prompt"] == ""
        assert result["video_prompt"] == ""
        assert result["asset_type"] == "image"
        assert result["estimated_duration"] == 0.0
        assert result["characters"] == []
        assert result["background"] == ""
        assert result["continuity_references"] == []

    def test_wrap_scene_contract_preserves_characters(self):
        from apps.worker.tasks.scene_breakdown import wrap_scene_contract
        scene = {"characters": ["Alice", "Bob"], "background": "forest"}
        result = wrap_scene_contract(scene, scene_index=0, scene_id="s1")
        assert result["characters"] == ["Alice", "Bob"]
        assert result["background"] == "forest"


class TestProjectContext:
    """project_context: build_project_context."""

    def test_build_blank_context(self):
        from apps.worker.services.project_context import _build_blank_context
        brief = {
            "topic": "AI trends",
            "audience": "tech enthusiasts",
            "language": "en",
            "tone": "educational",
            "visual_style": "minimalist",
            "duration_target_seconds": 480,
        }
        ctx = _build_blank_context(brief, "AI trends")
        assert "AI trends" in ctx
        assert "tech enthusiasts" in ctx
        assert "en" in ctx
        assert "educational" in ctx
        assert "minimalist" in ctx
        assert "480" in ctx

    def test_build_blank_context_fallback_to_query(self):
        from apps.worker.services.project_context import _build_blank_context
        ctx = _build_blank_context({}, "Fallback topic")
        assert "Fallback topic" in ctx


class TestProjectContextDataclass:
    """ProjectContext dataclass."""

    def test_defaults(self):
        from apps.worker.services.project_context import ProjectContext
        ctx = ProjectContext(project_id="abc-123")
        assert ctx.project_id == "abc-123"
        assert ctx.brief_payload == {}
        assert ctx.channel_dna is None
        assert ctx.rag_context == ""


class TestIdempotencyConcept:
    """Verify idempotency logic (hash-based)."""

    def test_same_brief_same_hash(self):
        """2 lần tạo project với brief giống hệt → cùng brief_hash."""
        import hashlib
        import json

        def hash_brief(brief):
            return hashlib.sha256(
                json.dumps(brief, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()

        brief = {"topic": "Same topic", "audience": "general", "language": "vi"}
        assert hash_brief(brief) == hash_brief(dict(brief))

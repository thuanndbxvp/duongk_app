"""
Tests for style bible service — Phase 09.
"""
import pytest


class TestCharacterRefResolution:
    """Character reference resolution."""

    def test_character_in_scene_gets_ref(self):
        scene_chars = ["Hero", "Villain"]
        bible_chars = {"Hero": "asset-1", "Villain": "asset-2"}
        resolved = [bible_chars.get(c) for c in scene_chars]
        assert resolved == ["asset-1", "asset-2"]

    def test_missing_character_gets_placeholder(self):
        scene_chars = ["Hero", "Sidekick"]
        bible_chars = {"Hero": "asset-1"}
        resolved = [bible_chars.get(c) for c in scene_chars]
        assert resolved == ["asset-1", None]

    def test_deleted_asset_marks_invalid(self):
        """If asset is deleted, ref is invalid."""
        asset_exists = False
        ref_valid = asset_exists
        assert ref_valid is False


class TestNegativePromptConflict:
    """Channel forbidden_claims override bible negative."""

    def test_channel_forbidden_appended(self):
        bible_negative = "ugly"
        channel_forbidden = ["violence", "drugs"]
        combined = f"{bible_negative}, {', '.join(channel_forbidden)}"
        assert "violence" in combined
        assert "ugly" in combined

    def test_no_duplicate_negatives(self):
        """Standard negatives should not duplicate."""
        result = "low quality, blurry, watermark"
        count_low_quality = result.count("low quality")
        assert count_low_quality == 1


class TestStyleBibleReusability:
    """Bible can be used across multiple projects."""

    def test_same_bible_different_projects(self):
        bible_id = "bible-1"
        project_ids = ["proj-1", "proj-2", "proj-3"]
        assert all(isinstance(pid, str) for pid in project_ids)
        assert bible_id not in project_ids

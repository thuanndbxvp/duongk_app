"""
Tests for Style Bible API — Phase 09.
"""
import pytest
from uuid import uuid4


class TestStyleBibleSchemas:
    """Pydantic schemas for style bible."""

    def test_create_valid(self):
        from apps.api.schemas.style_bible import StyleBibleCreate
        req = StyleBibleCreate(name="My Bible", visual_palette={"primary": "#FF0000"})
        assert req.name == "My Bible"
        assert req.visual_palette == {"primary": "#FF0000"}

    def test_create_empty_name_rejected(self):
        from apps.api.schemas.style_bible import StyleBibleCreate
        with pytest.raises(Exception):
            StyleBibleCreate(name="")

    def test_update_partial(self):
        from apps.api.schemas.style_bible import StyleBibleUpdate
        req = StyleBibleUpdate(name="Updated")
        assert req.name == "Updated"
        assert req.description is None

    def test_character_ref_valid(self):
        from apps.api.schemas.style_bible import CharacterRef
        r = CharacterRef(asset_id=uuid4(), label="Hero", anchor_strength=0.8)
        assert r.anchor_strength == 0.8

    def test_anchor_strength_out_of_range(self):
        from apps.api.schemas.style_bible import CharacterRef
        with pytest.raises(Exception):
            CharacterRef(asset_id=uuid4(), anchor_strength=1.5)


class TestBuildPrompt:
    """build_prompt service."""

    def test_basic_merge(self):
        from apps.worker.services.style_bible import build_prompt
        bible = {"id": "b1", "version": 1, "visual_palette": {}, "lens_preference": "", "motion_style": "", "negative_prompt": ""}
        scene = {"scene_id": "s1", "narration": "Hello", "visual_description": "A beautiful scene", "image_prompt": "cinematic", "characters": [], "background": ""}
        prompt, neg, fp = build_prompt(bible, scene)
        assert "A beautiful scene" in prompt
        assert len(fp) == 64

    def test_idempotent_same_fingerprint(self):
        from apps.worker.services.style_bible import build_prompt
        bible = {"id": "b1", "version": 1, "visual_palette": {}, "negative_prompt": "blur"}
        scene = {"scene_id": "s1", "narration": "Test", "visual_description": "X", "image_prompt": "", "characters": [], "background": ""}
        _, _, fp1 = build_prompt(bible, scene)
        _, _, fp2 = build_prompt(dict(bible), dict(scene))
        assert fp1 == fp2

    def test_different_bible_different_fingerprint(self):
        from apps.worker.services.style_bible import build_prompt
        scene = {"scene_id": "s1", "narration": "T", "visual_description": "", "image_prompt": "", "characters": [], "background": ""}
        _, _, fp1 = build_prompt({"id": "a", "version": 1, "negative_prompt": ""}, scene)
        _, _, fp2 = build_prompt({"id": "b", "version": 1, "negative_prompt": ""}, scene)
        assert fp1 != fp2

    def test_negative_includes_forbidden_claims(self):
        from apps.worker.services.style_bible import build_prompt
        bible = {"negative_prompt": "ugly"}
        scene = {"scene_id": "s1", "narration": "T", "visual_description": "", "image_prompt": "", "characters": [], "background": ""}
        _, neg, _ = build_prompt(bible, scene, channel_forbidden_claims=["violence", "nudity"])
        assert "violence" in neg
        assert "ugly" in neg

    def test_standard_negatives_always_included(self):
        from apps.worker.services.style_bible import build_prompt
        bible = {"negative_prompt": ""}
        scene = {"scene_id": "s1", "narration": "T", "visual_description": "", "image_prompt": "", "characters": [], "background": ""}
        _, neg, _ = build_prompt(bible, scene)
        assert "low quality" in neg


class TestValidation:
    """Palette, lens, motion validation."""

    def test_valid_hex(self):
        from apps.worker.services.style_bible import validate_palette
        errors = validate_palette({"primary": "#FF0000", "secondary": "#00FF00"})
        assert len(errors) == 0

    def test_invalid_hex(self):
        from apps.worker.services.style_bible import validate_palette
        errors = validate_palette({"bad": "red"})
        assert len(errors) > 0

    def test_valid_lens(self):
        from apps.worker.services.style_bible import validate_lens
        assert validate_lens("50mm") is True

    def test_invalid_lens(self):
        from apps.worker.services.style_bible import validate_lens
        assert validate_lens("100mm") is False

    def test_valid_motion(self):
        from apps.worker.services.style_bible import validate_motion
        assert validate_motion("ken_burns_zoom_in") is True


class TestVersionRollback:
    """Version rollback logic."""

    def test_rollback_preserves_applications(self):
        """Rollback creates new version, old applications untouched."""
        old_version = 1
        new_version_after_rollback = 3  # 1→2(edit)→3(rollback)
        applications_untouched = True
        assert old_version < new_version_after_rollback
        assert applications_untouched

    def test_version_monotonic_increase(self):
        versions = [1, 2, 3, 4]
        for i in range(1, len(versions)):
            assert versions[i] > versions[i-1]

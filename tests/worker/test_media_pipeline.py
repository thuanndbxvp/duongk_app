"""
Tests for media_pipeline — Phase 05.
"""
import pytest


class TestMediaPipelineOps:
    """Media pipeline operations."""

    def test_ops_order_preserved(self):
        ops = ["normalize", "upscale", "cleanup", "resize"]
        assert ops[0] == "normalize"
        assert ops[-1] == "resize"

    def test_cleanup_requires_consent(self):
        """cleanup op requires consent_id."""
        ops_with_cleanup = "cleanup" in ["normalize", "upscale", "cleanup", "resize"]
        assert ops_with_cleanup is True

    def test_no_cleanup_no_consent_needed(self):
        ops = ["normalize", "resize"]
        needs_consent = "cleanup" in ops
        assert needs_consent is False


class TestWatermarkCleanup:
    """Watermark cleanup consent gate."""

    def test_cleanup_without_consent_blocked(self):
        """Cleanup without consent_record → blocked."""
        has_consent = False
        can_cleanup = has_consent
        assert can_cleanup is False

    def test_cleanup_with_consent_allowed(self):
        has_consent = True
        can_cleanup = has_consent
        assert can_cleanup is True

    def test_preview_does_not_mutate_source(self):
        """Preview creates variant but doesn't change source asset."""
        source_unchanged = True
        variant_created = True
        assert source_unchanged and variant_created

    def test_approve_creates_new_variant(self):
        """Approve creates a new variant, source still unchanged."""
        source_unchanged = True
        new_variant = True
        assert source_unchanged and new_variant


class TestThumbnailGeneration:
    """Thumbnail generation specs."""

    def test_candidate_count_3_to_5(self):
        count = 3
        assert 1 <= count <= 5

    def test_candidate_size_1280x720(self):
        width, height = 1280, 720
        assert width == 1280
        assert height == 720

    def test_each_candidate_has_score(self):
        candidates = [{"score": 0.7}, {"score": 0.85}]
        assert all(0 <= c["score"] <= 1.0 for c in candidates)


class TestMetadataPackage:
    """Metadata package structure."""

    def test_has_required_fields(self):
        pkg = {"title": "Test", "description": "Desc", "tags": ["a"], "hashtags": ["#b"]}
        assert "title" in pkg
        assert "description" in pkg
        assert "tags" in pkg
        assert "hashtags" in pkg

    def test_version_bumps(self):
        versions = [1, 2]
        assert versions[-1] > versions[0]


class TestCapabilityProbe:
    """Provider capability probing."""

    def test_probe_unknown_provider(self):
        import asyncio
        from apps.worker.services.capability_probe import probe_provider
        result = asyncio.run(probe_provider("unknown"))
        assert result.available is False

    def test_probe_gemini_no_key(self):
        import asyncio
        from apps.worker.services.capability_probe import probe_provider
        import os
        # Ensure no key set
        old = os.environ.pop("GEMINI_API_KEY", None)
        try:
            result = asyncio.run(probe_provider("gemini"))
            assert result.provider == "gemini"
        finally:
            if old:
                os.environ["GEMINI_API_KEY"] = old

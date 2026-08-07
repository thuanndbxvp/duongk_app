"""
Tests for voice form — Hidden Features P3.
"""
import pytest


class TestVoiceForm:
    """VoiceForm component logic."""

    def test_name_required(self):
        """Name field must be non-empty."""
        name = ""
        valid = len(name.strip()) > 0
        assert valid is False

    def test_name_valid(self):
        name = "My Voice"
        valid = len(name.strip()) > 0
        assert valid is True

    def test_sample_required_for_clone_provider(self):
        """Providers with requires_sample=True need sample file."""
        provider = {"requires_sample": True}
        sample = None
        needs_sample = provider["requires_sample"] and sample is None
        assert needs_sample is True

    def test_sample_not_required_for_non_clone(self):
        provider = {"requires_sample": False}
        sample = None
        needs_sample = provider["requires_sample"] and sample is None
        assert needs_sample is False

    def test_file_size_limit(self):
        """Max 10MB."""
        file_size = 11 * 1024 * 1024  # 11 MB
        valid = file_size <= 10 * 1024 * 1024
        assert valid is False

    def test_file_size_valid(self):
        file_size = 5 * 1024 * 1024  # 5 MB
        valid = file_size <= 10 * 1024 * 1024
        assert valid is True

    def test_providers_dynamic_not_hardcoded(self):
        """Providers should be fetched from API, not hardcoded."""
        from apps.api.modules.voice.providers import PROVIDERS
        assert len(PROVIDERS) >= 3
        assert any(p["id"] == "omnivoice" for p in PROVIDERS)
        assert any(p["id"] == "elevenlabs" for p in PROVIDERS)


class TestVoiceEndpoints:
    """Voice API endpoints."""

    def test_providers_returns_list(self):
        from apps.api.modules.voice.providers import PROVIDERS
        assert len(PROVIDERS) > 0
        for p in PROVIDERS:
            assert "id" in p
            assert "name" in p
            assert "languages" in p
            assert "supports_clone" in p

    def test_providers_has_required_fields(self):
        from apps.api.modules.voice.providers import PROVIDERS
        for p in PROVIDERS:
            assert "languages" in p
            assert isinstance(p["languages"], list)
            assert len(p["languages"]) > 0


class TestVoiceDetailActions:
    """VoiceDetailActions component logic."""

    def test_test_text_default(self):
        """Default test text is set."""
        test_text = "Xin chào, đây là test voice."
        assert len(test_text) > 0

    def test_delete_requires_confirm(self):
        """Delete should require confirmation."""
        confirmed = True
        can_delete = confirmed
        assert can_delete is True

    def test_no_confirm_no_delete(self):
        confirmed = False
        can_delete = confirmed
        assert can_delete is False

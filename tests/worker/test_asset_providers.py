"""
Tests for asset providers — Phase 02.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestAssetMetadata:
    """AssetMetadata dataclass."""

    def test_defaults(self):
        from apps.worker.services.asset_providers.base import AssetMetadata
        m = AssetMetadata(source="pexels", provider_id="123", storage_key="k", mime_type="image/jpeg", size_bytes=100, checksum="abc")
        assert m.source == "pexels"
        assert m.provider_id == "123"
        assert m.checksum == "abc"
        assert m.license == {}
        assert m.metadata == {}


class TestSearchResult:
    """SearchResult dataclass."""

    def test_defaults(self):
        from apps.worker.services.asset_providers.base import SearchResult
        r = SearchResult(provider="pexels", provider_id="456", thumbnail_url="http://img")
        assert r.provider == "pexels"
        assert r.description == ""
        assert r.photographer is None


class TestUploadProvider:
    """UploadProvider — user uploads."""

    def test_search_returns_empty(self):
        from apps.worker.services.asset_providers.upload import UploadProvider
        import asyncio
        p = UploadProvider()
        results, total, next_page = asyncio.run(p.search())
        assert results == []
        assert total == 0

    def test_materialize_raises(self):
        from apps.worker.services.asset_providers.upload import UploadProvider
        import asyncio
        p = UploadProvider()
        with pytest.raises(NotImplementedError):
            asyncio.run(p.materialize("123"))


class TestLocalPlaceholderProvider:
    """LocalPlaceholderProvider — test/dev."""

    def test_search_returns_5_results(self):
        from apps.worker.services.asset_providers.local_placeholder import LocalPlaceholderProvider
        import asyncio
        p = LocalPlaceholderProvider()
        results, total, next_page = asyncio.run(p.search("test"))
        assert len(results) == 5
        assert total == 5
        assert all(r.provider == "local_placeholder" for r in results)

    def test_materialize_returns_metadata(self):
        from apps.worker.services.asset_providers.local_placeholder import LocalPlaceholderProvider
        import asyncio
        p = LocalPlaceholderProvider()
        meta = asyncio.run(p.materialize("test-1"))
        assert meta.source == "local_placeholder"
        assert meta.mime_type == "image/svg+xml"
        assert meta.width == 640
        assert meta.height == 360
        assert len(meta.checksum) == 64


class TestPexelsProviderInit:
    """PexelsProvider initialization."""

    def test_default_api_key(self):
        from apps.worker.services.asset_providers.pexels import PexelsProvider
        p = PexelsProvider()
        assert p.name == "pexels"
        assert p.BASE == "https://api.pexels.com"

    def test_custom_api_key(self):
        from apps.worker.services.asset_providers.pexels import PexelsProvider
        p = PexelsProvider(api_key="custom-key")
        assert p.api_key == "custom-key"


class TestProviderRegistry:
    """PROVIDER_REGISTRY completeness."""

    def test_all_required_providers_registered(self):
        from apps.worker.services.asset_providers import PROVIDER_REGISTRY
        assert "upload" in PROVIDER_REGISTRY
        assert "pexels" in PROVIDER_REGISTRY
        assert "local_placeholder" in PROVIDER_REGISTRY


class TestIdempotencyConcept:
    """Materialize task idempotency: same provider + provider_id = skip."""

    def test_same_source_provider_id_should_skip(self):
        """If asset exists with same (source, provider_id) and status=ready, skip."""
        # This is a logic test, not integration
        existing = {"source": "pexels", "provider_id": "123", "status": "ready"}
        new_request = ("pexels", "123")
        should_skip = (existing["source"], existing["provider_id"]) == new_request and existing["status"] == "ready"
        assert should_skip is True

    def test_different_provider_should_not_skip(self):
        existing = {"source": "pexels", "provider_id": "123", "status": "ready"}
        new_request = ("pexels", "456")
        should_skip = (existing["source"], existing["provider_id"]) == new_request and existing["status"] == "ready"
        assert should_skip is False

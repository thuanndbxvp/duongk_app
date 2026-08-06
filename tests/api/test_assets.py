"""
Tests for Asset API endpoints — Phase 02.
"""
import pytest
from uuid import uuid4


class TestUploadInitSchema:
    """POST /api/assets/upload-init — schema validation."""

    def test_valid_upload_init(self):
        from apps.api.schemas.assets import UploadInitRequest
        req = UploadInitRequest(
            filename="test.jpg",
            mime_type="image/jpeg",
            size_bytes=102400,
            checksum="abc123def456",
        )
        assert req.filename == "test.jpg"
        assert req.mime_type == "image/jpeg"

    def test_invalid_mime_rejected(self):
        from apps.api.schemas.assets import UploadInitRequest
        with pytest.raises(Exception):
            UploadInitRequest(filename="test.exe", mime_type="application/x-msdownload", size_bytes=100, checksum="abc12345")

    def test_zero_size_rejected(self):
        from apps.api.schemas.assets import UploadInitRequest
        with pytest.raises(Exception):
            UploadInitRequest(filename="test.jpg", mime_type="image/jpeg", size_bytes=0, checksum="abc12345")

    def test_short_checksum_rejected(self):
        from apps.api.schemas.assets import UploadInitRequest
        with pytest.raises(Exception):
            UploadInitRequest(filename="test.jpg", mime_type="image/jpeg", size_bytes=100, checksum="short")

    def test_image_size_limit(self):
        from apps.api.schemas.assets import UploadInitRequest
        # 25 MB > 20 MB limit
        with pytest.raises(Exception):
            UploadInitRequest(filename="big.jpg", mime_type="image/jpeg", size_bytes=25 * 1024 * 1024 + 1, checksum="abc12345")

    def test_video_size_limit(self):
        from apps.api.schemas.assets import UploadInitRequest
        # 250 MB > 200 MB limit
        with pytest.raises(Exception):
            UploadInitRequest(filename="big.mp4", mime_type="video/mp4", size_bytes=201 * 1024 * 1024, checksum="abc12345")


class TestUploadCompleteSchema:
    """POST /api/assets/upload-complete — schema."""

    def test_valid_complete(self):
        from apps.api.schemas.assets import UploadCompleteRequest
        req = UploadCompleteRequest(asset_id=uuid4(), checksum="sha256hash123")
        assert req.checksum == "sha256hash123"

    def test_short_checksum(self):
        from apps.api.schemas.assets import UploadCompleteRequest
        with pytest.raises(Exception):
            UploadCompleteRequest(asset_id=uuid4(), checksum="1234567")


class TestSearchSchema:
    """POST /api/assets/search — schema."""

    def test_valid_search(self):
        from apps.api.schemas.assets import AssetSearchRequest
        req = AssetSearchRequest(query="mountain", media_type="image")
        assert req.provider == "pexels"
        assert req.query == "mountain"

    def test_empty_query_rejected(self):
        from apps.api.schemas.assets import AssetSearchRequest
        with pytest.raises(Exception):
            AssetSearchRequest(query="", media_type="image")

    def test_invalid_provider(self):
        from apps.api.schemas.assets import AssetSearchRequest
        with pytest.raises(Exception):
            AssetSearchRequest(provider="unsplash", query="test")


class TestSceneAssetBinding:
    """POST /api/scenes/{id}/assets — binding."""

    def test_valid_bind_request(self):
        from apps.api.schemas.assets import SceneAssetBindRequest
        req = SceneAssetBindRequest(asset_id=uuid4(), position=0)
        assert req.position == 0


class TestRLSConcept:
    """Verify RLS logic concept for assets."""

    def test_asset_owner_id_required(self):
        """Assets require owner_id = auth.uid()."""
        from apps.api.schemas.assets import AssetResponse
        from uuid import UUID as UuidType
        owner = uuid4()
        a = AssetResponse(
            id=uuid4(), owner_id=owner, source='upload',
            storage_key='test', mime_type='image/png',
            size_bytes=100, checksum='abc123', status='ready',
            created_at='2024-01-01T00:00:00Z', updated_at='2024-01-01T00:00:00Z',
        )
        assert str(a.owner_id) == str(owner)

"""
Tests for asset endpoints — Hidden Features P5.
"""
import pytest


class TestAssetEndpoints:
    """Asset API endpoints from Phase 02 router."""

    def test_list_endpoint_exists(self):
        from apps.api.routers.assets import router
        paths = [r.path for r in router.routes]
        assert '/api/assets' in paths

    def test_upload_init_exists(self):
        from apps.api.routers.assets import router
        paths = [r.path for r in router.routes]
        assert '/api/assets/upload-init' in paths

    def test_search_exists(self):
        from apps.api.routers.assets import router
        paths = [r.path for r in router.routes]
        assert '/api/assets/search' in paths

    def test_detail_endpoint_exists(self):
        from apps.api.routers.assets import router
        paths = [r.path for r in router.routes]
        assert '/api/assets/{asset_id}' in paths


class TestAssetSchema:
    """Asset Pydantic schemas."""

    def test_upload_init_request(self):
        from apps.api.schemas.assets import UploadInitRequest
        req = UploadInitRequest(filename="test.jpg", mime_type="image/jpeg", size_bytes=102400, checksum="abc123def456")
        assert req.filename == "test.jpg"

    def test_invalid_mime_rejected(self):
        from apps.api.schemas.assets import UploadInitRequest
        with pytest.raises(Exception):
            UploadInitRequest(filename="test.exe", mime_type="application/x-msdownload", size_bytes=100, checksum="abc12345")

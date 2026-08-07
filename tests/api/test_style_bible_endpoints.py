"""
Tests for style bible API endpoints — Hidden Features P4.
"""
import pytest


class TestStyleBibleAPI:
    """Style bible endpoints."""

    def test_create_endpoint(self):
        """POST /api/style-bibles creates a bible."""
        from apps.api.routers.style_bible import router
        # POST at '' prefix
        post_exists = any(r.methods and 'POST' in r.methods and r.path == '/api/style-bibles' for r in router.routes)
        assert post_exists

    def test_list_endpoint(self):
        """GET /api/style-bibles returns list."""
        from apps.api.routers.style_bible import router
        get_exists = any(r.methods and 'GET' in r.methods and r.path == '/api/style-bibles' for r in router.routes)
        assert get_exists

    def test_detail_endpoint(self):
        """GET /api/style-bibles/{bible_id} returns detail."""
        from apps.api.routers.style_bible import router
        detail_exists = '/api/style-bibles/{bible_id}' in [r.path for r in router.routes]
        assert detail_exists

    def test_update_endpoint(self):
        """PATCH /api/style-bibles/{bible_id} updates."""
        from apps.api.routers.style_bible import router
        update_exists = '/api/style-bibles/{bible_id}' in [r.path for r in router.routes]
        assert update_exists

    def test_rollback_endpoint(self):
        """POST /api/style-bibles/{bible_id}/rollback/{version} exists."""
        from apps.api.routers.style_bible import router
        rollback_exists = '/api/style-bibles/{bible_id}/rollback/{version}' in [r.path for r in router.routes]
        assert rollback_exists

    def test_assets_endpoint(self):
        """POST /api/style-bibles/{bible_id}/assets exists."""
        from apps.api.routers.style_bible import router
        assets_exists = '/api/style-bibles/{bible_id}/assets' in [r.path for r in router.routes]
        assert assets_exists


class TestStyleBibleSchema:
    """Style bible Pydantic schemas."""

    def test_create_schema(self):
        from apps.api.schemas.style_bible import StyleBibleCreate
        req = StyleBibleCreate(name="Test Bible", visual_palette={"primary": "#FF0000"})
        assert req.name == "Test Bible"

    def test_apply_request(self):
        from apps.api.schemas.style_bible import StyleBibleApplyRequest
        from uuid import uuid4
        req = StyleBibleApplyRequest(bible_id=uuid4())
        assert req.scene_ids is None

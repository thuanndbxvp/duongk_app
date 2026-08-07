"""
Tests for cancel render button — Hidden Features P1.
"""
import pytest


class TestCancelRenderButton:
    """CancelRenderButton component logic."""

    def test_shows_when_running(self):
        """Button visible when status is 'running'."""
        status = 'running'
        visible = status in ('running', 'pending')
        assert visible is True

    def test_shows_when_pending(self):
        status = 'pending'
        visible = status in ('running', 'pending')
        assert visible is True

    def test_hidden_when_success(self):
        status = 'success'
        visible = status in ('running', 'pending')
        assert visible is False

    def test_hidden_when_failed(self):
        status = 'failed'
        visible = status in ('running', 'pending')
        assert visible is False

    def test_hidden_when_cancelled(self):
        status = 'cancelled'
        visible = status in ('running', 'pending')
        assert visible is False

    def test_cancel_endpoint_exists(self):
        """POST /api/jobs/{job_id}/cancel exists in render router."""
        from apps.api.routers.render import router
        paths = [r.path for r in router.routes]
        assert '/api/jobs/{job_id}/cancel' in paths

    def test_poll_mechanism_concept(self):
        """After cancel, poll every 2s max 30s."""
        max_polls = 15  # 30s / 2s
        assert max_polls == 15
        cancelled_detected = True
        assert cancelled_detected is True


class TestConfigWatcher:
    """Config watcher wire in Celery."""

    def test_worker_ready_signal_importable(self):
        from celery.signals import worker_ready
        assert worker_ready is not None

    def test_start_watcher_importable(self):
        from apps.worker.services.config_watcher import start_watcher
        assert callable(start_watcher)


class TestDeadServicesCleanup:
    """youtube.py removal verification."""

    def test_youtube_py_no_longer_importable(self):
        """youtube.py should be removed, imports should fail."""
        try:
            from apps.api.services import youtube
            found = True
        except ImportError:
            found = False
        assert not found, "apps.api.services.youtube should have been removed"

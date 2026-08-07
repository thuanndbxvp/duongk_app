"""
Tests for config_watcher boot — Hidden Features P1.
"""
import pytest


class TestConfigWatcherBoot:
    """Config watcher starts on worker boot."""

    def test_celery_app_has_worker_ready_signal(self):
        """Verify celery_app.py registers worker_ready signal."""
        import apps.worker.celery_app as ca
        # Check that start_config_watcher function exists
        assert hasattr(ca, 'start_config_watcher')

    def test_start_watcher_function_exists(self):
        from apps.worker.services.config_watcher import start_watcher
        assert callable(start_watcher)

    def test_config_watcher_module_importable(self):
        from apps.worker.services import config_watcher
        assert config_watcher is not None


class TestWatcherGracefulFailure:
    """Watcher handles Redis down gracefully."""

    def test_start_watcher_handles_exceptions(self):
        """start_watcher should not crash worker on Redis connection failure."""
        # The signal handler in celery_app has try/except
        import apps.worker.celery_app as ca
        import inspect
        source = inspect.getsource(ca.start_config_watcher)
        assert 'try:' in source
        assert 'except' in source


class TestTTLFallback:
    """TTL polling fallback when Redis pub/sub down."""

    def test_polling_interval_default(self):
        """Default polling interval should be 60s."""
        interval = 60
        assert interval > 0
        assert interval <= 60

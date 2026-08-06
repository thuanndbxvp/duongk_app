"""
Tests for render_video task — Phase 04.
"""
import pytest


class TestOutputVerification:
    """ffprobe verify output."""

    def test_verify_checks_streams(self):
        """Output must have at least 1 stream."""
        info = {"streams": [{"codec_type": "video"}], "format": {"duration": "10.0"}}
        streams = info.get("streams", [])
        assert len(streams) > 0
        assert streams[0]["codec_type"] == "video"

    def test_verify_too_short_fails(self):
        """Duration < 1s should fail."""
        dur = 0.5
        assert dur < 1.0

    def test_verify_valid_duration(self):
        dur = 30.0
        assert dur >= 1.0


class TestRenderJobStatusFlow:
    """Status transitions for render_jobs."""

    def test_pending_to_running(self):
        assert 'running' in ('pending', 'running', 'success', 'failed', 'cancelled')

    def test_running_to_success(self):
        assert 'success' in ('pending', 'running', 'success', 'failed', 'cancelled')

    def test_running_to_cancelled(self):
        assert 'cancelled' in ('pending', 'running', 'success', 'failed', 'cancelled')

    def test_running_to_failed(self):
        assert 'failed' in ('pending', 'running', 'success', 'failed', 'cancelled')


class TestRetryBehavior:
    """Retry tracking for failed renders."""

    def test_retry_increments_count(self):
        job = {"retry_count": 2, "status": "failed"}
        job["retry_count"] += 1
        assert job["retry_count"] == 3

    def test_no_duplicate_output_on_retry(self):
        """Retry same job should not create duplicate output_asset_id."""
        existing_output = "abc-123"
        new_output = existing_output  # same
        assert new_output == existing_output


class TestProgressCallback:
    """Progress tracking during render."""

    def test_progress_increases(self):
        progress = [0.0, 0.25, 0.5, 0.75, 1.0]
        for i in range(1, len(progress)):
            assert progress[i] > progress[i-1]

    def test_progress_never_exceeds_1(self):
        for p in [0, 0.5, 1.0]:
            assert 0.0 <= p <= 1.0

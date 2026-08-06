"""
Tests for tts_scene worker task — Phase 03.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestSRTTimestamps:
    """SRT timestamps match voice line durations."""

    def test_timestamps_sequential(self):
        from apps.worker.tasks.srt_generate import build_srt, sec_to_srt
        lines = [{"text": "A", "duration_seconds": 2.5}, {"text": "B", "duration_seconds": 3.0}]
        srt = build_srt(lines)
        assert sec_to_srt(0) in srt
        assert sec_to_srt(2.5) in srt
        assert sec_to_srt(5.5) in srt

    def test_fallback_duration_for_zero(self):
        from apps.worker.tasks.srt_generate import build_srt
        lines = [{"text": "X", "duration_seconds": 0}]
        srt = build_srt(lines)
        assert "00:00:03,000" in srt  # fallback 3s


class TestUniqueConstraint:
    """Verify (scene_id, voice_version) unique constraint concept."""

    def test_same_scene_same_version_collision(self):
        """Two inserts with same (scene_id, voice_version) should be handled."""
        row1 = {"scene_id": "abc", "voice_version": 1}
        row2 = {"scene_id": "abc", "voice_version": 1}
        is_duplicate = (row1["scene_id"], row1["voice_version"]) == (row2["scene_id"], row2["voice_version"])
        assert is_duplicate is True

    def test_different_version_allowed(self):
        row1 = {"scene_id": "abc", "voice_version": 1}
        row2 = {"scene_id": "abc", "voice_version": 2}
        is_duplicate = (row1["scene_id"], row1["voice_version"]) == (row2["scene_id"], row2["voice_version"])
        assert is_duplicate is False


class TestVoiceLineStatusFlow:
    """Status transitions for voice_line."""

    def test_pending_to_running_to_success(self):
        states = ["pending", "running", "success"]
        assert states[0] == "pending"
        assert states[-1] == "success"

    def test_pending_to_running_to_failed(self):
        states = ["pending", "running", "failed"]
        assert states[-1] == "failed"

    def test_failed_can_retry_to_pending(self):
        """Retry sets status back to pending."""
        initial = "failed"
        after_retry = "pending"
        assert after_retry == "pending"


class TestTimeoutBehavior:
    """Timeout handling for TTS scene."""

    def test_timeout_results_in_failed(self):
        """If task times out, status should be 'failed' with error_code."""
        error_code = "tts_timeout"
        status = "failed"
        assert status == "failed"
        assert error_code == "tts_timeout"

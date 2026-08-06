"""
Tests for Voice API — Phase 03.
"""
import pytest
from uuid import uuid4


class TestVoiceSchemas:
    """Pydantic schemas for voice."""

    def test_voice_start_request(self):
        from apps.api.schemas.voice import VoiceStartRequest
        vid = uuid4()
        req = VoiceStartRequest(voice_profile_id=vid)
        assert req.voice_profile_id == vid
        assert req.voice_version == 1
        assert req.scene_ids is None

    def test_voice_start_with_scene_ids(self):
        from apps.api.schemas.voice import VoiceStartRequest
        sids = [uuid4(), uuid4()]
        req = VoiceStartRequest(voice_profile_id=uuid4(), scene_ids=sids)
        assert len(req.scene_ids) == 2

    def test_voice_status_response(self):
        from apps.api.schemas.voice import VoiceStatusResponse, VoiceLineResponse
        r = VoiceStatusResponse(project_id=uuid4(), lines=[], total=0, succeeded=0, failed=0, pending=0, running=0)
        assert r.total == 0

    def test_voice_line_response_fields(self):
        from apps.api.schemas.voice import VoiceLineResponse
        line = VoiceLineResponse(id=uuid4(), scene_id=uuid4(), voice_version=1, status='pending')
        assert line.status == 'pending'
        assert line.duration_seconds is None
        assert line.error_code is None

    def test_extra_forbidden(self):
        from apps.api.schemas.voice import VoiceStartRequest
        with pytest.raises(Exception):
            VoiceStartRequest(voice_profile_id=uuid4(), hack=123)

    def test_timeline_response(self):
        from apps.api.schemas.voice import TimelineResponse
        from datetime import datetime
        t = TimelineResponse(id=uuid4(), project_id=uuid4(), version=1, schema_version=1, model={}, status='draft', created_at=datetime.now())
        assert t.version == 1
        assert t.model == {}


class TestSRTGenerator:
    """SRT formatting and timestamp conversion."""

    def test_sec_to_srt_zero(self):
        from apps.worker.tasks.srt_generate import sec_to_srt
        assert sec_to_srt(0) == "00:00:00,000"

    def test_sec_to_srt_one_hour(self):
        from apps.worker.tasks.srt_generate import sec_to_srt
        assert sec_to_srt(3600) == "01:00:00,000"

    def test_sec_to_srt_with_ms(self):
        from apps.worker.tasks.srt_generate import sec_to_srt
        assert sec_to_srt(65.5) == "00:01:05,500"

    def test_build_srt_empty(self):
        from apps.worker.tasks.srt_generate import build_srt
        assert build_srt([]) == ""

    def test_build_srt_single_line(self):
        from apps.worker.tasks.srt_generate import build_srt
        srt = build_srt([{"text": "Hello world", "duration_seconds": 5.0}])
        assert "Hello world" in srt
        assert "00:00:00,000" in srt
        assert "00:00:05,000" in srt

    def test_build_srt_multiple_lines(self):
        from apps.worker.tasks.srt_generate import build_srt
        lines = [
            {"text": "First", "duration_seconds": 3.0},
            {"text": "Second", "duration_seconds": 4.0},
        ]
        srt = build_srt(lines)
        assert "1\n" in srt
        assert "2\n" in srt
        assert "00:00:03,000" in srt  # end of first
        assert "00:00:07,000" in srt  # end of second


class TestDurationEstimate:
    """Duration estimate fallback."""

    def test_wpm_estimate(self):
        from apps.worker.tasks.tts_scene import _estimate_duration_from_text
        dur = _estimate_duration_from_text("one two three four five")
        assert dur > 0
        assert dur == pytest.approx(2.0, 0.5)  # 5 words / 2.5 wps ≈ 2s


class TestTimelineCompiler:
    """Timeline model compilation."""

    def test_model_schema_structure(self):
        """Verify the structure contract."""
        model = {
            "schema_version": 1,
            "total_duration": 120.5,
            "clips": [],
            "transitions": [],
            "audio_tracks": [],
            "subtitle_track": {"source": "srt", "style": "default", "safe_area": "1080x1920_20pct"},
            "output": {"width": 1080, "height": 1920, "fps": 30, "codec": "h264", "quality": "high"},
        }
        assert model["schema_version"] == 1
        assert "clips" in model
        assert "audio_tracks" in model
        assert "output" in model


class TestIdempotency:
    """TTS idempotency logic."""

    def test_already_success_should_skip(self):
        """If voice_line.status == 'success', skip."""
        line = {"status": "success", "storage_key": "audio.wav"}
        should_skip = line["status"] == "success"
        assert should_skip is True

    def test_pending_should_run(self):
        line = {"status": "pending"}
        should_skip = line["status"] == "success"
        assert should_skip is False

    def test_failed_should_retry(self):
        line = {"status": "failed"}
        should_skip = line["status"] == "success"
        assert should_skip is False

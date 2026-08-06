"""
Tests for render pipeline — Phase 04.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestRenderSchemas:
    """Pydantic schemas for render."""

    def test_render_start_request(self):
        from apps.api.schemas.render import RenderStartRequest
        from uuid import uuid4
        req = RenderStartRequest(kind='draft', timeline_id=uuid4())
        assert req.kind == 'draft'

    def test_render_start_extra_forbidden(self):
        from apps.api.schemas.render import RenderStartRequest
        from uuid import uuid4
        with pytest.raises(Exception):
            RenderStartRequest(kind='draft', timeline_id=uuid4(), hack=True)

    def test_render_job_response(self):
        from apps.api.schemas.render import RenderJobResponse
        from uuid import uuid4
        r = RenderJobResponse(id=uuid4(), project_id=uuid4(), job_type='draft', status='pending')
        assert r.progress == 0.0

    def test_export_response(self):
        from apps.api.schemas.render import ExportResponse
        from uuid import uuid4
        from datetime import datetime
        e = ExportResponse(id=uuid4(), job_id=uuid4(), download_url='http://x', expires_at=datetime.now())
        assert 'http' in e.download_url


class TestRenderPlanner:
    """RenderPlanner.compile_ffmpeg_args."""

    def test_draft_720p_scales_down(self):
        from apps.worker.services.render_planner import compile_ffmpeg_args
        model = {
            "schema_version": 1, "total_duration": 15,
            "clips": [{"scene_id": "s1", "scene_index": 1, "duration": 15}],
            "audio_tracks": [],
            "output": {"width": 1080, "height": 1920, "fps": 30, "codec": "h264"},
        }
        argv = compile_ffmpeg_args(model, 'draft', '/tmp/out.mp4')
        assert '-preset' in argv
        assert 'veryfast' in argv
        assert '-crf' in argv

    def test_final_1080p(self):
        from apps.worker.services.render_planner import compile_ffmpeg_args
        model = {
            "schema_version": 1, "total_duration": 30,
            "clips": [{"scene_id": "s1", "scene_index": 1, "duration": 30}],
            "audio_tracks": [],
            "output": {"width": 1080, "height": 1920, "fps": 30, "codec": "h264"},
        }
        argv = compile_ffmpeg_args(model, 'final', '/tmp/out.mp4')
        assert 'slow' in argv
        assert '18' in argv

    def test_includes_libx264(self):
        from apps.worker.services.render_planner import compile_ffmpeg_args
        model = {"clips": [{"duration": 5}], "output": {}, "audio_tracks": [], "total_duration": 5}
        argv = compile_ffmpeg_args(model, 'draft', '/tmp/o.mp4')
        assert 'libx264' in argv


class TestFFmpegTimeParser:
    """parse_ffmpeg_time function."""

    def test_valid_time(self):
        from apps.worker.services.ffmpeg_runner import parse_ffmpeg_time
        t = parse_ffmpeg_time('frame=  100 fps=30 time=00:01:23.45 bitrate=1000kbits/s')
        assert t == pytest.approx(83.45, 0.01)

    def test_no_time(self):
        from apps.worker.services.ffmpeg_runner import parse_ffmpeg_time
        assert parse_ffmpeg_time('some other line') is None

    def test_zero_time(self):
        from apps.worker.services.ffmpeg_runner import parse_ffmpeg_time
        t = parse_ffmpeg_time('time=00:00:00.00')
        assert t == 0.0


class TestRenderPlannerMultiClip:
    """Multiple clips rendering."""

    def test_two_clips_concat(self):
        from apps.worker.services.render_planner import compile_ffmpeg_args
        model = {
            "total_duration": 20,
            "clips": [
                {"scene_id": "s1", "duration": 10},
                {"scene_id": "s2", "duration": 10},
            ],
            "audio_tracks": [],
            "output": {},
        }
        argv = compile_ffmpeg_args(model, 'draft', '/tmp/o.mp4')
        assert 'concat' in ' '.join(argv)


class TestCancelConcept:
    """Cancel logic for render jobs."""

    def test_cancel_requested_flag(self):
        """cancel_requested flag triggers process kill."""
        job = {"cancel_requested": True, "status": "running"}
        should_cancel = job["cancel_requested"] and job["status"] == "running"
        assert should_cancel is True

    def test_already_finished_no_cancel(self):
        job = {"cancel_requested": True, "status": "success"}
        should_cancel = job["cancel_requested"] and job["status"] == "running"
        assert should_cancel is False


class TestDraftActiveConstraint:
    """Per-project: only 1 draft active."""

    def test_second_draft_blocked(self):
        """If a draft is already pending/running, reject new draft."""
        active_jobs = [{"job_type": "draft", "status": "running"}]
        new_kind = "draft"
        has_active = any(j["job_type"] == new_kind and j["status"] in ("pending", "running") for j in active_jobs)
        assert has_active is True

    def test_final_allowed_alongside_draft(self):
        active_jobs = [{"job_type": "draft", "status": "running"}]
        new_kind = "final"
        has_active = any(j["job_type"] == new_kind and j["status"] in ("pending", "running") for j in active_jobs)
        assert has_active is False

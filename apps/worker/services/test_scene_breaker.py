"""
Unit tests for SceneBreaker.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from apps.worker.services.scene_breaker import SceneBreaker


class TestSceneBreaker:
    """Test suite for SceneBreaker."""

    @pytest.fixture
    def breaker(self):
        return SceneBreaker(default_wpm=150)

    def test_segment_scenes_basic(self, breaker):
        """Test basic scene segmentation."""
        script = """Hook content here.

This is the body paragraph one.

This is body paragraph two.

CTA at the end."""

        scenes = breaker.segment_scenes(script, pacing_wpm=150)

        assert len(scenes) == 4
        assert scenes[0]['scene_number'] == 1
        assert scenes[0]['start_time'] == 0.0
        assert scenes[0]['text'] == "Hook content here."
        assert 'broll_keywords' in scenes[0]

    def test_segment_scenes_timestamps(self, breaker):
        """Test timestamp calculation."""
        script = "Word " * 300  # 300 words

        scenes = breaker.segment_scenes(script, pacing_wpm=150)
        # 300 words / 150 wpm = 2 minutes = 120 seconds

        assert len(scenes) == 1
        assert scenes[0]['duration_seconds'] == pytest.approx(120.0, rel=1)

    def test_extract_broll_keywords(self, breaker):
        """Test B-roll keyword extraction."""
        text = "Hôm nay tôi đang nấu ăn tại bếp với nguyên liệu tươi."

        keywords = breaker._extract_broll_keywords(text)

        assert 'nấu ăn' in keywords
        assert 'tại bếp' in keywords

    def test_extract_broll_keywords_empty(self, breaker):
        """Test extraction with no keywords."""
        text = "Đây là một câu không có từ khóa nào."

        keywords = breaker._extract_broll_keywords(text)

        assert len(keywords) == 0

    def test_calculate_total_duration(self, breaker):
        """Test duration calculation."""
        scenes = [
            {'duration_seconds': 60.0},
            {'duration_seconds': 90.0},
            {'duration_seconds': 45.0},
        ]

        stats = breaker.calculate_total_duration(scenes)

        assert stats['total_duration_seconds'] == 195.0
        assert stats['scene_count'] == 3

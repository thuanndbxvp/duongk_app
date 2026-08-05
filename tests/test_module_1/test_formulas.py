"""
Unit tests for Module 1 Formulas.
"""
import pytest
from apps.api.modules.module_1.formulas import (
    filter_quality_videos,
    detect_viral_videos
)


class TestFilterQualityVideos:
    """Tests for Formula A0 - Video Filter."""
    
    def test_keeps_quality_videos(self):
        """Test that quality videos are kept."""
        videos = [
            {
                'snippet': {'published_at': '2026-01-01T00:00:00Z', 'live_broadcast_content': 'none'},
                'content_details': {'duration': 'PT10M'},
                'statistics': {'view_count': '50000'}
            }
        ]
        result = filter_quality_videos(videos)
        assert len(result) == 1
    
    def test_filters_shorts(self):
        """Test that Shorts (<60s) are filtered."""
        videos = [
            {
                'snippet': {'published_at': '2026-01-01T00:00:00Z', 'live_broadcast_content': 'none'},
                'content_details': {'duration': 'PT30S'},
                'statistics': {'view_count': '50000'}
            }
        ]
        result = filter_quality_videos(videos)
        assert len(result) == 0
    
    def test_filters_live_streams(self):
        """Test that Live streams are filtered."""
        videos = [
            {
                'snippet': {'published_at': '2026-01-01T00:00:00Z', 'live_broadcast_content': 'live'},
                'content_details': {'duration': 'PT0S'},
                'statistics': {'view_count': '50000'}
            }
        ]
        result = filter_quality_videos(videos)
        assert len(result) == 0
    
    def test_filters_low_views(self):
        """Test that videos with <1000 views are filtered."""
        videos = [
            {
                'snippet': {'published_at': '2026-01-01T00:00:00Z', 'live_broadcast_content': 'none'},
                'content_details': {'duration': 'PT10M'},
                'statistics': {'view_count': '500'}
            }
        ]
        result = filter_quality_videos(videos)
        assert len(result) == 0


class TestDetectViralVideos:
    """Tests for Formula A2 - Viral Detection."""
    
    def test_detects_single_viral_video(self):
        """Test detection of single viral video."""
        videos = [
            {'statistics': {'view_count': '10000'}},
            {'statistics': {'view_count': '12000'}},
            {'statistics': {'view_count': '11000'}},
            {'statistics': {'view_count': '500000'}},  # Viral
            {'statistics': {'view_count': '11500'}},
        ]
        result = detect_viral_videos(videos)
        assert len(result) == 1
        assert result[0]['statistics']['view_count'] == '500000'
    
    def test_no_viral_for_similar_views(self):
        """Test that videos with similar views are not viral."""
        videos = [
            {'statistics': {'view_count': '10000'}},
            {'statistics': {'view_count': '10000'}},
            {'statistics': {'view_count': '10000'}},
            {'statistics': {'view_count': '10000'}},
            {'statistics': {'view_count': '10000'}},
        ]
        result = detect_viral_videos(videos)
        assert len(result) == 0
    
    def test_returns_all_for_small_sample(self):
        """Test that small samples (<5) are not analyzed."""
        videos = [
            {'statistics': {'view_count': '10000'}},
            {'statistics': {'view_count': '500000'}},
        ]
        result = detect_viral_videos(videos)
        assert len(result) == 2

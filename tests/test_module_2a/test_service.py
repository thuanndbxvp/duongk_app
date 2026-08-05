"""
Unit tests for Module 2A YouTubeCollector.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from apps.api.modules.module_2a.service import YouTubeCollector


class TestYouTubeCollector:
    """Tests for YouTubeCollector service."""
    
    @pytest.fixture
    def collector(self):
        return YouTubeCollector(api_key="test_key")
    
    def test_initialization(self, collector):
        """Test collector initialization."""
        assert collector.api_key == "test_key"
        assert collector.BATCH_SIZE == 50
        assert collector.MAX_VIDEOS == 200
    
    @pytest.mark.asyncio
    async def test_collect_channel_videos(self, collector):
        """Test video collection from channel."""
        # Mock YouTube API responses
        with patch.object(collector, '_get_channel_video_ids', new_callable=AsyncMock) as mock_ids, \
             patch.object(collector, '_fetch_video_metadata', new_callable=AsyncMock) as mock_meta:
            
            mock_ids.return_value = ['video1', 'video2']
            mock_meta.return_value = [
                {
                    'id': 'video1',
                    'snippet': {'title': 'Test', 'publishedAt': '2026-01-01T00:00:00Z'},
                    'contentDetails': {'duration': 'PT10M'},
                    'statistics': {'viewCount': '50000'}
                }
            ]
            
            result = await collector.collect_channel_videos('channel123')
            
            assert result['channel_id'] == 'channel123'
            assert 'quality_videos' in result
            assert 'viral_videos' in result

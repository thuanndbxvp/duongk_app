"""
Unit tests for Transcript Engine.
"""
import pytest
from unittest.mock import patch, AsyncMock
from apps.api.modules.transcript.engine import TranscriptEngine, TranscriptTier


class TestTranscriptEngine:
    """Tests for TranscriptEngine."""
    
    @pytest.fixture
    def engine(self):
        return TranscriptEngine(supadata_api_key="test_key")
    
    def test_initialization(self, engine):
        """Test engine initialization."""
        assert engine.supadata_key == "test_key"
        assert getattr(engine, 'openai_client', None) is None
    
    @pytest.mark.asyncio
    async def test_get_transcript_tier1_success(self, engine):
        """Test successful Tier 1 transcript fetch."""
        with patch.object(engine, '_fetch_youtube_api', new_callable=AsyncMock) as mock:
            mock.return_value = {
                'video_id': 'test123',
                'transcript': 'Test transcript content',
                'language': 'vi'
            }
            
            result = await engine.get_transcript('test123')
            
            assert result is not None
            assert result['tier_used'] == 1
            assert result['transcript'] == 'Test transcript content'
    
    @pytest.mark.asyncio
    async def test_get_transcript_all_tiers_fail(self, engine):
        """Test when all tiers fail."""
        with patch.object(engine, '_fetch_youtube_api', new_callable=AsyncMock) as mock1, \
             patch.object(engine, '_fetch_supadata', new_callable=AsyncMock) as mock2, \
             patch.object(engine, '_fetch_openai_whisper', new_callable=AsyncMock) as mock3:
            
            mock1.return_value = None
            mock2.return_value = None
            mock3.side_effect = Exception("Whisper failed")
            
            result = await engine.get_transcript('test123')
            
            assert result is None

"""
Unit tests for RAG Service.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
import numpy as np
import os
import sys

# Đảm bảo có thể import module từ apps
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from apps.worker.services.rag_service import RAGService


class TestRAGService:
    """Test suite for RAGService."""

    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client."""
        return MagicMock()

    @pytest.fixture
    def mock_embedding_router(self):
        """Create mock EmbeddingRouter."""
        router = MagicMock()
        router.embed = AsyncMock(return_value=np.random.rand(1024))
        return router

    @pytest.fixture
    def rag_service(self, mock_supabase, mock_embedding_router):
        """Create RAGService instance."""
        return RAGService(mock_supabase, mock_embedding_router)

    @pytest.mark.asyncio
    async def test_retrieve_context_returns_chunks(self, rag_service, mock_supabase, mock_embedding_router):
        """Test retrieve_context returns chunks and context text."""
        # Setup mock RPC response
        mock_supabase.rpc.return_value.execute.return_value.data = [
            {
                'chunk_id': '11111111-1111-1111-1111-111111111111',
                'text': 'Xin chào các bạn, hôm nay tôi sẽ...',
                'section': 'hook',
                'timestamp_start': 0.0,
                'timestamp_end': 30.0,
                'similarity': 0.85,
                'mmr_score': 0.85,
            },
            {
                'chunk_id': '22222222-2222-2222-2222-222222222222',
                'text': 'Phần tiếp theo, chúng ta sẽ...',
                'section': 'body',
                'timestamp_start': 30.0,
                'timestamp_end': 180.0,
                'similarity': 0.72,
                'mmr_score': 0.65,
            },
        ]

        # Execute
        result = await rag_service.retrieve_context(
            assistant_id='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            query='Cách chăm sóc da',
            top_k=10,
            lambda_mmr=0.7,
        )

        # Verify
        assert 'chunks' in result
        assert 'context_text' in result
        assert 'num_chunks' in result
        assert result['num_chunks'] == 2
        assert len(result['chunks']) == 2
        assert '[00:00]' in result['context_text']
        assert '[00:30]' in result['context_text']

    @pytest.mark.asyncio
    async def test_retrieve_context_with_section_filter(self, rag_service, mock_supabase):
        """Test retrieve_context with section filter."""
        mock_supabase.rpc.return_value.execute.return_value.data = [
            {
                'chunk_id': '11111111-1111-1111-1111-111111111111',
                'text': 'Hook content',
                'section': 'hook',
                'timestamp_start': 0.0,
                'timestamp_end': 30.0,
                'similarity': 0.9,
                'mmr_score': 0.9,
            }
        ]

        await rag_service.retrieve_context(
            assistant_id='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            query='test',
            section_filter='hook',
        )

        # Verify RPC was called with section filter
        call_args = mock_supabase.rpc.call_args_list[0]
        args, kwargs = call_args
        assert args[0] == 'match_dna_chunks'
        assert args[1]['p_section_filter'] == 'hook'

    def test_assemble_context_formats_timestamps(self, rag_service):
        """Test _assemble_context formats timestamps correctly."""
        chunks = [
            {'timestamp_start': 0.0, 'timestamp_end': 30.0, 'text': 'First'},
            {'timestamp_start': 65.5, 'timestamp_end': 120.0, 'text': 'Second'},
        ]

        result = rag_service._assemble_context(chunks)

        assert '[00:00]' in result['context_text']
        assert '[01:05]' in result['context_text']  # 65.5s = 1m 5s
        assert 'First' in result['context_text']
        assert 'Second' in result['context_text']

    def test_build_script_prompt_formats_correctly(self, rag_service):
        """Test build_script_prompt generates valid prompt."""
        persona = {
            'channel_name': 'Kênh Mẫu',
            'emotional_signature': 'vui vẻ, gần gũi',
            'pacing_profile': {'wpm': 160},
            'mimic_rules': [
                {'rule_type': 'opening', 'do': ['Chào hỏi ấm áp']},
                {'rule_type': 'pacing', 'do': ['Nói chậm rãi']},
            ]
        }
        context = "Context from videos..."
        topic = "Cách làm bánh"

        prompt = rag_service.build_script_prompt(persona, context, topic)

        assert 'Kênh Mẫu' in prompt
        assert '160 WPM' in prompt
        assert 'Context from videos' in prompt
        assert 'Cách làm bánh' in prompt
        assert 'Chào hỏi ấm áp' in prompt
        assert '"title":' in prompt

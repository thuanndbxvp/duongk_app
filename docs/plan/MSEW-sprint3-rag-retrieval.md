# Sprint 3 Task Group 1: RAG Retrieval - Micro-Step Execution Workflow

## MSEW Checklist

- [ ] **Bước 1:** Tạo SQL migration file
- [ ] **Bước 2:** Implement RPC function với MMR
- [ ] **Bước 3:** Tạo Python RAGService
- [ ] **Bước 4:** Implement retrieve_context()
- [ ] **Bước 5:** Viết unit tests
- [ ] **Bước 6:** Self-verify với acceptance criteria

---

## Bước 1: Tạo SQL Migration File

**File:** `supabase/migrations/0014_match_dna_chunks.sql`

```sql
-- ============================================================
-- Migration: 0014_match_dna_chunks.sql
-- Purpose: RAG retrieval với MMR (Maximal Marginal Relevance)
-- ============================================================

-- RPC function: Vector search với MMR reranking
CREATE OR REPLACE FUNCTION match_dna_chunks(
    p_assistant_id UUID,
    p_query_embedding VECTOR(1024),
    p_top_k INT DEFAULT 10,
    p_lambda FLOAT DEFAULT 0.7,
    p_section_filter TEXT DEFAULT NULL
) RETURNS TABLE(
    chunk_id UUID,
    text TEXT,
    section TEXT,
    timestamp_start FLOAT,
    timestamp_end FLOAT,
    similarity FLOAT,
    mmr_score FLOAT
) AS $$
DECLARE
    v_result JSONB;
BEGIN
    -- Greedy MMR selection
    WITH RECURSIVE mmr_selection AS (
        -- Base case: select highest similarity chunk
        SELECT
            dc.id AS chunk_id,
            dc.text,
            dc.section,
            dc.timestamp_start,
            dc.timestamp_end,
            1 - (dc.embedding <=> p_query_embedding) AS similarity,
            (1 - (dc.embedding <=> p_query_embedding))::FLOAT AS mmr_score,
            ARRAY[dc.id] AS selected_ids,
            1 AS iteration
        FROM dna_chunks dc
        WHERE dc.assistant_id = p_assistant_id
            AND dc.expires_at > NOW()
            AND (p_section_filter IS NULL OR dc.section = p_section_filter)
        ORDER BY (dc.embedding <=> p_query_embedding) ASC
        LIMIT 1
        
        UNION ALL
        
        -- Recursive case: select based on MMR score
        SELECT
            dc.id AS chunk_id,
            dc.text,
            dc.section,
            dc.timestamp_start,
            dc.timestamp_end,
            1 - (dc.embedding <=> p_query_embedding) AS similarity,
            (p_lambda * (1 - (dc.embedding <=> p_query_embedding)) - 
             (1 - p_lambda) * COALESCE(
                 (SELECT MAX(1 - (dc.embedding <=> dc2.embedding))
                  FROM dna_chunks dc2
                  WHERE dc2.id = ANY(ms.selected_ids)),
                 0
             ))::FLOAT AS mmr_score,
            array_append(ms.selected_ids, dc.id) AS selected_ids,
            ms.iteration + 1 AS iteration
        FROM dna_chunks dc, mmr_selection ms
        WHERE dc.assistant_id = p_assistant_id
            AND dc.expires_at > NOW()
            AND (p_section_filter IS NULL OR dc.section = p_section_filter)
            AND dc.id != ALL(ms.selected_ids)
            AND ms.iteration < p_top_k
    )
    SELECT jsonb_agg(
        jsonb_build_object(
            'chunk_id', chunk_id,
            'text', text,
            'section', section,
            'timestamp_start', timestamp_start,
            'timestamp_end', timestamp_end,
            'similarity', similarity,
            'mmr_score', mmr_score
        )
    ) INTO v_result
    FROM (
        SELECT DISTINCT ON (chunk_id) *
        FROM mmr_selection
        ORDER BY chunk_id, mmr_score DESC
    ) ranked;

    -- Return results
    RETURN QUERY
    SELECT 
        (j->>'chunk_id')::UUID,
        (j->>'text')::TEXT,
        (j->>'section')::TEXT,
        COALESCE((j->>'timestamp_start')::FLOAT, 0),
        COALESCE((j->>'timestamp_end')::FLOAT, 0),
        (j->>'similarity')::FLOAT,
        COALESCE((j->>'mmr_score')::FLOAT, 0)
    FROM jsonb_array_elements(COALESCE(v_result, '[]'::jsonb)) j;
END;
$$ LANGUAGE plpgsql STABLE;
```

---

## Bước 2: Tạo Python RAG Service

**File:** `apps/worker/services/rag_service.py`

```python
"""
RAG Service - Retrieval Augmented Generation for script generation.
"""
from typing import Optional
from supabase import Client
from apps.api.modules.rag.embedding_router import EmbeddingRouter


class RAGService:
    """Service for retrieving relevant DNA chunks using RAG."""

    def __init__(self, supabase: Client, embedding_router: EmbeddingRouter):
        """
        Initialize RAG service.
        
        Args:
            supabase: Supabase client (admin/service_role)
            embedding_router: Router for embedding generation
        """
        self.supabase = supabase
        self.embedding_router = embedding_router

    async def retrieve_context(
        self,
        assistant_id: str,
        query: str,
        top_k: int = 10,
        lambda_mmr: float = 0.7,
        section_filter: Optional[str] = None,
    ) -> dict:
        """
        Retrieve relevant DNA chunks using MMR search.
        
        Args:
            assistant_id: UUID of channel assistant
            query: Search query text
            top_k: Number of chunks to retrieve
            lambda_mmr: MMR lambda (0-1, higher = more relevance)
            section_filter: Optional section filter ('hook', 'body', 'cta', 'broll')
            
        Returns:
            dict with keys: chunks, context_text, num_chunks
        """
        # 1. Embed query
        query_embedding = await self.embedding_router.embed(query)

        # 2. Call RPC for MMR search
        result = self.supabase.rpc('match_dna_chunks', {
            'p_assistant_id': assistant_id,
            'p_query_embedding': query_embedding.tolist(),
            'p_top_k': top_k,
            'p_lambda': lambda_mmr,
            'p_section_filter': section_filter,
        }).execute()

        chunks = result.data or []
        return self._assemble_context(chunks)

    def _assemble_context(self, chunks: list[dict]) -> dict:
        """
        Assemble retrieved chunks into formatted context.
        
        Args:
            chunks: List of chunk dictionaries from RPC
            
        Returns:
            dict with formatted context
        """
        context_parts = []
        for chunk in chunks:
            # Format timestamp
            ts = chunk.get('timestamp_start')
            if ts is not None:
                minutes, seconds = int(ts // 60), int(ts % 60)
                timestamp = f"[{minutes:02d}:{seconds:02d}]"
            else:
                timestamp = ""

            # Append formatted text
            context_parts.append(f"{timestamp} {chunk['text']}")

        return {
            'chunks': chunks,
            'context_text': '\n\n---\n\n'.join(context_parts),
            'num_chunks': len(chunks),
        }

    def build_script_prompt(
        self,
        channel_persona: dict,
        rag_context: str,
        topic: str,
    ) -> str:
        """
        Build system prompt with RAG context for script generation.
        
        Args:
            channel_persona: Channel DNA data
            rag_context: Retrieved context text
            topic: User-provided topic
            
        Returns:
            Formatted prompt string
        """
        mimic_rules = channel_persona.get('mimic_rules', [])
        rules_text = '\n'.join([
            f"- Rule {i+1}: {rule.get('rule_type', 'general')}: {rule.get('do', ['N/A'])[0]}"
            for i, rule in enumerate(mimic_rules[:3])
        ])

        return f"""Bạn là một chuyên gia viết kịch bản YouTube, chuyên về phong cách của kênh {channel_persona.get('channel_name', 'này')}.

## Phong cách kênh:
- Emotional signature: {channel_persona.get('emotional_signature', 'N/A')}
- Pacing: {channel_persona.get('pacing_profile', {}).get('wpm', 150)} WPM

## Mimic Rules (bắt BUỘC tuân theo):
{rules_text or '- Không có rules cụ thể'}

## Context từ các video đã phân tích:
{rag_context}

## Chủ đề cần viết:
{topic}

## Yêu cầu:
1. Viết kịch bản hoàn chỉnh, bám sát phong cách kênh
2. Có Hook mạnh ở đầu (30 giây đầu tiên)
3. Cấu trúc rõ ràng: Hook → Body → CTA
4. Độ dài: 8-12 phút
5. Thêm ghi chú [B-ROLL: mô tả] ở các vị trí cần B-roll

Trả lời JSON theo schema:
{{
  "title": "Tiêu đề video",
  "hook": "30 giây đầu (hook)",
  "body": "Nội dung chính (8-10 phút)",
  "cta": "Call to action cuối video",
  "estimated_duration_minutes": 10,
  "broll_positions": ["vị trí 1", "vị trí 2"],
  "mimic_score": 8.5
}}"""
```

---

## Bước 3: Viết Unit Tests

**File:** `apps/worker/services/test_rag_service.py`

```python
"""
Unit tests for RAG Service.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
import numpy as np
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
        assert call_args[1]['name'] == 'match_dna_chunks'
        assert call_args[1]['params']['p_section_filter'] == 'hook'

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
```

---

## Bước 4: Verify và Push

**Sau khi hoàn thành code, chạy lệnh:**

```bash
# 1. Apply migration locally (nếu có Supabase local)
supabase db push

# 2. Run tests
cd apps/worker && pytest services/test_rag_service.py -v

# 3. Check coverage
pytest --cov=apps.worker.services.rag_service --cov-report=term-missing
```

---

## Step-by-Step Commands for Tier 2

```bash
# Giao việc cho Tier 2:
# ============================================================
# TASK: Sprint 3 - RAG Retrieval
# ============================================================

# 1. Đọc context
cat docs/plan/CONTEXT-sprint3-rag-retrieval.md

# 2. Check skill routing
cat docs/plan/SKILL-ROUTING-sprint3-rag-retrieval.md

# 3. Đọc plan
cat docs/plan/PLAN-sprint3-rag-retrieval.md

# 4. Implement theo MSEW
cat docs/plan/MSEW-sprint3-rag-retrieval.md

# 5. Self-verify
cat docs/plan/ACCEPTANCE-sprint3-rag-retrieval.md
```

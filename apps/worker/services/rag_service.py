"""
RAG Service - Retrieval Augmented Generation for script generation.
"""
from typing import Optional
from supabase import Client
from apps.api.modules.rag.embedder import Embedder

class RAGService:
    """Service for retrieving relevant DNA chunks using RAG."""

    def __init__(self, supabase: Client, embedder: Embedder):
        """
        Initialize RAG service.
        
        Args:
            supabase: Supabase client (admin/service_role)
            embedder: Embedder for generating vectors
        """
        self.supabase = supabase
        self.embedder = embedder

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
        embeddings = await self.embedder.embed_texts([query])
        query_embedding = embeddings[0]

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
            context_parts.append(f"{timestamp} {chunk.get('text', '')}")

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
    def build_context_with_evidence(
        self,
        channel_persona: dict,
        rag_context: str,
        topic: str,
        source_insight_ids: list[str] | None = None,
    ) -> str:
        """
        Build script prompt with optional evidence injection from insights.

        Phase 06: If source_insight_ids provided, load evidence snippets
        and inject them into the prompt as [evidence] block.
        """
        prompt = self.build_script_prompt(channel_persona, rag_context, topic)

        if source_insight_ids and len(source_insight_ids) > 0:
            # Load evidence from insight_items
            snippets = []
            for iid in source_insight_ids[:5]:
                insight = self.supabase.table('insight_items').select('body, evidence_comment_ids').eq('id', iid).maybe_single().execute()
                if insight.data:
                    # Escape prompt injection
                    body = insight.data.get('body', '').replace('```', "'''")
                    evidence_ids = insight.data.get('evidence_comment_ids', [])
                    snippets.append(f"- {body} (evidence: {len(evidence_ids)} comments)")

            if snippets:
                evidence_block = "\n".join(snippets)
                prompt += f"\n\n[evidence]\n{evidence_block}\n[evidence_end]\n"

        return prompt


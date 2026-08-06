"""
Service: project_context — Build consolidated context for project script generation.
Phase 01: Combines brief_payload + optional channel_dna + rag_context.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from supabase import Client


@dataclass
class ProjectContext:
    """Consolidated context for script generation."""
    project_id: str
    brief_payload: dict = field(default_factory=dict)
    channel_dna: Optional[dict] = None
    rag_context: str = ""


async def build_project_context(
    supabase: Client,
    project_id: str,
    rag_service=None,
    query: str = "",
) -> ProjectContext:
    """
    Build consolidated ProjectContext from DB + optional RAG.

    Args:
        supabase: Supabase admin client
        project_id: UUID of the project
        rag_service: Optional RAGService instance for channel DNA retrieval
        query: Query topic for RAG retrieval

    Returns:
        ProjectContext with brief, optional channel DNA, and RAG context.
    """
    ctx = ProjectContext(project_id=project_id)

    # 1. Fetch latest brief
    brief_rows = (
        supabase.table('project_briefs')
        .select('*')
        .eq('project_id', project_id)
        .order('version', desc=True)
        .limit(1)
        .execute()
    )
    if brief_rows.data:
        ctx.brief_payload = brief_rows.data[0]

    # 2. Fetch project for channel_assistant_id linkage
    project_rows = (
        supabase.table('projects')
        .select('id, channel_assistant_id, mode')
        .eq('id', project_id)
        .single()
        .execute()
    )

    # 3. If project is clone_channel mode, pull channel DNA
    if project_rows.data and project_rows.data.get('channel_assistant_id'):
        assistant_id = project_rows.data['channel_assistant_id']
        assistant_rows = (
            supabase.table('channel_assistants')
            .select('persona, pacing_profile, channel_name')
            .eq('id', assistant_id)
            .single()
            .execute()
        )
        if assistant_rows.data:
            ctx.channel_dna = assistant_rows.data

    # 4. RAG retrieval if rag_service is provided
    if rag_service and query:
        try:
            # For clone_channel: retrieve from assistant's DNA chunks
            assistant_id = project_rows.data.get('channel_assistant_id') if project_rows.data else None
            if assistant_id:
                result = await rag_service.retrieve_context(
                    assistant_id=assistant_id,
                    query=query,
                    top_k=10,
                )
                ctx.rag_context = result.get('context_text', '')
            else:
                # Blank mode: no RAG, just use brief as context
                ctx.rag_context = _build_blank_context(ctx.brief_payload, query)
        except Exception:
            # Graceful degradation — use blank fallback
            ctx.rag_context = _build_blank_context(ctx.brief_payload, query)

    return ctx


def _build_blank_context(brief: dict, query: str) -> str:
    """Build blank context when no channel DNA is available."""
    topic = brief.get('topic', query)
    audience = brief.get('audience', 'general')
    language = brief.get('language', 'vi')
    tone = brief.get('tone', 'casual')
    visual = brief.get('visual_style', 'cinematic')
    duration = brief.get('duration_target_seconds', 600)

    return f"""## Topic: {topic}
## Audience: {audience}
## Language: {language}
## Tone: {tone}
## Visual Style: {visual}
## Target Duration: {duration}s ({(duration // 60)}m {duration % 60}s)

Write a script for this topic in {language} language targeting {audience} audience.
Use a {tone} tone and {visual} visual style throughout.
"""

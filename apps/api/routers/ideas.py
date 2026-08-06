"""
Routers cho Ideas: get ideas của assistant.
Mounted dưới /api/ideas.
"""
from fastapi import APIRouter, Depends, HTTPException
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin


router = APIRouter(prefix="/api/ideas", tags=["Ideas"])


@router.get("/{assistant_id}")
async def get_ideas(
    assistant_id: str,
    user_id: str = Depends(get_supabase_user),
    limit: int = 50,
):
    """Lấy generated ideas của assistant (verify ownership)."""
    admin = get_supabase_admin()
    
    # Verify ownership
    assistant = (
        admin.table('channel_assistants')
        .select('id')
        .eq('id', assistant_id)
        .eq('user_id', user_id)
        .single()
        .execute()
    )
    if not assistant.data:
        raise HTTPException(404, 'Assistant not found')

    result = (
        admin.table('generated_ideas')
        .select('*')
        .eq('assistant_id', assistant_id)
        .order('gap_score', desc=True)
        .limit(min(limit, 200))
        .execute()
    )
    return result.data or []
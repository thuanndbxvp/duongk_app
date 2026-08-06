"""
Routers cho Channel Assistant CRUD.
Mounted dưới /api/assistants.
"""
from fastapi import APIRouter, Depends, HTTPException
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from typing import Optional


router = APIRouter(prefix="/api/assistants", tags=["Assistants"])


@router.get("")
async def list_assistants(
    user_id: str = Depends(get_supabase_user),
    limit: int = 50,
    offset: int = 0,
):
    """
    List assistants của user hiện tại.
    
    Query params:
        limit: số row tối đa (default 50, max 200).
        offset: pagination offset.
    
    Returns:
        List of channel_assistants rows.
    """
    admin = get_supabase_admin()
    result = (
        admin.table('channel_assistants')
        .select('*')
        .eq('user_id', user_id)
        .order('created_at', desc=True)
        .range(offset, offset + min(limit, 200) - 1)
        .execute()
    )
    return result.data or []


@router.get("/{assistant_id}")
async def get_assistant(
    assistant_id: str,
    user_id: str = Depends(get_supabase_user),
):
    """
    Lấy chi tiết 1 assistant. Verify ownership.
    
    Args:
        assistant_id: UUID.
    
    Raises:
        HTTPException 404 nếu không tồn tại hoặc không thuộc user.
    """
    admin = get_supabase_admin()
    result = (
        admin.table('channel_assistants')
        .select('*')
        .eq('id', assistant_id)
        .eq('user_id', user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(404, 'Assistant not found')
    return result.data


@router.delete("/{assistant_id}")
async def delete_assistant(
    assistant_id: str,
    user_id: str = Depends(get_supabase_user),
):
    """
    Soft delete assistant: set status='deleted'.
    
    Returns:
        204 No Content.
    """
    admin = get_supabase_admin()
    # Verify ownership trước
    existing = (
        admin.table('channel_assistants')
        .select('id')
        .eq('id', assistant_id)
        .eq('user_id', user_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(404, 'Assistant not found')
    
    admin.table('channel_assistants').update({
        'status': 'deleted',
        'updated_at': 'now()',
    }).eq('id', assistant_id).execute()
    
    return None  # 204
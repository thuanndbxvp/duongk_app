"""
User endpoints - Get/update current user info.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin


router = APIRouter()


class UserUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    avatar_url: str | None = None
    credits: int
    tier: str
    role: str = 'user'
    created_at: str


@router.get('/users/me', response_model=UserResponse)
async def get_me(user_id: str = Depends(get_supabase_user)):
    """Get current user info."""
    admin = get_supabase_admin()
    
    user = (
        admin.table('users')
        .select('*')
        .eq('id', user_id)
        .single()
        .execute()
    )
    
    if not user.data:
        raise HTTPException(404, 'User not found')
    
    return user.data


@router.patch('/users/me', response_model=UserResponse)
async def update_me(
    update: UserUpdate,
    user_id: str = Depends(get_supabase_user),
):
    """Update current user profile."""
    admin = get_supabase_admin()
    
    update_data = update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(400, 'No fields to update')
    
    result = (
        admin.table('users')
        .update(update_data)
        .eq('id', user_id)
        .execute()
    )
    
    if not result.data:
        raise HTTPException(404, 'User not found')
    
    return result.data[0]


@router.get('/users/me/credits')
async def get_my_credits(user_id: str = Depends(get_supabase_user)):
    """Get current user credit balance."""
    admin = get_supabase_admin()
    
    user = (
        admin.table('users')
        .select('credits, tier')
        .eq('id', user_id)
        .single()
        .execute()
    )
    
    if not user.data:
        raise HTTPException(404, 'User not found')
    
    return {
        'credits': user.data['credits'],
        'tier': user.data['tier'],
    }

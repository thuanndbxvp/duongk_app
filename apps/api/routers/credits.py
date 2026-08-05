from fastapi import APIRouter, Depends
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.credit_manager import CreditManager


router = APIRouter()


@router.get('/credits/balance')
async def get_balance(user_id: str = Depends(get_supabase_user)):
    """Get current credit balance."""
    manager = CreditManager()
    return {
        'credits': manager.get_balance(user_id),
        'tier': _get_user_tier(user_id),
    }


@router.get('/credits/transactions')
async def get_transactions(user_id: str = Depends(get_supabase_user)):
    """Get credit transaction history."""
    admin = get_supabase_admin()
    result = (
        admin.table('credit_transactions')
        .select('*, jobs(task_type)')
        .eq('user_id', user_id)
        .order('created_at', desc=True)
        .limit(50)
        .execute()
    )
    return result.data


def _get_user_tier(user_id: str) -> str:
    admin = get_supabase_admin()
    user = admin.table('users').select('tier').eq('id', user_id).single().execute()
    return user.data['tier'] if user.data else 'free'

"""
Credit Manager - Hold/Adjust/Commit/Refund pattern.
"""
from typing import Optional
from uuid import UUID
from apps.api.dependencies.supabase import get_supabase_admin


PRICING = {
    'niche_validate': 5,
    'collect_channel': 10,
    'deep_analysis': 50,
    'script_generation': 30,
    'scene_breakdown': 10,
    'idea_generation': 5,
    'rag_retrieve': 1,
}


def get_user_role(user_id: str) -> str:
    """
    Lấy role của user từ bảng users.
    
    Args:
        user_id: UUID string của user.
    
    Returns:
        'user' | 'admin' | 'super_admin'. Default 'user' nếu user không tồn tại.
    """
    admin = get_supabase_admin()
    result = (
        admin.table('users')
        .select('role')
        .eq('id', user_id)
        .single()
        .execute()
    )
    if result.data and 'role' in result.data:
        return result.data['role']
    return 'user'


class CreditManager:
    """Service for managing user credits."""
    
    def __init__(self):
        self.admin = get_supabase_admin()
    
    def get_pricing(self, job_type: str) -> int:
        """Get credit cost for a job type."""
        return PRICING.get(job_type, 0)
    
    def get_balance(self, user_id: str) -> int:
        """Get user's current credit balance."""
        user = (
            self.admin.table('users')
            .select('credits')
            .eq('id', user_id)
            .single()
            .execute()
        )
        return user.data['credits'] if user.data else 0
    
    def hold(self, user_id: str, job_id: str, amount: int) -> dict:
        """
        Hold credits for a job (atomic).
        
        Raises:
            ValueError: Insufficient credits or user not found
        """
        result = self.admin.rpc('hold_credits', {
            'p_user_id': user_id,
            'p_amount': amount,
            'p_job_id': job_id,
        }).execute()
        
        if not result.data:
            raise ValueError('Hold failed')
        
        return {
            'transaction_id': result.data[0]['transaction_id'],
            'balance_after': result.data[0]['balance_after'],
        }
    
    def adjust(self, job_id: str, final_amount: int) -> dict:
        """
        Adjust hold to final amount (refund difference).
        """
        result = self.admin.rpc('partial_commit_credits', {
            'p_job_id': job_id,
            'p_final_amount': final_amount,
        }).execute()
        
        return {
            'refund_amount': result.data[0].get('refund_amount', 0) if result.data else 0,
        }
    
    def commit(self, job_id: str) -> None:
        """Mark transaction as committed."""
        self.admin.table('credit_transactions').update({
            'metadata': {'status': 'committed'},
        }).eq('job_id', job_id).execute()
    
    def refund(self, job_id: str) -> int:
        """Refund credits on failure."""
        result = self.admin.rpc('refund_credits', {
            'p_job_id': job_id,
        }).execute()
        
        return result.data if result.data else 0

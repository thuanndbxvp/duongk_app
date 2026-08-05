"""
Dependency for charging credits before processing.
"""
from fastapi import HTTPException, Depends
from apps.api.dependencies.auth import get_supabase_user
from apps.api.services.credit_manager import CreditManager


def credit_required(
    job_type: str,
    user_id: str = Depends(get_supabase_user),
):
    """
    Check user has enough credits, then hold.
    
    Args:
        job_type: Type of job (must be in PRICING)
        user_id: From JWT (auto-injected)
        
    Raises:
        HTTPException: 402 if insufficient credits
    """
    manager = CreditManager()
    cost = manager.get_pricing(job_type)
    
    if cost == 0:
        return
    
    balance = manager.get_balance(user_id)
    if balance < cost:
        raise HTTPException(
            status_code=402,
            detail=f'Insufficient credits: have {balance}, need {cost}',
        )

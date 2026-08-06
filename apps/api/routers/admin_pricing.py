"""
Admin Pricing Config — 2 endpoints.
Mounted dưới /api/admin/pricing.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from apps.api.dependencies.admin import require_admin
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.audit import log_admin_action


router = APIRouter(prefix="/api/admin/pricing", tags=["Admin Pricing"])


class PricingUpdate(BaseModel):
    credits: Optional[int] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None


@router.patch("/{job_type}")
async def update_pricing(
    job_type: str,
    update: PricingUpdate,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Update credit_pricing row + audit log."""
    db = get_supabase_admin()
    
    before = db.table('credit_pricing').select('*').eq('job_type', job_type).single().execute().data
    if not before:
        raise HTTPException(404, 'Job type not found')
    
    update_data = update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(400, 'No fields to update')
    update_data['updated_by'] = admin_id
    update_data['updated_at'] = 'now()'
    
    db.table('credit_pricing').update(update_data).eq('job_type', job_type).execute()
    after = db.table('credit_pricing').select('*').eq('job_type', job_type).single().execute().data
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='pricing.update',
        target_type='pricing',
        target_id=job_type,
        before=before,
        after=after,
        ip=request.client.host if request.client else None,
    )
    
    return after


@router.post("/reload")
async def reload_pricing(
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """
    Publish Redis channel để worker reload cache.
    Phase 6 STUB: chỉ ghi log. Phase 7+ sẽ impl Redis pub/sub thật.
    """
    admin_email = get_supabase_admin().table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='pricing.reload',
        target_type='pricing',
        reason='Manual reload pricing cache',
        ip=request.client.host if request.client else None,
    )
    return {'status': 'reload_queued', 'note': 'Phase 6 stub — Redis pub/sub Phase 7+'}
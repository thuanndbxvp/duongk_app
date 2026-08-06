"""
Admin Alerts Management — 2 endpoints.
Mounted dưới /api/admin/alerts.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
from uuid import UUID
from apps.api.dependencies.admin import require_admin
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.audit import log_admin_action


router = APIRouter(prefix="/api/admin/alerts", tags=["Admin Alerts"])


@router.get("")
async def list_alerts(
    admin_id: str = Depends(require_admin),
    severity: Optional[str] = None,
    category: Optional[str] = None,
    include_resolved: bool = False,
    limit: int = 100,
):
    """List admin_alerts. Default: unresolved only."""
    db = get_supabase_admin()
    query = db.table('admin_alerts').select('*')
    
    if not include_resolved:
        query = query.is_('resolved_at', 'null')
    if severity:
        query = query.eq('severity', severity)
    if category:
        query = query.eq('category', category)
    
    result = query.order('created_at', desc=True).limit(limit).execute()
    return result.data or []


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    request: Request,
    admin_id: str = Depends(require_admin),
):
    """Resolve alert."""
    db = get_supabase_admin()
    
    before = db.table('admin_alerts').select('*').eq('id', alert_id).single().execute().data
    if not before:
        raise HTTPException(404, 'Alert not found')
    if before.get('resolved_at'):
        raise HTTPException(400, 'Alert already resolved')
    
    db.table('admin_alerts').update({
        'resolved_at': 'now()',
        'resolved_by': admin_id,
    }).eq('id', alert_id).execute()
    
    admin_email = db.table('users').select('email').eq('id', admin_id).single().execute().data.get('email', '')
    log_admin_action(
        admin_id=UUID(admin_id),
        admin_email=admin_email,
        action='alert.resolve',
        target_type='alert',
        target_id=alert_id,
        before={'category': before.get('category'), 'severity': before.get('severity')},
        ip=request.client.host if request.client else None,
    )
    
    return {'id': alert_id, 'resolved': True}
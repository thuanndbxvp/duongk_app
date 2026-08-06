"""
Admin Audit Log Viewer — 3 endpoints (read-only).
Mounted dưới /api/admin/audit-logs.
"""
import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from typing import Optional
from apps.api.dependencies.admin import require_admin, require_mfa_for_critical
from apps.api.dependencies.supabase import get_supabase_admin


router = APIRouter(prefix="/api/admin/audit-logs", tags=["Admin Audit Logs"])


@router.get("")
async def list_audit_logs(
    admin_id: str = Depends(require_admin),
    admin_email: Optional[str] = None,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    """
    List audit logs với filter + full-text search (via admin_email/action/target_id).
    """
    db = get_supabase_admin()
    query = db.table('admin_audit_logs').select('*', count='exact')
    
    if admin_email:
        query = query.ilike('admin_email', f'%{admin_email}%')
    if action:
        query = query.ilike('action', f'%{action}%')
    if target_type:
        query = query.eq('target_type', target_type)
    if target_id:
        query = query.ilike('target_id', f'%{target_id}%')
    if from_date:
        query = query.gte('created_at', from_date)
    if to_date:
        query = query.lte('created_at', to_date)
    
    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1).order('created_at', desc=True)
    
    result = query.execute()
    return {
        'logs': result.data or [],
        'total': result.count or 0,
        'page': page,
        'limit': limit,
    }


@router.get("/{log_id}")
async def get_audit_log(
    log_id: str,
    admin_id: str = Depends(require_admin),
):
    """Lấy chi tiết 1 audit log (xem before/after JSON đã masked)."""
    db = get_supabase_admin()
    result = db.table('admin_audit_logs').select('*').eq('id', log_id).single().execute()
    if not result.data:
        raise HTTPException(404, 'Audit log not found')
    return result.data


@router.get("/export/csv")
async def export_audit_csv(
    admin_id: str = Depends(require_admin),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    """Export audit log → CSV. Cap 10k rows."""
    db = get_supabase_admin()
    
    if not from_date or not to_date:
        raise HTTPException(400, 'from_date and to_date required (max 30 days range)')
    
    # Validate date range
    try:
        from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
        if (to_dt - from_dt).days > 30:
            raise HTTPException(400, 'Date range max 30 days')
    except ValueError:
        raise HTTPException(400, 'Invalid date format (use ISO 8601)')
    
    query = (
        db.table('admin_audit_logs')
        .select('id, admin_email, action, target_type, target_id, ip, user_agent, reason, created_at')
        .gte('created_at', from_date)
        .lte('created_at', to_date)
        .order('created_at', desc=True)
        .limit(10000)
    )
    result = query.execute()
    
    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'admin_email', 'action', 'target_type', 'target_id', 'ip', 'user_agent', 'reason', 'created_at'])
    for row in (result.data or []):
        writer.writerow([
            row['id'], row['admin_email'], row['action'], row['target_type'],
            row['target_id'], row.get('ip'), row.get('user_agent'),
            row.get('reason'), row['created_at'],
        ])
    
    return Response(
        content=output.getvalue(),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="admin-audit-logs.csv"'},
    )
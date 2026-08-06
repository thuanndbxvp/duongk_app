"""
Admin Credit Management — 4 endpoints.
Mounted dưới /api/admin/credit.
"""
import csv
import io
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Optional
from apps.api.dependencies.admin import require_admin


router = APIRouter(prefix="/api/admin/credit", tags=["Admin Credit"])


@router.get("/ledger")
async def get_ledger(
    admin_id: str = Depends(require_admin),
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    limit: int = 100,
):
    """
    Credit ledger toàn hệ thống. Filter + paginate.
    """
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    
    query = db.table('credit_transactions').select('*, users!inner(email), jobs(task_type)', count='exact')
    
    if user_id:
        query = query.eq('user_id', user_id)
    if action:
        query = query.eq('action', action)
    if from_date:
        query = query.gte('created_at', from_date)
    if to_date:
        query = query.lte('created_at', to_date)
    
    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1).order('created_at', desc=True)
    
    result = query.execute()
    return {
        'transactions': result.data or [],
        'total': result.count or 0,
        'page': page,
        'limit': limit,
    }


@router.get("/stats")
async def get_stats(
    admin_id: str = Depends(require_admin),
):
    """
    4 stat metrics + sparkline 7 ngày.
    """
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    
    # Stats đơn giản (dùng table query thay vì RPC)
    all_tx = db.table('credit_transactions').select('amount, action, created_at').gte('created_at', 'now()-interval \'90 days\'').execute()
    total_issued = sum(t['amount'] for t in (all_tx.data or []) if t['amount'] > 0 and t['action'] != 'refund')
    total_spent = sum(-t['amount'] for t in (all_tx.data or []) if t['amount'] < 0 and t['action'] != 'refund')
    total_refunded = sum(t['amount'] for t in (all_tx.data or []) if t['action'] == 'refund')
    
    # Total hold (running jobs)
    hold_jobs = db.table('jobs').select('credits_held').eq('status', 'running').execute()
    total_hold = sum(j['credits_held'] or 0 for j in (hold_jobs.data or []))
    
    # Sparkline 7 ngày: group by day
    sparkline = []
    for i in range(7):
        day = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_tx = db.table('credit_transactions').select('amount').gte('created_at', f'{day}T00:00:00').lte('created_at', f'{day}T23:59:59').execute()
        day_spent = sum(-t['amount'] for t in (day_tx.data or []) if t['amount'] < 0)
        sparkline.append({'date': day, 'spent': day_spent})
    
    return {
        'total_issued': total_issued,
        'total_spent': total_spent,
        'total_hold': total_hold,
        'total_refunded': total_refunded,
        'sparkline': list(reversed(sparkline)),
    }


@router.get("/export")
async def export_csv(
    admin_id: str = Depends(require_admin),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    """
    Export CSV — max 1 năm range.
    """
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    
    query = db.table('credit_transactions').select('id, user_id, action, amount, balance_after, reason, created_at, users!inner(email)')
    if from_date:
        query = query.gte('created_at', from_date)
    if to_date:
        query = query.lte('created_at', to_date)
    query = query.order('created_at', desc=True).limit(50000)  # safety cap
    
    result = query.execute()
    
    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['tx_id', 'user_email', 'action', 'amount', 'balance_after', 'reason', 'created_at'])
    for tx in (result.data or []):
        writer.writerow([
            tx['id'],
            tx.get('users', {}).get('email', ''),
            tx['action'],
            tx['amount'],
            tx['balance_after'],
            tx.get('reason', ''),
            tx['created_at'],
        ])
    
    return Response(
        content=output.getvalue(),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="credit-ledger.csv"'},
    )


@router.get("/pricing")
async def list_pricing(
    admin_id: str = Depends(require_admin),
):
    """List credit_pricing rows (admin view — không filter enabled)."""
    from apps.api.dependencies.supabase import get_supabase_admin
    db = get_supabase_admin()
    result = db.table('credit_pricing').select('*').order('credits').execute()
    return result.data or []
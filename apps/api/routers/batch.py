"""
FastAPI router for batch — Phase 10.
"""
from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.schemas.batch import (
    BatchCreateRequest, BatchResponse, BatchItemResponse, CostEstimate,
)
from apps.worker.services.cost_estimator import estimate_cost

router = APIRouter(prefix="/api/batches", tags=["Batch"])


@router.post("", response_model=BatchResponse, status_code=201)
async def create_batch(req: BatchCreateRequest, user_id: str = Depends(get_supabase_user)):
    """Create a new batch run."""
    admin = get_supabase_admin()
    cost = estimate_cost(req.task_type, len(req.project_ids))

    batch_res = admin.table('batch_runs').insert({
        'owner_id': user_id, 'name': req.name,
        'status': 'estimated', 'total_items': len(req.project_ids),
        'total_cost_estimate': cost['total'],
    }).execute()

    if not batch_res.data:
        raise HTTPException(500, 'Failed to create batch')

    batch_id = batch_res.data[0]['id']

    for i, pid in enumerate(req.project_ids):
        admin.table('batch_items').insert({
            'batch_id': batch_id, 'project_id': str(pid),
            'item_index': i, 'task_type': req.task_type,
            'cost_estimate': cost['per_item'],
        }).execute()

    return BatchResponse(**admin.table('batch_runs').select('*').eq('id', batch_id).single().execute().data)


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(batch_id: UUID, user_id: str = Depends(get_supabase_user)):
    admin = get_supabase_admin()
    b = admin.table('batch_runs').select('*').eq('id', str(batch_id)).eq('owner_id', user_id).maybe_single().execute()
    if not b.data:
        raise HTTPException(404, 'Not found')
    return BatchResponse(**b.data)


@router.get("/{batch_id}/items", response_model=list[BatchItemResponse])
async def get_batch_items(batch_id: UUID, user_id: str = Depends(get_supabase_user)):
    admin = get_supabase_admin()
    b = admin.table('batch_runs').select('id').eq('id', str(batch_id)).eq('owner_id', user_id).maybe_single().execute()
    if not b.data:
        raise HTTPException(404, 'Not found')
    items = admin.table('batch_items').select('*').eq('batch_id', str(batch_id)).order('item_index').execute()
    return [BatchItemResponse(**i) for i in (items.data or [])]


@router.post("/{batch_id}/approve")
async def approve_batch(batch_id: UUID, user_id: str = Depends(get_supabase_user)):
    admin = get_supabase_admin()
    b = admin.table('batch_runs').select('*').eq('id', str(batch_id)).eq('owner_id', user_id).single().execute()
    if not b.data:
        raise HTTPException(404, 'Not found')
    if b.data['status'] != 'estimated':
        raise HTTPException(400, 'Batch must be in estimated status')

    admin.table('batch_runs').update({'status': 'approved'}).eq('id', str(batch_id)).execute()
    try:
        from apps.worker.services.batch_fanout import run_batch
        import asyncio
        asyncio.create_task(run_batch(admin, UUID(str(batch_id))))
    except Exception:
        pass
    return {"status": "approved", "batch_id": str(batch_id)}


@router.post("/{batch_id}/cancel")
async def cancel_batch(batch_id: UUID, user_id: str = Depends(get_supabase_user)):
    admin = get_supabase_admin()
    b = admin.table('batch_runs').select('*').eq('id', str(batch_id)).eq('owner_id', user_id).single().execute()
    if not b.data:
        raise HTTPException(404, 'Not found')
    admin.table('batch_runs').update({'status': 'cancelled'}).eq('id', str(batch_id)).execute()
    return {"status": "cancelled"}

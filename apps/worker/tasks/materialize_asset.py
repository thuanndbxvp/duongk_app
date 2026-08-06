"""
Celery task: materialize_asset — download stock asset → R2.
Phase 02: Idempotent by (source, provider_id, checksum).
"""
import hashlib
from celery import Task
from apps.worker.celery_app import celery_app
from apps.worker.services.asset_providers import (
    PexelsProvider, LocalPlaceholderProvider,
)
from supabase import create_client
import os


PROVIDER_MAP = {
    "pexels": PexelsProvider,
    "local_placeholder": LocalPlaceholderProvider,
}


@celery_app.task(
    name="materialize_asset",
    bind=True,
    max_retries=3,
    acks_late=True,
)
def materialize_asset(self: Task, asset_id: str, provider: str, provider_id: str, owner_id: str = ""):
    """
    Materialize a stock asset from provider into user's library.

    Idempotency: checks if asset with same (source, provider_id) already exists and is 'ready'.
    """
    supabase = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    # Idempotency check
    existing = supabase.table('assets').select('*').eq('source', provider).eq('provider_id', provider_id).maybe_single().execute()
    if existing.data and existing.data.get('status') == 'ready':
        return {"status": "skipped", "asset_id": existing.data['id'], "reason": "already_ready"}

    # Get provider instance
    provider_cls = PROVIDER_MAP.get(provider)
    if not provider_cls:
        raise ValueError(f"Unknown provider: {provider}")

    import asyncio

    async def _materialize():
        inst = provider_cls()
        meta = await inst.materialize(provider_id)

        if existing.data and asset_id:
            # Update existing row
            supabase.table('assets').update({
                'storage_key': meta.storage_key,
                'mime_type': meta.mime_type,
                'size_bytes': meta.size_bytes,
                'width': meta.width,
                'height': meta.height,
                'duration_seconds': meta.duration_seconds,
                'checksum': meta.checksum,
                'license': meta.license,
                'metadata': meta.metadata,
                'status': 'ready',
            }).eq('id', existing.data['id']).execute()
            final_id = existing.data['id']
        else:
            # Create new asset row
            asset_res = supabase.table('assets').insert({
                'owner_id': owner_id or existing.data.get('owner_id', ''),
                'source': meta.source,
                'provider_id': meta.provider_id,
                'storage_key': meta.storage_key,
                'mime_type': meta.mime_type,
                'size_bytes': meta.size_bytes,
                'checksum': meta.checksum,
                'width': meta.width,
                'height': meta.height,
                'duration_seconds': meta.duration_seconds,
                'license': meta.license,
                'metadata': meta.metadata,
                'status': 'ready',
            }).execute()
            final_id = asset_res.data[0]['id'] if asset_res.data else None

        # Create original variant
        if final_id:
            supabase.table('asset_variants').upsert({
                'asset_id': final_id,
                'variant_kind': 'original',
                'storage_key': meta.storage_key,
                'mime_type': meta.mime_type,
                'size_bytes': meta.size_bytes,
                'width': meta.width,
                'height': meta.height,
                'duration_seconds': meta.duration_seconds,
            }, on_conflict='asset_id,variant_kind').execute()

        return {"status": "materialized", "asset_id": final_id}

    return asyncio.run(_materialize())

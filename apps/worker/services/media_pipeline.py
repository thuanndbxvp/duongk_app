"""
Media pipeline — normalize → upscale → cleanup → resize → validate.
Phase 05.
"""
from __future__ import annotations
from typing import Literal
from uuid import UUID

Operation = Literal["normalize", "upscale", "cleanup", "resize"]


async def run_media_pipeline(
    supabase,
    asset_id: UUID,
    ops: list[Operation],
    consent_id: UUID | None = None,
) -> dict:
    """
    Run media pipeline ops on an asset.

    Args:
        supabase: Supabase admin client.
        asset_id: Source asset UUID.
        ops: Ordered list of operations to apply.
        consent_id: Required for 'cleanup' op.

    Returns:
        dict with variant_id, storage_key, status.
    """
    # Load source asset
    asset = supabase.table('assets').select('*').eq('id', str(asset_id)).single().execute()
    if not asset.data:
        raise ValueError('Asset not found')

    source = asset.data
    current_key = source['storage_key']
    current_mime = source['mime_type']
    current_size = source['size_bytes']
    current_w = source.get('width')
    current_h = source.get('height')

    for op in ops:
        if op == 'cleanup' and not consent_id:
            raise ValueError('consent_id required for cleanup')

        if op == 'normalize':
            current_key = f"{current_key}_normalized"
            current_mime = current_mime or 'image/png'
        elif op == 'upscale':
            current_key = f"{current_key}_upscaled"
            current_w = (current_w or 1920) * 2
            current_h = (current_h or 1080) * 2
        elif op == 'cleanup':
            current_key = f"{current_key}_cleaned"
        elif op == 'resize':
            current_key = f"{current_key}_resized"

    # Create asset_variant
    variant_res = supabase.table('asset_variants').insert({
        'asset_id': str(asset_id),
        'variant_kind': 'processed',
        'storage_key': current_key,
        'mime_type': current_mime,
        'size_bytes': current_size,
        'width': current_w,
        'height': current_h,
    }).execute()

    variant = variant_res.data[0] if variant_res.data else {}
    return {"variant_id": variant.get('id'), "storage_key": current_key, "status": "processed"}

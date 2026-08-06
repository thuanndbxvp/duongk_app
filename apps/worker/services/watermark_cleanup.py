"""
Watermark cleanup service — consent gate + provenance.
Phase 05: Preview BEFORE commit, never mutate source.
"""
from __future__ import annotations
from uuid import UUID


async def create_cleanup_preview(supabase, asset_id: UUID, user_id: str) -> dict:
    """Create a preview of watermark detection (no inpainting)."""
    # Verify asset ownership
    asset = supabase.table('assets').select('*').eq('id', str(asset_id)).eq('owner_id', user_id).single().execute()
    if not asset.data:
        raise PermissionError('Asset not found or not owned')

    # Create consent record
    consent_res = supabase.table('consent_records').upsert({
        'user_id': user_id,
        'asset_id': str(asset_id),
        'consent_type': 'watermark_cleanup',
        'status': 'pending',
    }, on_conflict='user_id,asset_id,consent_type').execute()

    consent = consent_res.data[0] if consent_res.data else {}

    # Create preview variant (no actual mutation)
    preview_variant = supabase.table('asset_variants').insert({
        'asset_id': str(asset_id),
        'variant_kind': 'preview',
        'storage_key': asset.data['storage_key'] + '_cleanup_preview',
        'mime_type': asset.data['mime_type'],
        'size_bytes': asset.data['size_bytes'],
        'width': asset.data.get('width'),
        'height': asset.data.get('height'),
    }).execute()

    variant = preview_variant.data[0] if preview_variant.data else {}
    return {
        "preview_asset_id": variant.get('id'),
        "consent_id": consent.get('id', ''),
        "status": "preview_ready",
    }


async def approve_cleanup(supabase, consent_id: UUID, user_id: str) -> dict:
    """User approves cleanup → create cleaned variant."""
    # Verify consent
    consent = supabase.table('consent_records').select('*').eq('id', str(consent_id)).eq('user_id', user_id).single().execute()
    if not consent.data:
        raise PermissionError('Consent not found')
    if consent.data['status'] != 'pending':
        raise ValueError('Consent already processed')

    # Approve consent
    from datetime import datetime, timezone
    supabase.table('consent_records').update({
        'status': 'approved',
        'approved_at': datetime.now(timezone.utc).isoformat(),
    }).eq('id', str(consent_id)).execute()

    # Create cleaned variant
    asset = supabase.table('assets').select('*').eq('id', consent.data['asset_id']).single().execute()

    cleaned = supabase.table('asset_variants').insert({
        'asset_id': consent.data['asset_id'],
        'variant_kind': 'processed',
        'storage_key': asset.data['storage_key'] + '_cleaned',
        'mime_type': asset.data['mime_type'],
        'size_bytes': asset.data['size_bytes'],
        'width': asset.data.get('width'),
        'height': asset.data.get('height'),
    }).execute()

    variant = cleaned.data[0] if cleaned.data else {}
    return {"variant_id": variant.get('id'), "consent_id": str(consent_id), "status": "cleaned"}

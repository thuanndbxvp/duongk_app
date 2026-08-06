"""
Character lab service — generate candidates, bind scenes, coverage check.
Phase 11: Coverage gate blocks batch when scenes lack anchors.
"""
from __future__ import annotations
from uuid import UUID


async def generate_character_candidates(
    supabase,
    lab_run_id: UUID,
    character_names: list[str],
    provider: str = "gemini",
) -> list[dict]:
    """Generate character anchor candidates."""
    candidates = []
    for name in character_names[:10]:  # Cap at 10
        import hashlib
        cid = f"char-{lab_run_id}-{name}"
        checksum = hashlib.sha256(cid.encode()).hexdigest()

        asset_res = supabase.table('assets').insert({
            'owner_id': 'system',
            'source': provider,
            'provider_id': cid,
            'storage_key': f"lab/characters/{name}.png",
            'mime_type': 'image/png',
            'size_bytes': 102400,
            'checksum': checksum,
            'status': 'ready',
            'license': {'provider': provider},
        }).execute()

        asset_id = asset_res.data[0]['id'] if asset_res.data else None

        anchor_res = supabase.table('character_anchors').upsert({
            'lab_run_id': str(lab_run_id),
            'character_name': name,
            'asset_id': asset_id,
            'provider': provider,
            'anchor_strength': 0.7,
            'metadata': {'generated_by': provider},
        }, on_conflict='lab_run_id,character_name').execute()

        candidates.append(anchor_res.data[0] if anchor_res.data else {})

    return candidates


async def coverage_check(supabase, project_id: UUID) -> dict:
    """Check if all scenes have character + background anchors."""
    scenes = supabase.table('project_scenes').select('id, characters').eq('project_id', str(project_id)).execute()
    if not scenes.data:
        return {"total_scenes": 0, "scenes_with_character": 0, "scenes_with_background": 0, "coverage_pct": 0, "missing_scenes": []}

    total = len(scenes.data)
    missing = []
    with_char = 0
    with_bg = 0

    for scene in scenes.data:
        binding = supabase.table('scene_anchor_bindings').select('*').eq('scene_id', scene['id']).maybe_single().execute()
        if binding.data:
            if binding.data.get('character_anchor_id'):
                with_char += 1
            if binding.data.get('background_anchor_id'):
                with_bg += 1
        if not binding.data or not binding.data.get('character_anchor_id'):
            missing.append(UUID(scene['id']))

    coverage = max(with_char / total, 0) if total > 0 else 0
    return {
        "total_scenes": total,
        "scenes_with_character": with_char,
        "scenes_with_background": with_bg,
        "coverage_pct": round(coverage, 2),
        "missing_scenes": missing,
    }

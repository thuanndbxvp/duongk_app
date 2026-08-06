"""
Timeline compiler — build versioned timeline JSON from scenes + voice_lines + assets.
Phase 03.
"""


async def compile_timeline_model(supabase, project_id: str) -> dict:
    """
    Compile timeline model v1 from project data.

    Returns versioned JSON with clips, transitions, audio_tracks, subtitle_track, output config.
    """
    # Get project for output config
    proj = supabase.table('projects').select('id').eq('id', project_id).single().execute()
    briefs = supabase.table('project_briefs').select('*').eq('project_id', project_id).order('version', desc=True).limit(1).execute()
    brief = briefs.data[0] if briefs.data else {}

    aspect = brief.get('aspect_ratio', '9:16')
    is_vertical = aspect == '9:16'
    output_width = 1080
    output_height = 1920 if is_vertical else 1080
    safe_area = "1080x1920_20pct" if is_vertical else "1920x1080_10pct"

    # Get scenes with voice_lines and assets
    scenes_res = supabase.table('project_scenes').select('*').eq('project_id', project_id).order('scene_index').execute()
    scenes = scenes_res.data or []

    clips = []
    audio_tracks = []
    cursor = 0.0

    for scene in scenes:
        # Voice line
        vl_res = supabase.table('voice_lines').select('*').eq('scene_id', scene['id']).order('voice_version', desc=True).limit(1).execute()
        voice_line = vl_res.data[0] if vl_res.data else None

        duration = float(voice_line.get('duration_seconds') or scene.get('estimated_duration') or 5)

        # Scene assets
        sa_res = supabase.table('scene_assets').select('asset_id').eq('scene_id', scene['id']).execute()
        asset_id = sa_res.data[0]['asset_id'] if sa_res.data else None

        clip = {
            "scene_id": scene.get('scene_id', ''),
            "scene_index": scene.get('scene_index', 0),
            "asset_id": str(asset_id) if asset_id else None,
            "start": round(cursor, 3),
            "duration": round(duration, 3),
            "fit_mode": "cover",
            "motion": "ken_burns_zoom_in",
            "transition_in": "fade" if cursor == 0 else "dissolve",
            "transition_out": "dissolve",
        }
        clips.append(clip)

        if voice_line and voice_line.get('storage_key'):
            audio_tracks.append({
                "kind": "voice",
                "track_id": voice_line.get('storage_key', ''),
                "start": round(cursor, 3),
                "duration": round(duration, 3),
            })

        cursor += duration

    # Subtitle track reference
    st_res = supabase.table('subtitle_tracks').select('*').eq('project_id', project_id).order('version', desc=True).limit(1).execute()
    subtitle_track = {
        "source": "srt",
        "style": "default",
        "safe_area": safe_area,
        "track_id": st_res.data[0]['storage_key'] if st_res.data else None,
    }

    # Music track placeholder
    audio_tracks.append({
        "kind": "music",
        "track_id": None,
        "start": 0,
        "duration": round(cursor, 3),
    })

    # Transitions between clips
    transitions = []
    for i in range(1, len(clips)):
        transitions.append({
            "from_clip": i - 1,
            "to_clip": i,
            "type": "dissolve",
            "duration": 0.5,
        })

    return {
        "schema_version": 1,
        "total_duration": round(cursor, 3),
        "clips": clips,
        "transitions": transitions,
        "audio_tracks": audio_tracks,
        "subtitle_track": subtitle_track,
        "output": {
            "width": output_width,
            "height": output_height,
            "fps": 30,
            "codec": "h264",
            "quality": "high",
        },
    }

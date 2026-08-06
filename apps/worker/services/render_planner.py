"""
RenderPlanner — compile timeline model into FFmpeg command-line arguments.
Phase 04: Draft = 720p fast, Final = 1080p slow.
"""
from __future__ import annotations


def compile_ffmpeg_args(timeline_model: dict, kind: str, output_path: str) -> list[str]:
    """
    Build FFmpeg argv[] from timeline model.

    Args:
        timeline_model: Versioned timeline JSON from Phase 03.
        kind: 'draft' (720p fast) or 'final' (1080p slow).
        output_path: Output file path.

    Returns:
        FFmpeg command argument list (excluding 'ffmpeg').
    """
    output = timeline_model.get('output', {})
    is_draft = kind == 'draft'

    width = output.get('width', 1080)
    height = output.get('height', 1920)

    if is_draft:
        # Scale down to 720p equivalent
        scale_factor = 720 / max(width, height)
        width = int(width * scale_factor)
        height = int(height * scale_factor)
        # Make even
        width = width - (width % 2)
        height = height - (height % 2)
        preset = 'veryfast'
        crf = 28
    else:
        preset = 'slow'
        crf = 18

    fps = output.get('fps', 30)
    codec = output.get('codec', 'h264')

    args = ['-y']

    # Input: each clip = image, duration
    clips = timeline_model.get('clips', [])
    filter_parts = []
    concat_inputs = []

    for i, clip in enumerate(clips):
        duration = clip.get('duration', 5)
        # Use color source as placeholder if no asset
        args.extend(['-f', 'lavfi', '-i', f'color=c=black:s={width}x{height}:d={duration}:r={fps}'])
        concat_inputs.append(f'[{i}:v]')
        filter_parts.append(f'[{i}:v]trim=duration={duration},setpts=PTS-STARTPTS[v{i}]')

    # Audio: combine voice tracks with silence for missing
    audio_tracks = timeline_model.get('audio_tracks', [])
    audio_inputs = []
    audio_filter = []
    audio_offset = len(clips)

    for j, track in enumerate(audio_tracks):
        if track.get('kind') == 'voice' and track.get('track_id'):
            dur = track.get('duration', 5)
            args.extend(['-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=mono:d={dur}'])
            audio_inputs.append(f'[{audio_offset + j}:a]')
            audio_filter.append(f'[{audio_offset + j}:a]atrim=duration={dur}[a{j}]')

    # Concat video
    if len(filter_parts) > 1:
        vstack = ''.join(f'[v{i}]' for i in range(len(clips)))
        filter_parts.append(f'{vstack}concat=n={len(clips)}:v=1:a=0[outv]')
    else:
        filter_parts.append(f'[v0]copy[outv]')

    filter_str = ';'.join(filter_parts)

    # Codec settings
    args.extend([
        '-filter_complex', filter_str,
        '-map', '[outv]',
        '-c:v', 'libx264' if codec == 'h264' else codec,
        '-preset', preset,
        '-crf', str(crf),
        '-pix_fmt', 'yuv420p',
        '-r', str(fps),
    ])

    # Audio output
    if audio_inputs and audio_filter:
        astr = ';'.join(audio_filter)
        args.extend(['-filter_complex:a', astr])
        for k in range(len(audio_tracks)):
            args.extend(['-map', f'[a{k}]'])
        args.extend(['-c:a', 'aac', '-b:a', '128k'])
    else:
        args.extend(['-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=mono:d={sum(c.get("duration", 5) for c in clips)}'])
        args.extend(['-map', f'{audio_offset}:a', '-c:a', 'aac', '-b:a', '128k', '-shortest'])

    args.append(output_path)
    return args

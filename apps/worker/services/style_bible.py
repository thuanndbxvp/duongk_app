"""
Style Bible service — build_prompt + merge + fingerprint.
Phase 09: Merge bible + scene contract → final prompt.
"""
from __future__ import annotations
import hashlib
import json


VALID_LENS = {"24mm", "35mm", "50mm", "85mm", "135mm", "200mm"}
VALID_MOTIONS = {"ken_burns_zoom_in", "ken_burns_zoom_out", "pan_left", "pan_right", "tilt_up", "tilt_down", "static", "dolly_zoom", "tracking"}
PALETTE_HEX_RE = __import__('re').compile(r'^#[0-9a-fA-F]{6}$')


def validate_palette(palette: dict) -> list[str]:
    """Validate palette colors are valid hex."""
    errors = []
    for key, val in palette.items():
        if isinstance(val, str) and not PALETTE_HEX_RE.match(val):
            errors.append(f"Invalid hex color for '{key}': {val}")
    return errors


def validate_lens(lens: str) -> bool:
    return lens in VALID_LENS if lens else True


def validate_motion(motion: str) -> bool:
    return motion in VALID_MOTIONS if motion else True


def build_prompt(
    bible: dict,
    scene_contract: dict,
    channel_forbidden_claims: list[str] | None = None,
) -> tuple[str, str, str]:
    """
    Merge style bible + scene contract into final prompt.

    Returns:
        (merged_prompt, merged_negative, fingerprint)
    """
    palette = bible.get('visual_palette', {})
    lens = bible.get('lens_preference', '')
    motion = bible.get('motion_style', '')
    negative = bible.get('negative_prompt', '')

    # Build positive prompt
    parts = []

    # Visual description from scene
    vis = scene_contract.get('visual_description', '')
    if vis:
        parts.append(vis)

    # Image prompt from scene
    img = scene_contract.get('image_prompt', '')
    if img:
        parts.append(img)

    # Palette colors
    if palette:
        colors = ', '.join(f"{k}:{v}" for k, v in palette.items())
        parts.append(f"Color palette: {colors}")

    # Lens
    if lens and validate_lens(lens):
        parts.append(f"Shot with {lens} lens")

    # Motion
    if motion and validate_motion(motion):
        parts.append(f"Motion: {motion}")

    # Character refs
    characters = scene_contract.get('characters', [])
    if characters:
        parts.append(f"Characters: {', '.join(characters)}")

    # Background
    bg = scene_contract.get('background', '')
    if bg:
        parts.append(f"Background: {bg}")

    merged_prompt = ', '.join(parts) if parts else scene_contract.get('narration', '')

    # Build negative prompt
    merged_negative = negative

    # Append channel forbidden claims
    if channel_forbidden_claims:
        forbidden = ', '.join(channel_forbidden_claims)
        if merged_negative:
            merged_negative += f", {forbidden}"
        else:
            merged_negative = forbidden

    # Standard negatives
    std_negatives = "low quality, blurry, distorted, watermark, text, logo"
    if merged_negative:
        merged_negative += f", {std_negatives}"
    else:
        merged_negative = std_negatives

    # Fingerprint
    fp = hashlib.sha256(
        json.dumps({
            'bible_id': bible.get('id', ''),
            'bible_version': bible.get('version', 1),
            'scene_id': scene_contract.get('scene_id', ''),
            'prompt': merged_prompt,
            'negative': merged_negative,
        }, sort_keys=True).encode()
    ).hexdigest()

    return merged_prompt, merged_negative, fp

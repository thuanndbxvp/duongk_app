"""
Cost estimator — pricing table versioned.
Phase 10: Estimate batch cost before running.
"""
from __future__ import annotations

PRICING_TABLE = {
    "script_generation": 30,
    "scene_breakdown": 10,
    "tts_scene": 5,
    "render_draft": 20,
    "render_final": 50,
    "thumbnail_generation": 15,
    "metadata_package": 5,
}


def estimate_cost(task_type: str, item_count: int = 1) -> dict:
    """Estimate cost for a task type × count."""
    per_item = PRICING_TABLE.get(task_type, 10)
    total = per_item * item_count
    return {
        "total": total,
        "per_item": per_item,
        "item_count": item_count,
        "model_version": "v1",
    }


def cap_estimate(estimate: int, last_actual: int | None = None) -> int:
    """Cap estimate at max(estimate, last_actual * 1.2)."""
    if last_actual is None:
        return estimate
    cap = max(estimate, int(last_actual * 1.2))
    return cap

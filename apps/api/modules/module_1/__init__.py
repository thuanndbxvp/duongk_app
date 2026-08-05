"""
Module 1: Niche Validation (Discovery).

Provides:
- NicheValidator service
- Formula A0 (Video Filter)
- Formula A2 (Viral Detection)
"""
from apps.api.modules.module_1.service import NicheValidator
from apps.api.modules.module_1.formulas import filter_quality_videos, detect_viral_videos
from apps.api.modules.module_1.routes import router

__all__ = [
    "NicheValidator",
    "filter_quality_videos",
    "detect_viral_videos",
    "router"
]

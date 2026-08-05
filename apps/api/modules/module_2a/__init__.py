"""
Module 2A: Deep Collection.

Collects YouTube video metadata and applies filtering formulas.
"""
from apps.api.modules.module_2a.service import YouTubeCollector
from apps.api.modules.module_2a.routes import router

__all__ = ["YouTubeCollector", "router"]

"""
Provider health service — Phase 10.
"""
from __future__ import annotations
from dataclasses import dataclass
import time


@dataclass
class ProviderHealth:
    provider: str
    is_healthy: bool = True
    quota_remaining: int | None = None
    latency_ms: int | None = None


# In-memory health registry
_health_registry: dict[str, ProviderHealth] = {}


def update_health(provider: str, healthy: bool, quota: int | None = None):
    _health_registry[provider] = ProviderHealth(
        provider=provider,
        is_healthy=healthy,
        quota_remaining=quota,
        latency_ms=int(time.time() * 1000) % 500,
    )


def is_healthy(provider: str) -> bool:
    h = _health_registry.get(provider)
    return h.is_healthy if h else True  # Default: assume healthy


def has_quota(provider: str, needed: int = 1) -> bool:
    h = _health_registry.get(provider)
    if h is None or h.quota_remaining is None:
        return True
    return h.quota_remaining >= needed


def mark_exhausted(provider: str):
    _health_registry[provider] = ProviderHealth(provider=provider, is_healthy=False, quota_remaining=0)

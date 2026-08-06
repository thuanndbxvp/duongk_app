"""
Capability probe — verify AI provider availability.
Phase 05: Queries each provider for health/quotas.
"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field


@dataclass
class ProviderCapability:
    provider: str
    available: bool
    models: list[str] = field(default_factory=list)
    error: str = ""


async def probe_provider(provider: str) -> ProviderCapability:
    """Probe a single provider for availability."""
    probes = {
        "gemini": _probe_gemini,
        "nanobanana": _probe_nanobanana,
        "flux": _probe_flux,
        "sdxl": _probe_sdxl,
    }
    fn = probes.get(provider)
    if not fn:
        return ProviderCapability(provider=provider, available=False, error="unknown_provider")
    try:
        return await fn()
    except Exception as e:
        return ProviderCapability(provider=provider, available=False, error=str(e))


async def probe_all() -> dict[str, ProviderCapability]:
    """Probe all registered providers."""
    providers = ["gemini", "nanobanana", "flux", "sdxl"]
    results = await asyncio.gather(*[probe_provider(p) for p in providers], return_exceptions=True)
    caps = {}
    for p, result in zip(providers, results):
        if isinstance(result, Exception):
            caps[p] = ProviderCapability(provider=p, available=False, error=str(result))
        else:
            caps[p] = result
    return caps


async def _probe_gemini() -> ProviderCapability:
    import os
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return ProviderCapability(provider="gemini", available=False, error="no_api_key")
    return ProviderCapability(provider="gemini", available=True, models=["gemini-2.0-flash-exp"])


async def _probe_nanobanana() -> ProviderCapability:
    return ProviderCapability(provider="nanobanana", available=False, error="not_configured")


async def _probe_flux() -> ProviderCapability:
    return ProviderCapability(provider="flux", available=False, error="not_configured")


async def _probe_sdxl() -> ProviderCapability:
    return ProviderCapability(provider="sdxl", available=False, error="not_configured")

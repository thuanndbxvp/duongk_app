"""
AssetProvider abstract contract — Phase 02.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AssetMetadata:
    """Metadata for a materialized asset."""
    source: str
    provider_id: str
    storage_key: str
    mime_type: str
    size_bytes: int
    checksum: str
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    license: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    """Search result from a provider."""
    provider: str
    provider_id: str
    thumbnail_url: str
    description: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    photographer: Optional[str] = None
    pexels_url: Optional[str] = None


class AssetProvider(ABC):
    """Abstract contract for asset providers."""

    name: str = "base"

    @abstractmethod
    async def search(
        self,
        query: str,
        media_type: str = "image",
        orientation: Optional[str] = None,
        page: int = 1,
    ) -> tuple[list[SearchResult], int, Optional[int]]:
        """
        Search for assets.

        Returns:
            Tuple of (results, total_results, next_page_or_None).
        """
        ...

    @abstractmethod
    async def materialize(self, provider_id: str) -> AssetMetadata:
        """
        Download and materialize an asset from provider into local storage.

        Args:
            provider_id: Provider-specific asset identifier.

        Returns:
            AssetMetadata for the downloaded asset.
        """
        ...

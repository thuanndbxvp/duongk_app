# Package: asset_providers
# NOTE: Cleaned up - removed orphaned providers (pexels, local_placeholder, upload, ai_providers)
from apps.worker.services.asset_providers.base import AssetProvider, AssetMetadata, SearchResult

# NOTE: PROVIDER_REGISTRY now empty - re-add as needed when new providers are implemented
PROVIDER_REGISTRY: dict[str, type[AssetProvider]] = {}

__all__ = [
    "AssetProvider", "AssetMetadata", "SearchResult",
    "PROVIDER_REGISTRY",
]

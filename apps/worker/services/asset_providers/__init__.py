# Package: asset_providers
from apps.worker.services.asset_providers.base import AssetProvider, AssetMetadata, SearchResult
from apps.worker.services.asset_providers.upload import UploadProvider
from apps.worker.services.asset_providers.pexels import PexelsProvider
from apps.worker.services.asset_providers.local_placeholder import LocalPlaceholderProvider

PROVIDER_REGISTRY: dict[str, type[AssetProvider]] = {
    "upload": UploadProvider,
    "pexels": PexelsProvider,
    "local_placeholder": LocalPlaceholderProvider,
}

__all__ = [
    "AssetProvider", "AssetMetadata", "SearchResult",
    "UploadProvider", "PexelsProvider", "LocalPlaceholderProvider",
    "PROVIDER_REGISTRY",
]

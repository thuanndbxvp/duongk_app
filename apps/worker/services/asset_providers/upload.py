"""
UploadProvider — handles user-uploaded assets.
"""
from .base import AssetProvider, AssetMetadata, SearchResult


class UploadProvider(AssetProvider):
    name = "upload"

    async def search(self, *args, **kwargs):
        return [], 0, None

    async def materialize(self, provider_id: str) -> AssetMetadata:
        raise NotImplementedError("upload provider does not need materialize")

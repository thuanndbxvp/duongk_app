"""
LocalPlaceholderProvider — generates simple placeholder assets for test/dev.
"""
from .base import AssetProvider, AssetMetadata, SearchResult


class LocalPlaceholderProvider(AssetProvider):
    name = "local_placeholder"

    async def search(
        self,
        query: str,
        media_type: str = "image",
        orientation: str = None,
        page: int = 1,
    ):
        """Return simple placeholder results for testing."""
        results = []
        for i in range(5):
            results.append(SearchResult(
                provider=self.name,
                provider_id=f"placeholder-{i+1}",
                thumbnail_url="",
                description=f"Placeholder for: {query}",
            ))
        return results, 5, None

    async def materialize(self, provider_id: str) -> AssetMetadata:
        """Generate a tiny placeholder SVG."""
        import hashlib
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360"><rect width="640" height="360" fill="#333"/><text x="50%" y="50%" fill="#fff" text-anchor="middle" dominant-baseline="middle" font-size="24">{provider_id}</text></svg>'
        data = svg.encode()
        checksum = hashlib.sha256(data).hexdigest()

        return AssetMetadata(
            source=self.name,
            provider_id=provider_id,
            storage_key=f"placeholders/{provider_id}.svg",
            mime_type="image/svg+xml",
            size_bytes=len(data),
            checksum=checksum,
            width=640,
            height=360,
        )

"""
PexelsProvider — search and materialize assets from Pexels API.
"""
import os
import hashlib
import httpx
from .base import AssetProvider, AssetMetadata, SearchResult


class PexelsProvider(AssetProvider):
    name = "pexels"
    BASE = "https://api.pexels.com"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("PEXELS_API_KEY", "")

    def _headers(self) -> dict:
        return {"Authorization": self.api_key}

    async def search(
        self,
        query: str,
        media_type: str = "image",
        orientation: str = None,
        page: int = 1,
    ):
        """Search Pexels API."""
        endpoint = "/v1/search" if media_type == "image" else "/videos/search"
        params = {"query": query, "per_page": 20, "page": page}
        if orientation:
            params["orientation"] = orientation

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{self.BASE}{endpoint}",
                headers=self._headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        items = data.get("photos") or data.get("videos") or []
        for item in items:
            r = SearchResult(
                provider=self.name,
                provider_id=str(item["id"]),
                thumbnail_url=item.get("src", {}).get("medium", item.get("image", "")),
                description=item.get("alt", ""),
                width=item.get("width"),
                height=item.get("height"),
                duration_seconds=item.get("duration"),
                photographer=item.get("photographer"),
                pexels_url=item.get("url"),
            )
            results.append(r)

        total = data.get("total_results", 0)
        next_page = page + 1 if data.get("next_page") else None
        return results, total, next_page

    async def materialize(self, provider_id: str) -> AssetMetadata:
        """Download asset from Pexels and prepare metadata."""
        # Get asset info from Pexels
        async with httpx.AsyncClient(timeout=30) as client:
            # Try photo endpoint first
            resp = await client.get(
                f"{self.BASE}/v1/photos/{provider_id}",
                headers=self._headers(),
            )
            if resp.status_code == 404:
                # Try video endpoint
                resp = await client.get(
                    f"{self.BASE}/videos/videos/{provider_id}",
                    headers=self._headers(),
                )
            resp.raise_for_status()
            data = resp.json()

        # Determine download URL
        if "src" in data:
            download_url = data["src"].get("original") or data["src"].get("large2x") or data["src"].get("large")
            mime_type = "image/jpeg"
            width = data.get("width")
            height = data.get("height")
            duration = None
        else:
            video_files = data.get("video_files", [])
            best = video_files[0] if video_files else {}
            download_url = best.get("link", "")
            mime_type = "video/mp4"
            width = best.get("width")
            height = best.get("height")
            duration = data.get("duration")

        # Download file
        async with httpx.AsyncClient(timeout=120) as client:
            dl_resp = await client.get(download_url)
            dl_resp.raise_for_status()
            file_data = dl_resp.content

        checksum = hashlib.sha256(file_data).hexdigest()
        ext = "jpg" if mime_type.startswith("image/") else "mp4"
        storage_key = f"pexels/{provider_id}.{ext}"

        license_info = {
            "photographer": data.get("photographer", ""),
            "photographer_url": data.get("photographer_url", ""),
            "pexels_id": str(data.get("id", provider_id)),
            "url": data.get("url", ""),
        }

        return AssetMetadata(
            source=self.name,
            provider_id=str(provider_id),
            storage_key=storage_key,
            mime_type=mime_type,
            size_bytes=len(file_data),
            checksum=checksum,
            width=width,
            height=height,
            duration_seconds=duration,
            license=license_info,
        )

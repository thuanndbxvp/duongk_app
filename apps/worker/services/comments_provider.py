"""
Comments provider abstraction — Phase 06.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CommentRow:
    """Normalized comment row."""
    comment_id: str
    video_id: str
    author_display_name: str
    text: str
    like_count: int = 0
    reply_count: int = 0
    published_at: str = ""


class CommentsProvider(ABC):
    """Abstract contract for fetching comments."""

    @abstractmethod
    async def fetch(self, video_ids: list[str], page_token: str | None = None) -> tuple[list[CommentRow], str | None]:
        """
        Fetch comments for given video IDs.

        Returns:
            Tuple of (comments, next_page_token).
        """
        ...


class YouTubeDataAPIProvider(CommentsProvider):
    """YouTube Data API v3 provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def fetch(self, video_ids: list[str], page_token: str | None = None) -> tuple[list[CommentRow], str | None]:
        """Fetch comments via YouTube Data API v3."""
        import os
        if not self.api_key or self.api_key.startswith('xxx'):
            # Dev/mock mode
            return self._mock_fetch(video_ids)

        import httpx
        comments = []
        for vid in video_ids[:10]:  # Rate limit guard
            params = {
                'part': 'snippet',
                'videoId': vid,
                'maxResults': 50,
                'key': self.api_key,
            }
            if page_token:
                params['pageToken'] = page_token

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    'https://www.googleapis.com/youtube/v3/commentThreads',
                    params=params,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get('items', []):
                        snippet = item.get('snippet', {}).get('topLevelComment', {}).get('snippet', {})
                        comments.append(CommentRow(
                            comment_id=item.get('id', ''),
                            video_id=vid,
                            author_display_name=snippet.get('authorDisplayName', ''),
                            text=snippet.get('textDisplay', ''),
                            like_count=snippet.get('likeCount', 0),
                            published_at=snippet.get('publishedAt', ''),
                        ))
                    page_token = data.get('nextPageToken')
                else:
                    page_token = None
        return comments, page_token

    def _mock_fetch(self, video_ids: list[str]) -> tuple[list[CommentRow], None]:
        """Mock comments for dev/testing."""
        comments = []
        for i, vid in enumerate(video_ids):
            for j in range(5):
                comments.append(CommentRow(
                    comment_id=f"mock-{vid}-{j}",
                    video_id=vid,
                    author_display_name=f"User{j}",
                    text=f"Mock comment {j} for video {vid}. Great content!",
                    like_count=j * 2,
                ))
        return comments, None

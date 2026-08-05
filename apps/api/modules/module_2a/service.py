"""
Module 2A - YouTubeCollector Service.
Collects video metadata from YouTube channels.
"""
import os
import asyncio
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from apps.api.modules.module_1.formulas import filter_quality_videos, detect_viral_videos


class YouTubeCollector:
    """Service for collecting YouTube video metadata."""
    
    BATCH_SIZE = 50  # YouTube API max videos per request
    MAX_VIDEOS = 200  # Max videos per channel
    MAX_CONCURRENT = 4  # Max concurrent API calls
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("YOUTUBE_API_KEY_1")
        self._client = None
    
    async def get_client(self):
        """Lazy initialization of YouTube client."""
        if self._client is None:
            self._client = build('youtube', 'v3', developerKey=self.api_key)
        return self._client
    
    async def collect_channel_videos(
        self,
        channel_id: str,
        max_videos: int = MAX_VIDEOS
    ) -> Dict[str, Any]:
        """
        Collect videos from a YouTube channel.
        
        Args:
            channel_id: YouTube channel ID
            max_videos: Maximum number of videos to collect
        
        Returns:
            Dict with all_videos, quality_videos, viral_videos
        """
        # Step 1: Get video IDs
        video_ids = await self._get_channel_video_ids(channel_id, max_videos)
        
        # Step 2: Batch into groups of 50
        batches = [
            video_ids[i:i + self.BATCH_SIZE]
            for i in range(0, len(video_ids), self.BATCH_SIZE)
        ]
        
        # Step 3: Fetch metadata in parallel (max 4 concurrent)
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
        
        async def fetch_batch(batch_ids: List[str]) -> List[Dict[str, Any]]:
            async with semaphore:
                return await self._fetch_video_metadata(batch_ids)
        
        results = await asyncio.gather(*[fetch_batch(b) for b in batches])
        
        # Flatten results
        all_videos = [v for batch in results for v in batch]
        
        # Step 4: Apply Formula A0 - Filter quality videos
        quality_videos = filter_quality_videos(all_videos)
        
        # Step 5: Apply Formula A2 - Detect viral videos
        viral_videos = detect_viral_videos(quality_videos)
        
        return {
            "channel_id": channel_id,
            "total_videos_collected": len(all_videos),
            "quality_videos_count": len(quality_videos),
            "viral_videos_count": len(viral_videos),
            "all_videos": all_videos,
            "quality_videos": quality_videos,
            "viral_videos": viral_videos
        }
    
    async def _get_channel_video_ids(
        self,
        channel_id: str,
        max_videos: int
    ) -> List[str]:
        """Get video IDs from a channel using search."""
        client = await self.get_client()
        video_ids = []
        next_page_token = None
        
        while len(video_ids) < max_videos:
            remaining = max_videos - len(video_ids)
            
            try:
                # Use search to get videos (sorted by date)
                response = await asyncio.to_thread(
                    client.search().list(
                        part='id',
                        channelId=channel_id,
                        type='video',
                        order='date',
                        maxResults=min(50, remaining),
                        pageToken=next_page_token
                    ).execute
                )
                
                for item in response.get('items', []):
                    if item['id']['kind'] == 'youtube#video':
                        video_ids.append(item['id']['videoId'])
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except HttpError as e:
                print(f"YouTube API error: {e}")
                break
            except Exception as e:
                print(f"Error getting video IDs: {e}")
                break
        
        return video_ids
    
    async def _fetch_video_metadata(
        self,
        video_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Fetch metadata for a batch of videos."""
        client = await self.get_client()
        
        try:
            response = await asyncio.to_thread(
                client.videos().list(
                    part='snippet,contentDetails,statistics',
                    id=','.join(video_ids)
                ).execute
            )
            
            return response.get('items', [])
            
        except HttpError as e:
            print(f"YouTube API error: {e}")
            return []
        except Exception as e:
            print(f"Error fetching metadata: {e}")
            return []

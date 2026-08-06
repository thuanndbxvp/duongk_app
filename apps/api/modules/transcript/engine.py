"""
Transcript Engine - 3-Tier Fallback Strategy.

Tier 1: youtube-transcript-api (FREE)
Tier 2: Supadata API ($0.001/min)
Tier 3: OpenAI Whisper API ($0.006/min)
"""
import os
import io
from enum import Enum
from typing import Optional, List, Dict, Any
import httpx
import openai
from apps.api.services.routing import get_routing_config
class TranscriptTier(Enum):
    YOUTUBE_API = 1      # youtube-transcript-api (FREE)
    SUPADATA = 2         # Supadata API ($0.001/min)
    OPENAI_WHISPER = 3   # OpenAI Whisper API ($0.006/min)


class TranscriptEngine:
    """
    3-tier fallback transcript retrieval.

    Tier 1: youtube-transcript-api (fastest, free)
    Tier 2: Supadata API ($0.001/min)
    Tier 3: OpenAI Whisper API ($0.006/min)
    """

    def __init__(
        self,
        supadata_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        self.supadata_key = supadata_api_key or os.environ.get("SUPADATA_API_KEY")
        self.openai_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self._openai_client = None

    async def get_transcript(
        self,
        video_id: str,
        preferred_languages: List[str] = ['vi', 'en']
    ) -> Optional[Dict[str, Any]]:
        """
        Get transcript with 3-tier fallback.
        """
        # Tier 1: youtube-transcript-api (FREE)
        try:
            result = await self._fetch_youtube_api(video_id, preferred_languages)
            if result:
                return {**result, "tier_used": 1, "estimated_cost_usd": 0.0}
        except Exception as e:
            print(f"Tier 1 (YouTube API) failed: {e}")

        # Tier 2: Supadata API ($0.001/min)
        try:
            result = await self._fetch_supadata(video_id, preferred_languages)
            if result:
                return {**result, "tier_used": 2, "estimated_cost_usd": 0.01}
        except Exception as e:
            print(f"Tier 2 (Supadata) failed: {e}")

        # Tier 3: OpenAI Whisper API ($0.006/min)
        try:
            result = await self._fetch_openai_whisper(video_id)
            if result:
                return {**result, "tier_used": 3, "estimated_cost_usd": 0.06}
        except Exception as e:
            print(f"Tier 3 (OpenAI Whisper) failed: {e}")

        return None

    async def _fetch_youtube_api(
        self,
        video_id: str,
        languages: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Tier 1: Use youtube-transcript-api (FREE)."""
        from youtube_transcript_api import YouTubeTranscriptApi

        for lang in languages:
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list.find_transcript([lang])
                content = ' '.join([t['text'] for t in transcript.fetch()])
                return {"video_id": video_id, "transcript": content, "language": lang}
            except Exception:
                continue

        return None

    async def _fetch_supadata(
        self,
        video_id: str,
        languages: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Tier 2: Use Supadata API ($0.001/min)."""
        if not self.supadata_key:
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            for lang in languages:
                try:
                    response = await client.get(
                        "https://api.supadata.ai/v1/youtube/transcript",
                        params={"videoId": video_id, "lang": lang},
                        headers={"Authorization": f"Bearer {self.supadata_key}"}
                    )

                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "video_id": video_id,
                            "transcript": data.get('text', ''),
                            "language": lang
                        }
                except Exception:
                    continue

        return None

    async def _fetch_openai_whisper(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Tier 3: Use OpenAI Whisper API ($0.006/min).

        KHÔNG cần chạy Whisper local!
        Chỉ cần gọi OpenAI API.
        """
        if not self.openai_key:
            return None

        # Get audio bytes from YouTube
        audio_bytes = await self._get_audio_bytes(video_id)
        if not audio_bytes:
            return None

        # Initialize OpenAI client
        if self._openai_client is None:
            self._openai_client = openai.AsyncOpenAI(api_key=self.openai_key)

        # Create file-like object
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = f"{video_id}.mp3"

        try:
            response = await self._openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )

            return {
                "video_id": video_id,
                "transcript": response.text,
                "language": "auto"
            }
        except Exception as e:
            print(f"OpenAI Whisper API error: {e}")
            return None

    async def _get_audio_bytes(self, video_id: str) -> Optional[bytes]:
        """
        Get audio from YouTube as bytes.
        """
        from pytube import YouTube

        try:
            yt = YouTube(f"https://youtube.com/watch?v={video_id}")
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').last()

            buffer = io.BytesIO()
            audio_stream.stream_to_buffer(buffer)
            buffer.seek(0)

            return buffer.getvalue()
        except Exception as e:
            print(f"Error fetching audio: {e}")
            return None

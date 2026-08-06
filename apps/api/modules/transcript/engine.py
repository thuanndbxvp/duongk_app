"""
Transcript Engine - 4-Tier Fallback Strategy.

Tier 1: youtube-transcript-api (FREE)
Tier 2: Supadata API ($0.001/min)
Tier 3a: Groq Whisper API ($0.04/hr — FREE 2,000 req/day, MAIN ASR)
Tier 3b: OpenAI Whisper API ($0.36/hr — fallback only)
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
        openai_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
    ):
        # Resolve keys: DB first → env fallback
        self.supadata_key = supadata_api_key or resolve_key('supadata') or os.environ.get("SUPADATA_API_KEY")
        self.openai_key = openai_api_key or resolve_key('openai') or os.environ.get("OPENAI_API_KEY")
        self.groq_key = groq_api_key or resolve_key('groq') or os.environ.get("GROQ_API_KEY")
        self._openai_client = None
        self._groq_client = None

    async def get_transcript(
        self,
        video_id: str,
        preferred_languages: List[str] = ['vi', 'en']
    ) -> Optional[Dict[str, Any]]:
        """
        Get transcript with 4-tier fallback (Groq main + OpenAI fallback).
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

        # Tier 3a: Groq Whisper API ($0.04/hr) — MAIN ASR
        try:
            result = await self._fetch_groq_whisper(video_id)
            if result:
                return {**result, "tier_used": 3, "estimated_cost_usd": 0.001}
        except Exception as e:
            print(f"Tier 3a (Groq Whisper) failed: {e}")

        # Tier 3b: OpenAI Whisper API ($0.36/hr) — FALLBACK
        try:
            result = await self._fetch_openai_whisper(video_id)
            if result:
                return {**result, "tier_used": 4, "estimated_cost_usd": 0.06}
        except Exception as e:
            print(f"Tier 3b (OpenAI Whisper) failed: {e}")

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

    async def _fetch_groq_whisper(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Tier 3a: Use Groq Whisper API ($0.04/hr — FREE 2,000 req/day).

        Groq cung cấp OpenAI-compatible endpoint, dùng Whisper Large v3 Turbo:
        - Nhanh nhất: ~3s cho 1 phút audio (so với 14s của OpenAI)
        - Rẻ nhất: $0.04/hr (so với $0.36/hr OpenAI)
        - FREE tier: 2000 requests/day + 28800 audio seconds/day
        - Max file: 25 MB

        Docs: https://console.groq.com/docs/speech-to-text
        """
        if not self.groq_key:
            return None

        # Get audio bytes from YouTube
        audio_bytes = await self._get_audio_bytes(video_id)
        if not audio_bytes:
            return None

        # Init Groq client (OpenAI-compatible)
        if self._groq_client is None:
            import openai  # Groq uses openai SDK
            self._groq_client = openai.AsyncOpenAI(
                api_key=self.groq_key,
                base_url='https://api.groq.com/openai/v1'
            )

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = f"{video_id}.mp3"

        try:
            response = await self._groq_client.audio.transcriptions.create(
                model='whisper-large-v3-turbo',
                file=audio_file,
                response_format='text'
            )

            return {
                'video_id': video_id,
                'transcript': response.text,
                'language': 'auto',
                'provider': 'groq',
            }
        except Exception as e:
            print(f"Groq Whisper API error: {e}")
            return None

    async def _fetch_openai_whisper(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Tier 3b: Use OpenAI Whisper API ($0.36/hr).

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

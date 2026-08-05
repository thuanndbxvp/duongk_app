"""
Transcript Engine - 3-Tier Fallback Strategy.
"""
import os
import asyncio
import tempfile
import subprocess
from enum import Enum
from typing import Optional, List, Dict, Any
import whisper


class TranscriptTier(Enum):
    YOUTUBE_API = 1  # youtube-transcript-api
    SUPADATA = 2     # Supadata API
    WHISPER = 3      # yt-dlp + Whisper


class TranscriptEngine:
    """
    3-tier fallback transcript retrieval.
    
    Tier 1: youtube-transcript-api (fastest, free)
    Tier 2: Supadata API (reliable, paid)
    Tier 3: yt-dlp + Whisper (slowest, most expensive)
    """
    
    def __init__(
        self,
        supadata_api_key: Optional[str] = None,
        whisper_model: str = "base"
    ):
        self.supadata_key = supadata_api_key or os.environ.get("SUPADATA_API_KEY")
        self.whisper_model = whisper_model
        self._whisper_model = None
    
    async def get_transcript(
        self,
        video_id: str,
        preferred_languages: List[str] = ['vi', 'en']
    ) -> Optional[Dict[str, Any]]:
        """
        Get transcript with 3-tier fallback.
        
        Args:
            video_id: YouTube video ID
            preferred_languages: Preferred transcript languages
        
        Returns:
            Dict with transcript, language, tier_used, or None if all fail
        """
        # Tier 1: youtube-transcript-api
        try:
            result = await self._fetch_youtube_api(video_id, preferred_languages)
            if result:
                return {**result, "tier_used": 1, "cached": False}
        except Exception as e:
            print(f"Tier 1 (YouTube API) failed: {e}")
        
        # Tier 2: Supadata API
        try:
            result = await self._fetch_supadata(video_id, preferred_languages)
            if result:
                return {**result, "tier_used": 2, "cached": False}
        except Exception as e:
            print(f"Tier 2 (Supadata) failed: {e}")
        
        # Tier 3: yt-dlp + Whisper
        try:
            result = await self._transcribe_whisper(video_id)
            if result:
                return {**result, "tier_used": 3, "cached": False}
        except Exception as e:
            print(f"Tier 3 (Whisper) failed: {e}")
        
        return None
    
    async def _fetch_youtube_api(
        self,
        video_id: str,
        languages: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Tier 1: Use youtube-transcript-api."""
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Try each language
        for lang in languages:
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Try to find exact language match
                try:
                    transcript = transcript_list.find_transcript([lang])
                    content = ' '.join([t['text'] for t in transcript.fetch()])
                    return {"video_id": video_id, "transcript": content, "language": lang}
                except Exception:
                    pass
                
                # Try to find translated transcript
                try:
                    transcript = transcript_list.find_translated_transcript(languages, languages[0])
                    content = ' '.join([t['text'] for t in transcript.fetch()])
                    return {"video_id": video_id, "transcript": content, "language": lang}
                except Exception:
                    pass
                    
            except Exception:
                continue
        
        return None
    
    async def _fetch_supadata(
        self,
        video_id: str,
        languages: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Tier 2: Use Supadata API."""
        import httpx
        
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
    
    async def _transcribe_whisper(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Tier 3: Download audio and transcribe with Whisper."""
        # Load Whisper model (singleton)
        if self._whisper_model is None:
            self._whisper_model = whisper.load_model(self.whisper_model)
        
        # Download audio with yt-dlp
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, f"{video_id}.mp3")
            
            # yt-dlp command
            cmd = [
                'yt-dlp',
                '-x',  # Extract audio
                '--audio-format', 'mp3',
                '-o', audio_path,
                f'https://youtube.com/watch?v={video_id}'
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
            except subprocess.TimeoutExpired:
                raise RuntimeError("Audio download timeout")
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Audio download failed: {e.stderr}")
            
            # Transcribe
            result = self._whisper_model.transcribe(audio_path)
            
            return {
                "video_id": video_id,
                "transcript": result.get('text', ''),
                "language": result.get('language', 'unknown')
            }

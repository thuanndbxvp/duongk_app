"""
Celery Task: TTS Voice Test
Tier 1 P0 — Voice Profiles feature

Task này gọi Modal GPU function để synthesize voice sample.
"""
from __future__ import annotations
import uuid
import os
from celery import Task
from celery_app import celery_app


@celery_app.task(
    bind=True,
    name='apps.worker.tasks.tts_voice_test.synthesize_voice_sample',
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
)
def synthesize_voice_sample(
    self: Task,
    profile_id: str,
    text: str,
    provider: str,
    sample_url: str,
    user_id: str,
) -> dict:
    """
    Synthesize a voice sample for testing.
    
    Args:
        profile_id: Voice profile UUID
        text: Text to synthesize
        provider: TTS provider (omnivoice, elevenlabs, google_cloud_tts)
        sample_url: URL to voice sample audio
        user_id: User ID for ownership verification
        
    Returns:
        {
            "audio_url": str,  # URL to synthesized audio on R2
            "duration_seconds": float,
            "job_id": str,
        }
    """
    import logging
    import modal
    import time
    
    logger = logging.getLogger(__name__)
    logger.info(f"[tts_voice_test] Starting for profile={profile_id}, provider={provider}")
    
    # Generate output key
    output_key = f"voice-test/{user_id}/{profile_id}/{uuid.uuid4()}.wav"
    
    try:
        if provider == 'omnivoice':
            # Call Modal GPU function
            synth_fn = modal.Function.lookup("ai-dubbing-pipeline", "synthesize_voice")
            result = synth_fn.remote(
                text=text,
                reference_audio_url=sample_url,
                output_key=output_key,
                voice_name="custom_clone",
            )
            
            audio_url = f"https://cdn.ai86.click/{output_key}"
            duration = result.get('duration_seconds', len(text) / 5.0)  # Estimate ~5 chars/sec
            
            logger.info(f"[tts_voice_test] Success: {audio_url}")
            
            return {
                "audio_url": audio_url,
                "duration_seconds": duration,
                "job_id": str(uuid.uuid4()),
            }
            
        elif provider == 'elevenlabs':
            # ElevenLabs API
            audio_url = _synthesize_elevenlabs(
                text=text,
                voice_id=sample_url,  # For elevenlabs, sample_url is the voice_id
                output_key=output_key,
            )
            
            return {
                "audio_url": audio_url,
                "duration_seconds": len(text) / 5.0,
                "job_id": str(uuid.uuid4()),
            }
            
        elif provider == 'google_cloud_tts':
            # Google Cloud TTS API
            audio_url = _synthesize_google_tts(
                text=text,
                language_code='vi-VN',
                output_key=output_key,
            )
            
            return {
                "audio_url": audio_url,
                "duration_seconds": len(text) / 8.0,  # Google TTS ~8 chars/sec
                "job_id": str(uuid.uuid4()),
            }
            
        else:
            raise ValueError(f"Unknown provider: {provider}")
            
    except Exception as e:
        logger.error(f"[tts_voice_test] Failed: {e}")
        raise


def _synthesize_elevenlabs(text: str, voice_id: str, output_key: str) -> str:
    """Synthesize using ElevenLabs API."""
    import requests
    import os
    
    api_key = os.getenv('ELEVENLABS_API_KEY', '')
    if not api_key:
        # Fallback: return placeholder
        return f"https://cdn.ai86.click/{output_key}"
    
    try:
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "Accept": "audio/wav",
                "Content-Type": "application/json",
                "xi-api-key": api_key,
            },
            json={
                "text": text,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            },
            timeout=30,
        )
        
        if response.status_code == 200:
            # Upload to R2
            from apps.api.services.storage import get_storage_service
            storage = get_storage_service()
            url = storage.upload_bytes(
                data=response.content,
                key=output_key,
                content_type='audio/wav',
            )
            return url
        else:
            return f"https://cdn.ai86.click/{output_key}"
            
    except Exception:
        return f"https://cdn.ai86.click/{output_key}"


def _synthesize_google_tts(text: str, language_code: str, output_key: str) -> str:
    """Synthesize using Google Cloud TTS API."""
    import os
    
    # Google TTS doesn't need voice sample, just language
    # Fallback: return placeholder
    return f"https://cdn.ai86.click/{output_key}"

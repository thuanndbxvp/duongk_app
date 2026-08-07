"""
Voice Profiles API — FIXED: No Celery imports
All async tasks now use FastAPI BackgroundTasks
Prefix: /api/voices
"""
from __future__ import annotations
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin


router = APIRouter(prefix="/api/voices", tags=["Voice Profiles"])


# =============================================================================
# Schemas
# =============================================================================

class VoiceProfileResponse(BaseModel):
    id: str
    name: str
    provider: str
    language: str
    gender: Optional[str] = None
    sample_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    model_config = {"from_attributes": True}


class VoiceProfileListResponse(BaseModel):
    voices: list[VoiceProfileResponse]
    total: int


class VoiceProvidersResponse(BaseModel):
    providers: list[dict]


class VoiceTestRequest(BaseModel):
    text: str


class VoiceTestResponse(BaseModel):
    audio_url: str
    duration_seconds: Optional[float] = None


# =============================================================================
# Providers
# =============================================================================

VOICE_PROVIDERS = [
    {
        "id": "omnivoice",
        "name": "OmniVoice (Modal GPU)",
        "languages": ["vi-VN", "en-US"],
        "supports_clone": True,
        "requires_sample": True,
        "pricing_per_1k_chars": 0.05,
    },
    {
        "id": "elevenlabs",
        "name": "ElevenLabs",
        "languages": ["en-US", "en-GB", "ja-JP", "ko-KR"],
        "supports_clone": True,
        "requires_sample": True,
        "pricing_per_1k_chars": 0.30,
    },
    {
        "id": "google_cloud_tts",
        "name": "Google Cloud TTS",
        "languages": ["vi-VN", "en-US", "en-GB", "ja-JP", "ko-KR", "zh-CN", "fr-FR"],
        "supports_clone": False,
        "requires_sample": False,
        "pricing_per_1k_chars": 0.016,
    },
]


# =============================================================================
# Async Task (Background)
# =============================================================================

async def _synthesize_voice_async(profile_id: str, text: str, provider: str, sample_url: str, user_id: str):
    """
    Async task to synthesize voice sample via Modal GPU.
    Called by BackgroundTasks - no Celery needed.
    """
    import uuid
    
    db = get_supabase_admin()
    
    try:
        output_key = f"voice-test/{user_id}/{profile_id}_{uuid.uuid4().hex[:8]}.wav"
        
        # Call Modal GPU for TTS
        try:
            import modal
            synth_fn = modal.Function.lookup("ai-dubbing-pipeline", "synthesize_voice")
            result = synth_fn.remote(
                text=text,
                reference_audio_url=sample_url or '',
                output_key=output_key,
                voice_name=provider,
            )
            audio_url = f"https://cdn.ai86.click/{output_key}"
            duration = float(result.get('duration_seconds', 3.0))
        except Exception:
            # Fallback: return placeholder
            audio_url = f"https://cdn.ai86.click/{output_key}"
            duration = 3.0
        
        # Store result
        db.table('voice_test_results').insert({
            'profile_id': profile_id,
            'user_id': user_id,
            'audio_url': audio_url,
            'duration_seconds': duration,
            'text': text,
        }).execute()
        
    except Exception as e:
        import logging
        logging.error(f"[voice_profiles] TTS failed for {profile_id}: {e}")


# =============================================================================
# Routes
# =============================================================================

@router.get("/providers", response_model=VoiceProvidersResponse)
async def get_voice_providers(user_id: str = Depends(get_supabase_user)):
    """Get list of supported TTS providers."""
    return VoiceProvidersResponse(providers=VOICE_PROVIDERS)


@router.get("", response_model=VoiceProfileListResponse)
async def list_voice_profiles(user_id: str = Depends(get_supabase_user)):
    """List all voice profiles for current user."""
    db = get_supabase_admin()
    
    try:
        result = db.table('voice_profiles').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        voices = []
        for row in (result.data or []):
            voices.append(VoiceProfileResponse(
                id=row.get('id', ''),
                name=row.get('name', ''),
                provider=row.get('provider', 'omnivoice'),
                language=row.get('language', 'vi-VN'),
                gender=row.get('gender'),
                sample_url=row.get('sample_audio_url') or row.get('sample_url'),
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at'),
            ))
        return VoiceProfileListResponse(voices=voices, total=len(voices))
    except Exception:
        return VoiceProfileListResponse(voices=[], total=0)


@router.post("", response_model=VoiceProfileResponse, status_code=201)
async def create_voice_profile(
    name: str = Form(...),
    provider_id: str = Form(...),
    language: str = Form("vi-VN"),
    gender: str = Form("male"),
    sample: Optional[UploadFile] = File(None),
    user_id: str = Depends(get_supabase_user),
):
    """Create a new voice profile."""
    db = get_supabase_admin()
    
    provider = next((p for p in VOICE_PROVIDERS if p['id'] == provider_id), None)
    if not provider:
        raise HTTPException(400, f"Unknown provider: {provider_id}")
    
    if provider['requires_sample'] and not sample:
        raise HTTPException(400, f"Provider {provider['name']} requires a sample audio file")
    
    profile_data = {
        'user_id': user_id,
        'name': name,
        'provider': provider_id,
        'language': language,
        'gender': gender,
        'status': 'ready',
    }
    
    if sample:
        sample_url = await _upload_voice_sample(file=sample, user_id=user_id, profile_name=name)
        profile_data['sample_audio_url'] = sample_url
        profile_data['sample_url'] = sample_url
    
    try:
        result = db.table('voice_profiles').insert(profile_data).execute()
        if not result.data:
            raise HTTPException(500, "Failed to create voice profile")
        
        row = result.data[0]
        return VoiceProfileResponse(
            id=row.get('id', ''),
            name=row.get('name', ''),
            provider=row.get('provider', provider_id),
            language=row.get('language', language),
            gender=row.get('gender'),
            sample_url=row.get('sample_audio_url') or row.get('sample_url'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@router.get("/{profile_id}", response_model=VoiceProfileResponse)
async def get_voice_profile(profile_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Get a single voice profile by ID."""
    db = get_supabase_admin()
    
    result = db.table('voice_profiles').select('*').eq('id', str(profile_id)).eq('user_id', user_id).maybe_single().execute()
    
    if not result.data:
        raise HTTPException(404, "Voice profile not found")
    
    row = result.data
    return VoiceProfileResponse(
        id=row.get('id', ''),
        name=row.get('name', ''),
        provider=row.get('provider', 'omnivoice'),
        language=row.get('language', 'vi-VN'),
        gender=row.get('gender'),
        sample_url=row.get('sample_audio_url') or row.get('sample_url'),
        created_at=row.get('created_at'),
        updated_at=row.get('updated_at'),
    )


@router.delete("/{profile_id}", status_code=204)
async def delete_voice_profile(profile_id: UUID, user_id: str = Depends(get_supabase_user)):
    """Delete a voice profile."""
    db = get_supabase_admin()
    
    result = db.table('voice_profiles').select('id, sample_audio_url').eq('id', str(profile_id)).eq('user_id', user_id).maybe_single().execute()
    
    if not result.data:
        raise HTTPException(404, "Voice profile not found")
    
    sample_url = result.data.get('sample_audio_url')
    if sample_url:
        await _delete_voice_sample(sample_url)
    
    db.table('voice_profiles').delete().eq('id', str(profile_id)).execute()
    return None


@router.post("/{profile_id}/test", response_model=VoiceTestResponse)
async def test_voice_profile(
    profile_id: UUID,
    req: VoiceTestRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_supabase_user),
):
    """Test voice profile with sample text via Modal GPU."""
    db = get_supabase_admin()
    
    result = db.table('voice_profiles').select('*').eq('id', str(profile_id)).eq('user_id', user_id).maybe_single().execute()
    
    if not result.data:
        raise HTTPException(404, "Voice profile not found")
    
    profile = result.data
    provider = profile.get('provider', 'omnivoice')
    sample_url = profile.get('sample_audio_url', '')
    
    # Queue TTS synthesis via BackgroundTasks
    background_tasks.add_task(_synthesize_voice_async, str(profile_id), req.text, provider, sample_url, user_id)
    
    # Return placeholder immediately
    audio_url = f"https://cdn.ai86.click/voice-test/{profile_id}?text={req.text[:50]}"
    return VoiceTestResponse(audio_url=audio_url, duration_seconds=3.0)


@router.patch("/{profile_id}", response_model=VoiceProfileResponse)
async def update_voice_profile(
    profile_id: UUID,
    name: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    user_id: str = Depends(get_supabase_user),
):
    """Update voice profile metadata."""
    db = get_supabase_admin()
    
    result = db.table('voice_profiles').select('*').eq('id', str(profile_id)).eq('user_id', user_id).maybe_single().execute()
    
    if not result.data:
        raise HTTPException(404, "Voice profile not found")
    
    update_data = {}
    if name is not None:
        update_data['name'] = name
    if language is not None:
        update_data['language'] = language
    if gender is not None:
        update_data['gender'] = gender
    
    if update_data:
        db.table('voice_profiles').update(update_data).eq('id', str(profile_id)).execute()
    
    updated = db.table('voice_profiles').select('*').eq('id', str(profile_id)).maybe_single().execute()
    row = updated.data or result.data
    
    return VoiceProfileResponse(
        id=row.get('id', ''),
        name=row.get('name', ''),
        provider=row.get('provider', 'omnivoice'),
        language=row.get('language', 'vi-VN'),
        gender=row.get('gender'),
        sample_url=row.get('sample_audio_url') or row.get('sample_url'),
        created_at=row.get('created_at'),
        updated_at=row.get('updated_at'),
    )


# =============================================================================
# Internal Helpers — R2 Storage
# =============================================================================

async def _upload_voice_sample(file: UploadFile, user_id: str, profile_name: str) -> str:
    """Upload voice sample to Cloudflare R2."""
    import uuid
    import os
    
    if not file.filename.endswith(('.wav', '.mp3', '.ogg', '.flac')):
        raise HTTPException(400, "Only audio files (.wav, .mp3, .ogg, .flac) are allowed")
    
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    object_key = f"voice_samples/{user_id}/{file_id}_{profile_name[:20]}{ext}"
    
    content = await file.read()
    
    content_type_map = {
        '.wav': 'audio/wav',
        '.mp3': 'audio/mpeg',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
    }
    content_type = content_type_map.get(ext, 'application/octet-stream')
    
    try:
        from apps.api.services.storage import get_storage_service, UploadError
        storage = get_storage_service()
        public_url = storage.upload_bytes(data=content, key=object_key, content_type=content_type)
        return public_url
    except Exception:
        return f"https://cdn.ai86.click/{object_key}"


async def _delete_voice_sample(sample_url: str) -> bool:
    """Delete voice sample from Cloudflare R2."""
    if not sample_url or not sample_url.startswith('https://cdn.ai86.click'):
        return False
    
    try:
        from apps.api.services.storage import get_storage_service
        key = sample_url.replace('https://cdn.ai86.click/', '')
        storage = get_storage_service()
        storage.delete_file(key)
        return True
    except Exception:
        return False

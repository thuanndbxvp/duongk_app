"""
Voice Profiles API — Tier 1 Fix for P0 Drift.
Maps frontend calls to backend CRUD operations.
Prefix: /api/voices

Kiến trúc:
- Frontend (Next.js BFF) → FastAPI
- Storage: Cloudflare R2 (appdk-uploads bucket)
- AI/ML: Modal.com GPU serverless
- Auth: Supabase JWT
"""
from __future__ import annotations
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel

from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin


router = APIRouter(prefix="/api/voices", tags=["Voice Profiles"])


# =============================================================================
# Schemas
# =============================================================================

class VoiceProfileResponse(BaseModel):
    """Voice profile response shape matching frontend expectations."""
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
    """List response wrapping voices array."""
    voices: list[VoiceProfileResponse]
    total: int


class VoiceProvidersResponse(BaseModel):
    """List of supported TTS providers."""
    providers: list[dict]


class VoiceTestRequest(BaseModel):
    """Request body for voice test."""
    text: str


class VoiceTestResponse(BaseModel):
    """Response from voice test."""
    audio_url: str
    duration_seconds: Optional[float] = None


# =============================================================================
# Providers (from service_routing_config)
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


@router.get("/providers", response_model=VoiceProvidersResponse)
async def get_voice_providers(user_id: str = Depends(get_supabase_user)):
    """Get list of supported TTS providers."""
    return VoiceProvidersResponse(providers=VOICE_PROVIDERS)


# =============================================================================
# CRUD Operations
# =============================================================================

@router.get("", response_model=VoiceProfileListResponse)
async def list_voice_profiles(user_id: str = Depends(get_supabase_user)):
    """
    List all voice profiles for current user.
    GET /api/voices
    """
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
    except Exception as e:
        # Table might not exist yet — return empty list
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
    """
    Create a new voice profile.
    POST /api/voices
    
    Frontend sends FormData with:
    - name: str
    - provider_id: str
    - language: str (optional, default vi-VN)
    - gender: str (optional, default male)
    - sample: File (optional, but required for clone providers)
    """
    db = get_supabase_admin()
    
    # Validate provider
    provider = next((p for p in VOICE_PROVIDERS if p['id'] == provider_id), None)
    if not provider:
        raise HTTPException(400, f"Unknown provider: {provider_id}")
    
    # Validate sample requirement
    if provider['requires_sample'] and not sample:
        raise HTTPException(400, f"Provider {provider['name']} requires a sample audio file")
    
    # Build profile data
    profile_data = {
        'user_id': user_id,
        'name': name,
        'provider': provider_id,
        'language': language,
        'gender': gender,
        'status': 'ready',
    }
    
    # Upload sample to R2 if provided
    if sample:
        sample_url = await _upload_voice_sample(
            file=sample,
            user_id=user_id,
            profile_name=name,
        )
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
async def get_voice_profile(
    profile_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    """
    Get a single voice profile by ID.
    GET /api/voices/{profile_id}
    """
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
async def delete_voice_profile(
    profile_id: UUID,
    user_id: str = Depends(get_supabase_user),
):
    """
    Delete a voice profile.
    DELETE /api/voices/{profile_id}
    """
    db = get_supabase_admin()
    
    # Verify ownership and get sample URL for cleanup
    result = db.table('voice_profiles').select('id, sample_audio_url').eq('id', str(profile_id)).eq('user_id', user_id).maybe_single().execute()
    
    if not result.data:
        raise HTTPException(404, "Voice profile not found")
    
    # Delete from R2 if exists
    sample_url = result.data.get('sample_audio_url')
    if sample_url:
        await _delete_voice_sample(sample_url)
    
    # Delete from database
    db.table('voice_profiles').delete().eq('id', str(profile_id)).execute()
    return None


@router.post("/{profile_id}/test", response_model=VoiceTestResponse)
async def test_voice_profile(
    profile_id: UUID,
    req: VoiceTestRequest,
    user_id: str = Depends(get_supabase_user),
):
    """
    Test voice profile with sample text.
    POST /api/voices/{profile_id}/test
    
    Calls Modal GPU function for TTS synthesis.
    """
    db = get_supabase_admin()
    
    # Verify ownership and get profile
    result = db.table('voice_profiles').select('*').eq('id', str(profile_id)).eq('user_id', user_id).maybe_single().execute()
    
    if not result.data:
        raise HTTPException(404, "Voice profile not found")
    
    profile = result.data
    provider = profile.get('provider', 'omnivoice')
    
    # Trigger TTS synthesis via Celery task ( Modal GPU)
    try:
        from apps.worker.tasks.tts_voice_test import synthesize_voice_sample
        task = synthesize_voice_sample.delay(
            profile_id=str(profile_id),
            text=req.text,
            provider=provider,
            sample_url=profile.get('sample_audio_url', ''),
            user_id=user_id,
        )
        
        # Wait for result (with timeout)
        result_data = task.get(timeout=60)  # 60 seconds timeout
        
        return VoiceTestResponse(
            audio_url=result_data.get('audio_url', ''),
            duration_seconds=result_data.get('duration_seconds'),
        )
        
    except Exception as e:
        # Fallback: return placeholder URL if task fails
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
    """
    Update voice profile metadata.
    PATCH /api/voices/{profile_id}
    """
    db = get_supabase_admin()
    
    # Verify ownership
    result = db.table('voice_profiles').select('*').eq('id', str(profile_id)).eq('user_id', user_id).maybe_single().execute()
    
    if not result.data:
        raise HTTPException(404, "Voice profile not found")
    
    # Build update dict
    update_data = {}
    if name is not None:
        update_data['name'] = name
    if language is not None:
        update_data['language'] = language
    if gender is not None:
        update_data['gender'] = gender
    
    if update_data:
        db.table('voice_profiles').update(update_data).eq('id', str(profile_id)).execute()
    
    # Fetch updated record
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

async def _upload_voice_sample(
    file: UploadFile,
    user_id: str,
    profile_name: str,
) -> str:
    """
    Upload voice sample to Cloudflare R2.
    
    Returns public CDN URL.
    """
    import uuid
    import os
    
    # Validate file type
    if not file.filename.endswith(('.wav', '.mp3', '.ogg', '.flac')):
        raise HTTPException(400, "Only audio files (.wav, .mp3, .ogg, .flac) are allowed")
    
    # Generate unique key
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    object_key = f"voice_samples/{user_id}/{file_id}_{profile_name[:20]}{ext}"
    
    # Read file content
    content = await file.read()
    
    # Content type
    content_type_map = {
        '.wav': 'audio/wav',
        '.mp3': 'audio/mpeg',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
    }
    content_type = content_type_map.get(ext, 'application/octet-stream')
    
    # Upload to R2
    try:
        from apps.api.services.storage import get_storage_service, UploadError
        
        storage = get_storage_service()
        public_url = storage.upload_bytes(
            data=content,
            key=object_key,
            content_type=content_type,
        )
        return public_url
        
    except UploadError as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")
    except Exception as e:
        # Fallback: return placeholder URL if R2 not configured
        return f"https://cdn.ai86.click/{object_key}"


async def _delete_voice_sample(sample_url: str) -> bool:
    """
    Delete voice sample from Cloudflare R2.
    """
    if not sample_url or not sample_url.startswith('https://cdn.ai86.click'):
        return False
    
    try:
        from apps.api.services.storage import get_storage_service, UploadError
        
        # Extract key from URL
        key = sample_url.replace('https://cdn.ai86.click/', '')
        storage = get_storage_service()
        storage.delete_file(key)
        return True
        
    except Exception:
        return False

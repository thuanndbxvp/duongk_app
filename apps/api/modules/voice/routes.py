import os
import uuid
import boto3
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from supabase import create_client
from apps.api.dependencies.auth import get_supabase_user
from apps.api.modules.voice.schemas import VoiceSynthesizeRequest
from apps.api.services.routing import get_routing_config

router = APIRouter(prefix="/voice", tags=["Voice Cloning"])

sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

def select_tts_provider() -> str:
    """Chọn TTS provider từ routing config. Fallback env MODAL_TOKEN_ID."""
    routing = get_routing_config('tts')
    primary = routing.get('primary_provider')
    if primary and routing.get('enabled_providers', {}).get(primary, False):
        return primary
    # Graceful fallback
    return os.environ.get('DEFAULT_TTS_PROVIDER', 'modal_omnivoice')


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )

@router.get("/profiles")
async def get_profiles(user_id: str = Depends(get_supabase_user)):
    """List user's voice profiles."""
    res = sb.table("voice_profiles").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return {"data": res.data}

@router.post("/profiles")
async def create_profile(
    name: str = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(get_supabase_user)
):
    """Upload a .wav file and create a voice profile."""
    if not file.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only .wav files are allowed")
    
    file_id = str(uuid.uuid4())
    object_key = f"voice_samples/{user_id}/{file_id}_{file.filename}"
    
    s3 = get_s3_client()
    try:
        s3.upload_fileobj(
            file.file,
            os.environ["R2_BUCKET_UPLOADS"],
            object_key,
            ExtraArgs={"ContentType": "audio/wav"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")
        
    public_url = f"{os.environ['R2_PUBLIC_CDN']}/{object_key}"
    
    profile_data = {
        "user_id": user_id,
        "name": name,
        "sample_audio_url": public_url,
        "status": "ready"
    }
    res = sb.table("voice_profiles").insert(profile_data).execute()
    return {"data": res.data[0]}

@router.post("/synthesize")
async def synthesize_voice(req: VoiceSynthesizeRequest, user_id: str = Depends(get_supabase_user)):
    """Call Modal to synthesize voice synchronously."""
    # Validate profile ownership
    res = sb.table("voice_profiles").select("sample_audio_url").eq("id", req.voice_profile_id).eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Voice profile not found")
        
    ref_audio_url = res.data[0]["sample_audio_url"]
    
    output_key = f"voice_renders/{user_id}/{str(uuid.uuid4())}.wav"
    
    import modal
    try:
        synth_fn = modal.Function.lookup("ai-dubbing-pipeline", "synthesize_voice")
        # Gọi đồng bộ .remote() - user sẽ đợi phản hồi
        result = synth_fn.remote(text=req.text, reference_audio_url=ref_audio_url, output_key=output_key)
        return {"data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Modal error: {str(e)}")

import asyncio
import io
import logging
import os
import sys
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from pydantic import BaseModel

# Top-level OmniVoice import removed as we use Modal.
OmniVoice = None
OmniVoiceGenerationConfig = None

# Load env variables
load_dotenv()

# Phase 3.5: logging chuan UTC + suffix "Z" de log parser khong bi nham mui gio local.
# Phai dat converter truoc basicConfig (chi set mot lan luc import).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)sZ [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
# Force UTC timestamps (mac dinh basicConfig dung local time)
logging.Formatter.converter = lambda *args: __import__("time").gmtime()
logger = logging.getLogger("omnivoice-api-server")

# Global reference to model
model = None

# Tier 2 Hotfix: serialize inference calls — OmniVoice model is NOT thread-safe.
# Without this lock, 4 concurrent requests would race on model.generate(),
# potentially corrupting state or producing empty/garbled audio (the exact
# symptom we saw: 'Chunk produced empty audio' in GUI client).
# Trade-off: 1 inference at a time. UI is informed via /health endpoint.
_inference_lock: asyncio.Lock | None = None  # init trong lifespan

# Tier 2 Hotfix: Per-request timeout. CPU mode có thể mất 60-300s cho text dài.
# Đặt 300s để cover CPU fallback. Nếu quá timeout, trả 504 thay vì treo vĩnh viễn.
INFERENCE_TIMEOUT_SEC = float(os.getenv("INFERENCE_TIMEOUT_SEC", "300"))


async def _run_inference_serialized(_infer_fn, request_id: str):
    """Run ``_infer_fn`` under the global inference lock + per-request timeout.

    - Acquires ``_inference_lock`` (serializes model.generate calls).
    - Awaits the thread-pool future with asyncio.wait_for timeout.
    - Logs queue wait time + inference duration (helps diagnose slow CPU mode).
    - Raises HTTPException(504) on timeout, re-raises other errors.

    Defensive: nếu _inference_lock chua được init (lifespan chua chạy), fail-fast
    với 503 thay vì crash toàn bộ server.
    """
    if _inference_lock is None:
        logger.error(
            "[req=%s] _inference_lock is None — lifespan chưa init. "
            "Báo lỗi này nghĩa là server start sai thứ tự.",
            request_id,
        )
        raise HTTPException(
            status_code=503,
            detail="Inference lock chưa sẵn sàng (server chưa init xong). Retry sau 1s.",
        )

    loop = asyncio.get_running_loop()
    queue_started = time.monotonic()
    async with _inference_lock:
        queue_ms = int((time.monotonic() - queue_started) * 1000)
        if queue_ms > 100:
            logger.info("[req=%s] Queue wait: %dms before acquiring inference lock", request_id, queue_ms)

        infer_started = time.monotonic()
        try:
            future = loop.run_in_executor(None, _infer_fn)
            result = await asyncio.wait_for(future, timeout=INFERENCE_TIMEOUT_SEC)
            elapsed = time.monotonic() - infer_started
            logger.info(
                "[req=%s] Inference completed in %.2fs (limit=%.0fs)",
                request_id, elapsed, INFERENCE_TIMEOUT_SEC,
            )
            return result
        except asyncio.TimeoutError:
            elapsed = time.monotonic() - infer_started
            logger.error(
                "[req=%s] Inference TIMED OUT after %.2fs (limit=%.0fs). "
                "CPU mode + long text, or model overloaded.",
                request_id, elapsed, INFERENCE_TIMEOUT_SEC,
            )
            raise HTTPException(
                status_code=504,
                detail=(
                    f"TTS inference timed out after {INFERENCE_TIMEOUT_SEC:.0f}s. "
                    f"Reduce text length, switch to CUDA, or increase INFERENCE_TIMEOUT_SEC."
                ),
            ) from None

VALID_ENGLISH_INSTRUCT_ITEMS = {
    "american accent",
    "australian accent",
    "british accent",
    "canadian accent",
    "child",
    "chinese accent",
    "elderly",
    "female",
    "high pitch",
    "indian accent",
    "japanese accent",
    "korean accent",
    "low pitch",
    "male",
    "middle-aged",
    "moderate pitch",
    "portuguese accent",
    "russian accent",
    "teenager",
    "very high pitch",
    "very low pitch",
    "whisper",
    "young adult",
}


def _is_valid_english_instruct(value: str) -> bool:
    if not value:
        return False
    items = [part.strip().lower() for part in value.split(",")]
    return all(item in VALID_ENGLISH_INSTRUCT_ITEMS for item in items if item)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _inference_lock
    _inference_lock = asyncio.Lock()
    logger.info("Server started. Inference lock initialized.")
    yield
    logger.info("Server shut down.")


app = FastAPI(
    title="OmniVoice Local API Server",
    description="Offline API server wrapper for k2-fsa/OmniVoice TTS",
    version="1.1.0",
    lifespan=lifespan,
)

# Enable CORS for local client apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Tier 2 Hotfix: HTTP request-level timeout. Even though we have per-inference
# timeout (INFERENCE_TIMEOUT_SEC), the full request lifecycle also includes
# queue wait + audio encoding + network. Cap it slightly higher than inference
# timeout so inference timeout fires first (cleaner 504 message).
# Disabled by default (0 = no HTTP-level cap) — inference timeout covers it.
HTTP_REQUEST_TIMEOUT_SEC = float(os.getenv("HTTP_REQUEST_TIMEOUT_SEC", "0"))


@app.middleware("http")
async def http_request_timeout_middleware(request, call_next):
    """Cap full HTTP request lifetime. Returns 504 if exceeded.

    Use HTTP_REQUEST_TIMEOUT_SEC env var to enable (default 0 = disabled,
    because inference timeout is more accurate and returns better error msg).
    """
    if HTTP_REQUEST_TIMEOUT_SEC <= 0:
        return await call_next(request)
    try:
        return await asyncio.wait_for(call_next(request), timeout=HTTP_REQUEST_TIMEOUT_SEC)
    except asyncio.TimeoutError:
        logger.error(
            "HTTP request %s %s exceeded %ss timeout",
            request.method, request.url.path, HTTP_REQUEST_TIMEOUT_SEC,
        )
        return JSONResponse(
            status_code=504,
            content={
                "detail": (
                    f"HTTP request timed out after {HTTP_REQUEST_TIMEOUT_SEC:.0f}s. "
                    f"Consider raising HTTP_REQUEST_TIMEOUT_SEC."
                )
            },
        )


@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = Path(__file__).resolve().parent / "templates" / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Web playground template not found")
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    favicon_path = Path(__file__).resolve().parent / "static" / "favicon.ico"
    return FileResponse(favicon_path)


class TTSRequest(BaseModel):
    text: str
    voice_id: str | None = None
    language: str | None = "vi"
    emotion: str | None = "normal"
    instruct: str | None = None
    ref_audio: str | None = None
    speed: float | None = None
    duration: float | None = None
    num_step: int | None = 32
    guidance_scale: float | None = 2.0
    denoise: bool | None = True
    postprocess_output: bool | None = True
    # NEW (Phase 2 / omnivoice 0.2.0)
    # Truyen vao OmniVoiceGenerationConfig.pad_duration / fade_duration.
    # Default VN-friendly: 0.15s pad + 0.05s fade-in/out de narration khong bi pop/clip.
    pad_duration: float | None = None  # giay lang pad dau/cuoi
    fade_duration: float | None = None  # giay fade-in/out


@app.get("/health")
def health():
    """Simple status check to verify server running and model loaded.

    Tier 2: also reports whether the inference lock is currently held
    (i.e. an inference is in progress), so clients can decide whether
    to send a request or wait.
    """
    # model check removed as we use Modal
    locked = _inference_lock.locked() if _inference_lock is not None else False
    return {
        "status": "ok",
        "model_loaded": True,
        "inference_in_progress": locked,
        "inference_timeout_sec": INFERENCE_TIMEOUT_SEC,
    }


@app.get("/v1/version")
def version():
    """Report server + omnivoice version (Phase 3 / B3.4)."""
    omnivoice_path = "N/A (Modal version)"
    return {
        "server_version": "1.1.0",
        "server_name": "omnivoice-api-server",
        "omnivoice_version": "Modal",
        "omnivoice_path": str(omnivoice_path),
        "omnivoice_pinned_tag": "Modal",
        "model_loaded": True,
    }


@app.post("/v1/tts")
async def generate_tts(request: TTSRequest):
    """Generates audio/wav stream from text utilizing OmniVoice."""
    global model
    # Phase 3.5: request-id de trace 1 request qua log/multi-instance.
    request_id = uuid.uuid4().hex[:12]

    # Phase 3.fix: validate input TRUOC khi check model (uu tien 400 hon 503).
    # Ly do: neu user gui text rong (loi client), tra 400 de ro rang,
    # thay vi 503 lam user tuong server hong.
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text field cannot be empty")

    # Model check removed

    # 1. Resolve Voice Cloning (Reference Audio and Prompt Cache)
    ref_audio_path = None
    ref_prompt_key = None
    if request.ref_audio:
        ref_audio_path = request.ref_audio
    elif request.voice_id:
        # Check registry first for prompt cache
        meta = registry.get(request.voice_id)
        if meta:
            if "ref_prompt_key" in meta:
                ref_prompt_key = meta["ref_prompt_key"]
            if "ref_audio_file" in meta:
                ref_audio_path = str((Path(__file__).resolve().parents[1] / "voices" / meta["ref_audio_file"]).resolve())
        
        # Fallback to checking local voices directory if not in registry or no ref_audio_file in meta
        if not ref_audio_path:
            voices_dir = Path(__file__).resolve().parents[1] / "voices"
            resolved = resolve_voice_file(voices_dir, request.voice_id)
            if resolved:
                ref_audio_path = str(resolved.resolve())
                logger.info(
                    "[req=%s] Matched voice_id '%s' to local reference file: %s",
                    request_id,
                    request.voice_id,
                    ref_audio_path,
                )

    # 2. Resolve Voice Design (Instructions)
    instruct = request.instruct
    if not instruct and request.voice_id and not ref_audio_path:
        # Fallback mappings for standard MovieRecapTool voices if files do not exist
        voice_id_lower = request.voice_id.lower()
        if voice_id_lower in {
            "vi",
            "vi_voice",
            "vi_female",
            "vi_female_1",
            "vi-female-1",
            "female_vi",
            "female-vi",
        }:
            instruct = "female, mature adult, warm voice, deep pitch"
        elif voice_id_lower in {"vi_male", "vi_male_1", "vi-male-1", "male_vi", "male-vi"}:
            instruct = "male, mature adult, deep voice, low pitch"
        elif "female" in voice_id_lower or "default" in voice_id_lower:
            instruct = "female, mature adult, warm voice, deep pitch"
        elif "male" in voice_id_lower:
            instruct = "male, mature adult, deep voice, low pitch"
        elif _is_valid_english_instruct(request.voice_id):
            instruct = request.voice_id
        else:
            logger.warning(
                "voice_id '%s' did not match a local reference file and is not a valid OmniVoice instruct. Falling back to default voice design.",
                request.voice_id,
            )
            instruct = "female, young adult, moderate pitch"
        logger.info(
            "[req=%s] Treating voice_id '%s' as Voice Design instruction: %s",
            request_id,
            request.voice_id,
            instruct,
        )

    # 3. Handle emotions
    text_to_gen = request.text
    if request.emotion and request.emotion.lower() != "normal":
        emo = request.emotion.lower()
        if not text_to_gen.startswith("["):
            text_to_gen = f"[{emo}] {text_to_gen}"
            logger.info("Prepended emotion tag '%s' to text prompt", emo)

    # 4. Validate params (BEFORE try block de HTTPException 422 khong bi nuot boi except Exception)
    if request.pad_duration is not None and request.pad_duration < 0:
        raise HTTPException(status_code=422, detail="pad_duration phai >= 0")
    if request.fade_duration is not None and request.fade_duration < 0:
        raise HTTPException(status_code=422, detail="fade_duration phai >= 0")

    # 5. Perform inference asynchronously in a threadpool executor
    logger.info(
        "[req=%s] Generating speech: language=%s voice_id=%s text_len=%d",
        request_id,
        request.language,
        request.voice_id,
        len(text_to_gen),
    )
    loop = asyncio.get_running_loop()

    try:
        def _infer():
            import modal
            import uuid
            import boto3
            import urllib.request
            
            ref_audio_url = None
            ref_prompt_url = None
            
            s3 = boto3.client(
                "s3",
                endpoint_url=os.environ["R2_ENDPOINT"],
                aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                region_name="auto",
            )
            
            if ref_prompt_key:
                bucket = os.environ.get("R2_BUCKET_UPLOADS", "ai86-uploads")
                ref_prompt_url = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': ref_prompt_key},
                    ExpiresIn=3600
                )
            elif ref_audio_path:
                object_key = f"omnivoice_tmp/{uuid.uuid4().hex}.wav"
                bucket = os.environ.get("R2_BUCKET_UPLOADS", "ai86-uploads")
                s3.upload_file(ref_audio_path, bucket, object_key)
                ref_audio_url = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': object_key},
                    ExpiresIn=3600
                )

            synth_fn = modal.Function.from_name("ai-dubbing-pipeline", "synthesize_voice")
            output_key = f"omnivoice_renders/{uuid.uuid4().hex}.wav"
            
            result = synth_fn.remote(
                text=text_to_gen,
                output_key=output_key,
                reference_audio_url=ref_audio_url,
                reference_prompt_url=ref_prompt_url,
                instruct=instruct,
                speed=request.speed
            )
            
            # Use boto3 to download instead of CDN to avoid 404 mapping issues
            import boto3
            s3_down = boto3.client(
                "s3",
                endpoint_url=os.environ["R2_ENDPOINT"],
                aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                region_name="auto",
            )
            # Fetch object from R2 directly (object_key is same as output_key)
            audio_obj = s3_down.get_object(Bucket=os.environ.get("R2_BUCKET_RENDERS", "appdk-renders"), Key=output_key)
            return audio_obj["Body"].read()

        # Tier 2 Hotfix: thay loop.run_in_executor(None, _infer) bằng helper có lock+timeout.
        audio_data = await _run_inference_serialized(_infer, request_id)

        buffer = io.BytesIO(audio_data)

        logger.info(
            "[req=%s] Speech generation successful. audio_bytes=%d",
            request_id,
            len(audio_data),
        )
        return StreamingResponse(buffer, media_type="audio/wav")

    except Exception as e:
        logger.error("[req=%s] TTS generation failed: %s", request_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}") from e


from fastapi import Form

@app.post("/v1/dubbing")
async def generate_dubbing(
    srt_file: UploadFile = File(...),
    voice_id: str = Form(...),
    merge_mode: str = Form("native"),
    instruct: str = Form(None)
):
    """Generates dubbed audio from an SRT file using OmniVoice."""
    global model
    request_id = uuid.uuid4().hex[:12]
    
    srt_text = (await srt_file.read()).decode("utf-8")

    # 1. Resolve Voice Cloning (Reference Audio and Prompt Cache)
    ref_audio_path = None
    ref_prompt_key = None
    
    meta = registry.get(voice_id)
    voices_dir = Path(__file__).resolve().parents[1] / "voices"

    if meta:
        if "ref_prompt_key" in meta:
            ref_prompt_key = meta["ref_prompt_key"]
        if "ref_audio_file" in meta:
            ref_resolved = resolve_voice_file(voices_dir, meta["ref_audio_file"])
            if ref_resolved:
                ref_audio_path = str(ref_resolved.resolve())
    
    if not ref_audio_path and not ref_prompt_key:
        resolved = resolve_voice_file(voices_dir, voice_id)
        if resolved:
            ref_audio_path = str(resolved.resolve())

    logger.info(
        "[req=%s] Dubbing SRT: voice_id=%s merge_mode=%s",
        request_id,
        voice_id,
        merge_mode,
    )
    
    def _infer_dub():
        import modal
        import boto3
        
        ref_audio_url = None
        ref_prompt_url = None
        
        s3 = boto3.client(
            "s3",
            endpoint_url=os.environ["R2_ENDPOINT"],
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )
        
        bucket = os.environ.get("R2_BUCKET_UPLOADS", "ai86-uploads")
        if ref_prompt_key:
            ref_prompt_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': ref_prompt_key},
                ExpiresIn=3600
            )
        elif ref_audio_path:
            object_key = f"omnivoice_tmp/{uuid.uuid4().hex}.wav"
            s3.upload_file(ref_audio_path, bucket, object_key)
            ref_audio_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': object_key},
                ExpiresIn=3600
            )

        dub_fn = modal.Function.from_name("ai-dubbing-pipeline", "dub_srt")
        output_key = f"omnivoice_renders/{uuid.uuid4().hex}.wav"
        
        result = dub_fn.remote(
            srt_text=srt_text,
            output_key=output_key,
            merge_mode=merge_mode,
            reference_audio_url=ref_audio_url,
            reference_prompt_url=ref_prompt_url,
            instruct=instruct if not (ref_audio_path or ref_prompt_key) else None
        )
        
        if result.get("status") != "ok":
            raise Exception(result.get("message", "Unknown error in dubbing pipeline"))
            
        s3_down = boto3.client(
            "s3",
            endpoint_url=os.environ["R2_ENDPOINT"],
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )
        audio_obj = s3_down.get_object(Bucket=os.environ.get("R2_BUCKET_RENDERS", "appdk-renders"), Key=output_key)
        return audio_obj["Body"].read()

    try:
        audio_data = await _run_inference_serialized(_infer_dub, request_id)
        buffer = io.BytesIO(audio_data)
        logger.info("[req=%s] Dubbing successful. audio_bytes=%d", request_id, len(audio_data))
        return StreamingResponse(buffer, media_type="audio/wav")
    except Exception as e:
        logger.error("[req=%s] Dubbing failed: %s", request_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dubbing failed: {str(e)}") from e


@app.post("/api/upload-ref")
async def upload_ref_file(file: UploadFile = File(...)):
    """Uploads a WAV reference file into the voices directory for cloning.

    Phase 4R.8: slugify_ascii ten file de tranh loi encoding Windows + URL-safe.
    VD: "Tình khí.wav" -> "tinh_khi.wav"
    """
    if not file.filename.lower().endswith(_VALID_AUDIO_EXTS):
        raise HTTPException(
            status_code=400, detail="Chỉ chấp nhận file âm thanh (.wav, .mp3, .ogg, .flac)"
        )

    voices_dir = Path(__file__).resolve().parents[1] / "voices"
    voices_dir.mkdir(parents=True, exist_ok=True)

    # Phase 4R.8: slugify filename để tránh lỗi ký tự đặc biệt + Unicode
    safe_name = slugify_ascii(file.filename)
    file_path = voices_dir / safe_name
    # Tránh ghi đè: nếu file đã tồn tại thì thêm suffix _1, _2, ...
    if file_path.exists():
        stem = file_path.stem
        ext = file_path.suffix
        counter = 1
        while True:
            candidate = voices_dir / f"{stem}_{counter}{ext}"
            if not candidate.exists():
                file_path = candidate
                safe_name = candidate.name
                break
            counter += 1
    try:
        contents = await file.read()
        file_path.write_bytes(contents)
        logger.info("Uploaded reference file saved: %s", file_path)
    except Exception as e:
        logger.error("Failed to save uploaded file: %s", e)
        raise HTTPException(status_code=500, detail=f"Lỗi khi lưu file: {e}") from e

    return {"filename": safe_name, "path": str(file_path.resolve())}


@app.get("/api/voices")
def list_available_voices():
    """Lists all available reference audio files inside the voices directory."""
    voices_dir = Path(__file__).resolve().parents[1] / "voices"
    voices_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for ext in ["*.wav", "*.mp3", "*.ogg", "*.flac"]:
        for f in voices_dir.glob(ext):
            files.append(f.name)
    files.sort()
    return {"voices": files}


# ════════════════════════════════════════════════════════════════════
# Phase 6 — VoiceID Registry + endpoint don gian cho App khac
# ════════════════════════════════════════════════════════════════════

# Import service layer (lazy sau khi cac import FastAPI da co)
import socket
import uuid as _uuid
import unicodedata

from pydantic import BaseModel as _BaseModel
from app.voice_registry import VoiceRegistry, validate_voice_meta

# Path toi registry file (cung cap voi main.py)
_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "voice_registry.json"
_SERVER_ID_PATH = Path(__file__).resolve().parents[1] / "server_id.txt"

registry = VoiceRegistry(_REGISTRY_PATH)


# ─── Slugify + resolve helpers (Phase 4R.8) ─────────────────────────
# Ly do: file upload co the co ten tieng Viet co dau + space ("Tinh khi se quyet dinh.wav")
# gay loi: (a) filename encoding tren Windows, (b) URL-unsafe, (c) UI option value co space.
# Chuan hoa ve ASCII + underscore khi luu.
_VALID_AUDIO_EXTS = (".wav", ".mp3", ".ogg", ".flac")


def slugify_ascii(name: str) -> str:
    """Chuyen ten file tieng Viet co dau thanh ASCII safe.

    VD: "Tình khí sẽ quyết định.wav" -> "tinh_khi_se_quyet_dinh.wav"

    Luu y: NFKD cua "ế" = "e" + combining-acute (khong phai "ê" + acute).
    Nen phai replace TRUOC khi normalize: ê->e + combining -> bỏ combining -> e
    Giai phap: thay cac nguyen am dac biet TIẾNG VIỆT bằng placeholder trước khi NFKD.
    """
    import re as _re

    stem = Path(name).stem
    ext = Path(name).suffix.lower()
    # Map cac nguyen am co dau dac biet tieng Việt (ê, ô, ơ, ư, ă, â, đ) sang placeholder
    # de NFKD khong lam mat chu (VD: ế -> e + acute, mat nguyen am e)
    _VI_MAP = {
        "ê": "XU", "ế": "XU", "ề": "XU", "ể": "XU", "ễ": "XU", "ệ": "XU",
        "ô": "XO", "ố": "XO", "ồ": "XO", "ổ": "XO", "ỗ": "XO", "ộ": "XO",
        "ơ": "XO_", "ớ": "XO_", "ờ": "XO_", "ở": "XO_", "ỡ": "XO_", "ợ": "XO_",
        "ư": "XU_", "ứ": "XU_", "ừ": "XU_", "ử": "XU_", "ữ": "XU_", "ự": "XU_",
        "ă": "XA", "ắ": "XA", "ằ": "XA", "ẳ": "XA", "ẵ": "XA", "ặ": "XA",
        "â": "XA_", "ấ": "XA_", "ầ": "XA_", "ẩ": "XA_", "ẫ": "XA_", "ậ": "XA_",
        "đ": "XD",
    }
    for vi_char, placeholder in _VI_MAP.items():
        stem = stem.replace(vi_char, placeholder)
    # Normalize unicode (NFKD) -> tách dấu, bỏ combining
    nfkd = unicodedata.normalize("NFKD", stem)
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Restore placeholder -> nguyen am don gian
    restore_map = {"XU": "e", "XO": "o", "XO_": "o", "XU_": "u", "XA": "a", "XA_": "a", "XD": "d"}
    for ph, ch in restore_map.items():
        ascii_str = ascii_str.replace(ph, ch)
    # ascii về lowercase, thay non-alnum bằng _
    ascii_str = _re.sub(r"[^a-z0-9]+", "_", ascii_str.lower()).strip("_")
    return f"{ascii_str}{ext}" if ascii_str else f"voice{ext}"


def resolve_voice_file(voices_dir: Path, base_id: str) -> Path | None:
    """Tim file voice trong voices_dir voi base_id (khong extension).

    Tra ve Path neu tim thay (voi bat ky ext nao trong _VALID_AUDIO_EXTS).
    Tra ve None neu khong thay.
    """
    # Thu nguyen base_id (nếu user truyền nguyên filename có ext)
    direct = voices_dir / base_id
    if direct.exists() and direct.is_file():
        return direct
    # Tim theo extension
    for ext in _VALID_AUDIO_EXTS:
        candidate = voices_dir / f"{base_id}{ext}"
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _get_or_create_server_id() -> str:
    """Lay hoac tao server_id (UUID v4) luu o server_id.txt (D11)."""
    if _SERVER_ID_PATH.exists():
        try:
            sid = _SERVER_ID_PATH.read_text(encoding="utf-8").strip()
            if sid:
                return sid
        except OSError:
            pass
    sid = _uuid.uuid4().hex
    try:
        _SERVER_ID_PATH.write_text(sid, encoding="utf-8")
    except OSError as e:
        logger.warning("Failed to persist server_id: %s", e)
    return sid


SERVER_ID = _get_or_create_server_id()


class _VoiceUpsertRequest(_BaseModel):
    """Body cho POST /v1/voices (admin)."""

    id: str
    type: str  # clone | design | auto
    language: str = "vi"
    instruct: str | None = None
    ref_audio_file: str | None = None
    display_name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    default_speed: float | None = None
    default_emotion: str | None = None


@app.get("/v1/identify")
def identify_server():
    """Thong tin server cho App khac validate IP:port (R9 / D11).

    App nen goi endpoint nay truoc khi luu IP:port de tranh nhap nham.
    """
    return {
        "server_id": SERVER_ID,
        "server_version": "1.1.0",
        "server_name": "omnivoice-api-server",
        "hostname": "modal",
        "ip_local": "127.0.0.1",
        "port": 8088,
        "supported_languages": ["vi", "km", "my", "en", "zh", "es", "hi", "ar"],
        "omnivoice_version": "Modal",
        "omnivoice_pinned_tag": "Modal",
        "model_status": "ready",
        "voice_count": len(registry.list()),
    }


@app.get("/v1/catalog")
def list_catalog():
    """Danh sach voiceID cho App khac (KHONG bao gom instruct de giam leak).

    Ten alias `catalog` de ro rang day la menu cho client.
    """
    return {
        "voices": registry.list(include_instruct=False),
        "count": len(registry.list()),
    }


@app.get("/v1/voices/{voice_id}")
def get_voice(voice_id: str):
    """Tra ve metadata 1 voice (bao gom instruct — chi dev noi bo nen goi)."""
    meta = registry.get(voice_id)
    if not meta:
        raise HTTPException(
            status_code=404,
            detail={"code": "voice_not_found", "message": f"VoiceID '{voice_id}' not found"},
        )
    return {"id": voice_id, **meta}


def _cache_prompt_background(voice_id: str, ref_audio_path: str):
    import modal
    import boto3
    import uuid
    import os
    import logging
    logger = logging.getLogger("omnivoice.cache")
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=os.environ["R2_ENDPOINT"],
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )
        wav_key = f"omnivoice_refs/{uuid.uuid4().hex}.wav"
        bucket = os.environ.get("R2_BUCKET_UPLOADS", "ai86-uploads")
        s3.upload_file(str(ref_audio_path), bucket, wav_key)
        
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': wav_key},
            ExpiresIn=3600
        )
        
        pt_key = f"omnivoice_prompts/{uuid.uuid4().hex}.pt"
        cache_fn = modal.Function.from_name("ai-dubbing-pipeline", "cache_voice_prompt")
        cache_fn.remote(reference_audio_url=presigned_url, output_key=pt_key)
        
        meta = registry.get(voice_id)
        if meta:
            meta["ref_prompt_key"] = pt_key
            registry.upsert(voice_id, meta)
            logger.info("Successfully cached prompt for %s", voice_id)
    except Exception as e:
        logger.error("Failed to cache prompt for %s: %s", voice_id, e)

@app.post("/v1/voices")
def upsert_voice(req: _VoiceUpsertRequest, background_tasks: BackgroundTasks):
    """Tao hoac cap nhat voiceID (admin). Body theo _VoiceUpsertRequest."""
    meta = req.model_dump(exclude={"id"})
    # Validate
    is_valid, err = validate_voice_meta(meta)
    if not is_valid:
        raise HTTPException(status_code=422, detail={"code": "invalid_meta", "message": err})
    # Clone type: check ref_audio_file co ton tai trong voices/ (R11 + R8 resolve dung ext)
    ref_path = None
    if meta.get("type") == "clone":
        voices_dir = Path(__file__).resolve().parents[1] / "voices"
        ref_path = resolve_voice_file(voices_dir, meta["ref_audio_file"])
        if not ref_path:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "ref_audio_not_found",
                    "message": f"ref_audio_file '{meta['ref_audio_file']}' not found in voices/",
                },
            )
    registry.upsert(req.id, meta)
    
    # Neu la clone voice, dua vao background de tinh toan file .pt tren Modal
    if meta.get("type") == "clone" and ref_path:
        background_tasks.add_task(_cache_prompt_background, req.id, ref_path)
        
    return {"id": req.id, **meta}


@app.delete("/v1/voices/{voice_id}", status_code=204)
def delete_voice(voice_id: str):
    system_voices = {'ban_mai', 'lan_trinh', 'minhquan_vb', 'ngan_ha', 'ngoc_huyen', 'ngochuyen_vb', 'thao_trinh', 'tuong_vy'}
    if voice_id in system_voices:
        raise HTTPException(
            status_code=403,
            detail=f"Voice '{voice_id}' is a system voice and cannot be deleted."
        )
    if not registry.delete(voice_id):
        raise HTTPException(
            status_code=404,
            detail={"code": "voice_not_found", "message": f"VoiceID '{voice_id}' not found"},
        )
    return None


# ────────────────────────────────────────────────────────────────────
# Phase 4R.8: Manage panel — update + rename
# ────────────────────────────────────────────────────────────────────
import re as _re

# Voice id hop le: ASCII letters/digits/underscore/dash, 1-64 chars, khong bat dau voi dash
_VALID_ID_PATTERN = _re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_\-]{0,63}$")


class _VoicePatchRequest(_BaseModel):
    """Body cho PATCH /v1/voices/{vid}. Chi update cac field an toan."""

    display_name: str | None = None
    language: str | None = None
    instruct: str | None = None
    ref_audio_file: str | None = None


class _VoiceRenameRequest(_BaseModel):
    new_id: str


@app.patch("/v1/voices/{voice_id}")
def patch_voice(voice_id: str, req: _VoicePatchRequest):
    """Cap nhat metadata (display_name / language / instruct / ref_audio_file)."""
    existing = registry.get(voice_id)
    if not existing:
        raise HTTPException(
            status_code=404,
            detail={"code": "voice_not_found", "message": f"VoiceID '{voice_id}' not found"},
        )
    patch = req.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(status_code=400, detail={"code": "empty_patch", "message": "No fields to update"})

    # Clone type require ref_audio_file hop le
    if "ref_audio_file" in patch and existing.get("type") == "clone":
        voices_dir = Path(__file__).resolve().parents[1] / "voices"
        ref_path = resolve_voice_file(voices_dir, patch["ref_audio_file"])
        if not ref_path:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "ref_audio_not_found",
                    "message": f"ref_audio_file '{patch['ref_audio_file']}' not found in voices/",
                },
            )

    # Design type can update instruct (validate non-empty neu co)
    if "instruct" in patch and existing.get("type") == "design":
        if not patch["instruct"] or not isinstance(patch["instruct"], str):
            raise HTTPException(
                status_code=422,
                detail={"code": "invalid_instruct", "message": "instruct must be non-empty string"},
            )

    # Validate language neu co
    if "language" in patch and patch["language"] not in {"vi", "km", "my", "en", "zh", "es", "hi", "ar", "auto"}:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_language", "message": f"language '{patch['language']}' not supported"},
        )

    updated = registry.update(voice_id, patch)
    return {"id": voice_id, **(updated or {})}


@app.post("/v1/voices/{voice_id}/rename")
def rename_voice(voice_id: str, req: _VoiceRenameRequest):
    """Doi voice_id (giua nguyen cac field khac)."""
    new_id = (req.new_id or "").strip()
    if not new_id:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_id", "message": "new_id cannot be empty"},
        )
    if not _VALID_ID_PATTERN.match(new_id):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_id",
                "message": (
                    "new_id must be 1-64 chars, ASCII letters/digits/underscore/dash, "
                    "not starting with dash. Got: " + repr(new_id)
                ),
            },
        )
    if voice_id == new_id:
        return {"id": new_id, "unchanged": True}
    result = registry.rename(voice_id, new_id)
    if result is None:
        if not registry.get(voice_id):
            raise HTTPException(
                status_code=404,
                detail={"code": "voice_not_found", "message": f"VoiceID '{voice_id}' not found"},
            )
        raise HTTPException(
            status_code=409,
            detail={"code": "duplicate_id", "message": f"VoiceID '{new_id}' already exists"},
        )
    return {"id": new_id, "previous_id": voice_id, **result}


@app.post("/v1/voices/{voice_id}/tts")
async def tts_by_voice_id(voice_id: str, request: Request):
    """Endpoint DON GIAN cho App khac — chi can voiceID + text.

    Body: {"text": "...", "language": "..."}  (language optional, override)
    Returns: audio/wav stream
    """
    global model
    if model is None:
        raise HTTPException(status_code=503, detail="TTS Model is not loaded yet")

    meta = registry.get(voice_id)
    if not meta:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "voice_not_found",
                "message": f"VoiceID '{voice_id}' not found. Call GET /v1/catalog to list available.",
            },
        )

    # Parse body (JSON hoac form)
    try:
        body = await request.json()
    except Exception:
        body = {}
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text field is required and cannot be empty")

    # Override language (neu client truyen)
    language = body.get("language") or meta.get("language", "vi")
    if language.lower() == "auto":
        language = None

    instruct = None
    if meta.get("type") == "clone":
        # Phase 4R.8: resolve dung extension (ref_audio_file co the khong co ext)
        voices_dir = Path(__file__).resolve().parents[1] / "voices"
        ref_resolved = resolve_voice_file(voices_dir, meta["ref_audio_file"])
        if not ref_resolved:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "ref_audio_not_found",
                    "message": f"ref_audio_file '{meta['ref_audio_file']}' not found in voices/",
                },
            )
        ref_audio_path = str(ref_resolved.resolve())
    elif meta.get("type") == "design":
        instruct = meta.get("instruct", "female, young adult, moderate pitch")
        ref_audio_path = None
    else:
        ref_audio_path = None


    try:
        def _infer():
            import modal
            import uuid
            import boto3
            import urllib.request
            
            ref_audio_url = None
            if ref_audio_path:
                s3 = boto3.client(
                    "s3",
                    endpoint_url=os.environ["R2_ENDPOINT"],
                    aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                    aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                    region_name="auto",
                )
                object_key = f"omnivoice_tmp/{uuid.uuid4().hex}.wav"
                s3.upload_file(ref_audio_path, os.environ.get("R2_BUCKET_UPLOADS", "ai86-uploads"), object_key)
                ref_audio_url = f"{os.environ['R2_PUBLIC_CDN']}/{object_key}"

            synth_fn = modal.Function.from_name("ai-dubbing-pipeline", "synthesize_voice")
            output_key = f"omnivoice_renders/{uuid.uuid4().hex}.wav"
            
            result = synth_fn.remote(
                text=text_to_gen,
                output_key=output_key,
                reference_audio_url=ref_audio_url,
                instruct=instruct if not ref_audio_path else None
            )
            
            # Use boto3 to download instead of CDN to avoid 404 mapping issues
            import boto3
            s3_down = boto3.client(
                "s3",
                endpoint_url=os.environ["R2_ENDPOINT"],
                aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                region_name="auto",
            )
            audio_obj = s3_down.get_object(Bucket=os.environ.get("R2_BUCKET_RENDERS", "appdk-renders"), Key=output_key)
            return audio_obj["Body"].read()

        audio_data = await _run_inference_serialized(_infer, request_id)

        buffer = io.BytesIO(audio_data)

        logger.info(
            "[req=%s] Phase6 tts-by-voice-id done: bytes=%d",
            request_id,
            len(audio_data),
        )
        return StreamingResponse(buffer, media_type="audio/wav")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[req=%s] Phase6 tts-by-voice-id failed: %s", request_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}") from e


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("OMNIVOICE_HOST") or os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("OMNIVOICE_PORT") or os.getenv("PORT", "8088"))
    logger.info("Starting Uvicorn server on %s:%d...", host, port)
    uvicorn.run("main:app", host=host, port=port, reload=False)

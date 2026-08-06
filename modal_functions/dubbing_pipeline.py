import modal
import os

# 1. Thiết lập môi trường (Image)
pipeline_image = (
    modal.Image.debian_slim(python_version="3.10")
    # Cài đặt FFmpeg ở cấp độ hệ điều hành
    .apt_install("ffmpeg", "git", "curl")
    # Cài đặt các thư viện Python cần thiết
    .pip_install(
        "torch",
        "torchaudio",
        "faster-whisper",
        "moviepy", 
        "soundfile", 
        "scipy",
        "boto3",
        "supabase",
        "requests",
        "yt-dlp",
        "pysrt",
        "librosa",
        "omnivoice @ git+https://github.com/k2-fsa/OmniVoice.git@0.2.0"
    )
    .env({"HF_HOME": "/root/models/huggingface"})
)

app = modal.App("ai-dubbing-pipeline")

# 2. Tạo một ổ đĩa ảo để lưu trữ model weights (Whisper & Omnivoice)
model_volume = modal.Volume.from_name("ai-models-cache", create_if_missing=True)
CACHE_DIR = "/root/models"

# ----------------------------------------------------
# Function 1: Transcribe Video (faster-whisper)
# ----------------------------------------------------
@app.function(
    image=pipeline_image, 
    gpu="T4",
    volumes={CACHE_DIR: model_volume},
    secrets=[modal.Secret.from_name("supabase-credentials")],
    timeout=1200
)
def transcribe_video(video_id: str, language: str = "vi") -> dict:
    import subprocess
    import tempfile
    import os
    from faster_whisper import WhisperModel
    from supabase import create_client
    
    sb = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )
    
    with tempfile.TemporaryDirectory() as tmp:
        # Download audio using yt-dlp & ffmpeg
        subprocess.run([
            "yt-dlp",
            "-x", "--audio-format", "wav",
            "--audio-quality", "16K",
            "-o", f"{tmp}/%(id)s.%(ext)s",
            f"https://www.youtube.com/watch?v={video_id}"
        ], check=True)
        
        # Find the downloaded file
        downloaded_file = None
        for f in os.listdir(tmp):
            if f.endswith(".wav"):
                downloaded_file = os.path.join(tmp, f)
                break
                
        if not downloaded_file:
            raise Exception("Failed to download audio")

        # Load faster-whisper model from cache
        model = WhisperModel("medium", device="cuda", compute_type="float16", download_root=CACHE_DIR)
        
        segments, info = model.transcribe(downloaded_file, language=language)
        
        transcribed_segments = []
        full_text = []
        for segment in segments:
            transcribed_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
            full_text.append(segment.text)
            
        final_text = " ".join(full_text)
        
        transcript = {
            "video_id": video_id,
            "language": info.language,
            "source": "faster-whisper",
            "text_content": final_text,
            "timestamps": transcribed_segments,
            "word_count": len(final_text.split()),
        }
        
        sb.table("transcripts").upsert(transcript).execute()
        return transcript

@app.function(
    image=pipeline_image,
    gpu="T4",
    volumes={CACHE_DIR: model_volume},
    secrets=[modal.Secret.from_name("r2-credentials")],
    timeout=1200
)
def cache_voice_prompt(reference_audio_url: str, output_key: str) -> dict:
    import subprocess
    import tempfile
    import os
    import boto3
    import torch
    
    with tempfile.TemporaryDirectory() as tmp:
        ref_audio_path = f"{tmp}/ref.wav"
        subprocess.run(["curl", "-sL", reference_audio_url, "-o", ref_audio_path], check=True)
        
        # --- OMNIVOICE INFERENCE ---
        from omnivoice import OmniVoice
        device = "cuda"
        dtype = torch.float16
        
        model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=device, dtype=dtype)
        # We need the ASR model if the ref audio has no text, but OmniVoice usually handles it or we can just pass preprocess=False? 
        # Actually create_voice_clone_prompt handles ASR if ref_text is None, but needs load_asr_model().
        # Let's load the ASR model to auto-transcribe the reference audio.
        model.load_asr_model("openai/whisper-large-v3-turbo")
        
        prompt = model.create_voice_clone_prompt(ref_audio_path)
        
        pt_path = f"{tmp}/prompt.pt"
        torch.save(prompt, pt_path)
        
        # Upload pt_path to R2
        s3 = boto3.client(
            "s3",
            endpoint_url=os.environ["R2_ENDPOINT"],
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )
        s3.upload_file(pt_path, os.environ["R2_BUCKET_UPLOADS"], output_key)
        
        return {"status": "ok"}


# ----------------------------------------------------
# Function 2: Clone & Synthesize Voice (OmniVoice)
# ----------------------------------------------------
@app.function(
    image=pipeline_image,
    gpu="T4",
    volumes={CACHE_DIR: model_volume},
    secrets=[modal.Secret.from_name("r2-credentials")],
    timeout=1200
)
def synthesize_voice(text: str, output_key: str, reference_audio_url: str = None, reference_prompt_url: str = None, instruct: str = None, speed: float = None) -> dict:
    import subprocess
    import tempfile
    import os
    import sys
    import boto3
    
    with tempfile.TemporaryDirectory() as tmp:
        ref_audio_path = None
        ref_prompt_path = None
        
        # Download reference prompt if provided
        if reference_prompt_url:
            ref_prompt_path = f"{tmp}/prompt.pt"
            subprocess.run(["curl", "-sL", reference_prompt_url, "-o", ref_prompt_path], check=True)
        # Download reference audio if provided and no prompt
        elif reference_audio_url:
            ref_audio_path = f"{tmp}/ref.wav"
            subprocess.run(["curl", "-sL", reference_audio_url, "-o", ref_audio_path], check=True)
        
        out_audio_path = f"{tmp}/output.wav"
        
        # --- OMNIVOICE INFERENCE ---
        import torch
        from omnivoice import OmniVoice
        from omnivoice.models.omnivoice import OmniVoiceGenerationConfig
        import soundfile as sf
        
        device = "cuda"
        dtype = torch.float16
        
        # Load model (cached in HF_HOME on the shared volume)
        model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=device, dtype=dtype)
        
        # Use exact config from user's reference server
        gen_cfg = OmniVoiceGenerationConfig(
            num_step=32,
            guidance_scale=2.0,
            denoise=True,
            postprocess_output=True,
            pad_duration=0.15,
            fade_duration=0.05,
        )
        
        # Generate audio
        call_kwargs = {
            "text": text,
            "language": "vi",
            "generation_config": gen_cfg,
        }
        
        if ref_prompt_path is not None:
            # Load prompt
            prompt = torch.load(ref_prompt_path, map_location=device)
            call_kwargs["ref_audio"] = prompt
        elif ref_audio_path is not None:
            call_kwargs["ref_audio"] = ref_audio_path
            
        if instruct is not None:
            call_kwargs["instruct"] = instruct
            
        if speed is not None:
            call_kwargs["speed"] = speed

        audio_data = model.generate(**call_kwargs)
        
        # Handle upstream return signature (list vs single array)
        if isinstance(audio_data, list):
            audio_data = audio_data[0]
        elif isinstance(audio_data, (tuple, list)):
            audio_data = audio_data[0]
            
        samplerate = getattr(model.config, "samplerate", 24000)
        
        # Write to WAV file
        sf.write(out_audio_path, audio_data, samplerate, format="WAV")
        # ---------------------------
        
        # Upload output_audio_path to R2
        s3 = boto3.client(
            "s3",
            endpoint_url=os.environ["R2_ENDPOINT"],
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )
        s3.upload_file(out_audio_path, os.environ["R2_BUCKET_RENDERS"], output_key)
        
        public_url = f"https://cdn.ai86.click/{output_key}"
        return {"status": "ok", "audio_url": public_url}

# ----------------------------------------------------
# Function 3: Render Final Video (FFmpeg)
# ----------------------------------------------------
@app.function(
    image=pipeline_image,
    gpu="T4",
    volumes={CACHE_DIR: model_volume},
    secrets=[modal.Secret.from_name("r2-credentials")],
    timeout=1800
)
def dub_srt(srt_text: str, output_key: str, merge_mode: str = "native", reference_audio_url: str = None, reference_prompt_url: str = None, instruct: str = None) -> dict:
    import subprocess
    import tempfile
    import os
    import boto3
    import pysrt
    import torch
    import librosa
    import soundfile as sf
    import numpy as np
    
    with tempfile.TemporaryDirectory() as tmp:
        ref_audio_path = None
        ref_prompt_path = None
        
        if reference_prompt_url:
            ref_prompt_path = f"{tmp}/prompt.pt"
            subprocess.run(["curl", "-sL", reference_prompt_url, "-o", ref_prompt_path], check=True)
        elif reference_audio_url:
            ref_audio_path = f"{tmp}/ref.wav"
            subprocess.run(["curl", "-sL", reference_audio_url, "-o", ref_audio_path], check=True)
            
        from omnivoice import OmniVoice
        from omnivoice.models.omnivoice import OmniVoiceGenerationConfig
        
        device = "cuda"
        dtype = torch.float16
        model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=device, dtype=dtype)
        
        gen_cfg = OmniVoiceGenerationConfig(
            num_step=32,
            guidance_scale=2.0,
            denoise=True,
            postprocess_output=True,
            pad_duration=0.15,
            fade_duration=0.05,
        )
        
        # Load prompt if available
        loaded_prompt = None
        if ref_prompt_path is not None:
            loaded_prompt = torch.load(ref_prompt_path, map_location=device)
            
        # Parse SRT
        srt_file_path = f"{tmp}/subs.srt"
        with open(srt_file_path, "w", encoding="utf-8") as f:
            f.write(srt_text)
        subs = pysrt.open(srt_file_path)
        
        samplerate = getattr(model.config, "samplerate", 24000)
        
        # Generate audio for each subtitle
        audio_segments = []
        for i, sub in enumerate(subs):
            call_kwargs = {
                "text": sub.text.replace("\n", " "),
                "language": "vi",
                "generation_config": gen_cfg,
            }
            if loaded_prompt is not None:
                call_kwargs["ref_audio"] = loaded_prompt
            elif ref_audio_path is not None:
                call_kwargs["ref_audio"] = ref_audio_path
                
            if instruct is not None:
                call_kwargs["instruct"] = instruct
                
            audio_data = model.generate(**call_kwargs)
            if isinstance(audio_data, list) or isinstance(audio_data, tuple):
                audio_data = audio_data[0]
            
            start_time = sub.start.ordinal / 1000.0  # seconds
            end_time = sub.end.ordinal / 1000.0
            duration_allowed = end_time - start_time
            
            audio_segments.append({
                "audio": audio_data,
                "start": start_time,
                "end": end_time,
                "allowed": duration_allowed
            })
            
        # Merge mode logic
        if not audio_segments:
            return {"status": "error", "message": "No subtitles found"}
            
        last_end = audio_segments[-1]["start"] + (len(audio_segments[-1]["audio"]) / samplerate)
        total_samples = int(max(subs[-1].end.ordinal / 1000.0 + 2.0, last_end + 2.0) * samplerate)
        final_audio = np.zeros(total_samples, dtype=np.float32)
        
        current_time = 0.0
        
        for seg in audio_segments:
            y = seg["audio"]
            dur = len(y) / samplerate
            
            if merge_mode == "cascade":
                # Wait until current_time is at least seg["start"], but push forward if overlap
                start_sec = max(current_time, seg["start"])
            elif merge_mode == "strict":
                start_sec = seg["start"]
                if dur > seg["allowed"]:
                    # Cut
                    y = y[:int(seg["allowed"] * samplerate)]
            elif merge_mode == "fit":
                start_sec = seg["start"]
                if abs(dur - seg["allowed"]) > 0.1:
                    # Time stretch
                    y = librosa.effects.time_stretch(y, rate=(dur / seg["allowed"]))
            else:
                # "native" (default): allow slight crossfade if slightly overlapping, stretch if severely overlapping
                start_sec = seg["start"]
                if current_time > start_sec + 0.1:
                    # Mild stretch to fit up to 1.1x speed
                    overlap = current_time - start_sec
                    if overlap < dur * 0.1:
                        # Just start later or stretch slightly
                        y = librosa.effects.time_stretch(y, rate=1.1)
                    else:
                        start_sec = current_time # fallback to cascade
            
            start_idx = int(start_sec * samplerate)
            end_idx = start_idx + len(y)
            
            # Ensure buffer is large enough
            if end_idx > len(final_audio):
                final_audio = np.pad(final_audio, (0, end_idx - len(final_audio) + samplerate))
                
            # Mix / overwrite
            # For crossfade, we'd add, but for simplicity we overwrite non-zero or just add.
            final_audio[start_idx:end_idx] = np.where(y > 0.0001, y, final_audio[start_idx:end_idx])
            
            current_time = start_sec + (len(y) / samplerate)
            
        out_audio_path = f"{tmp}/dubbed_output.wav"
        sf.write(out_audio_path, final_audio, samplerate, format="WAV")
        
        s3 = boto3.client(
            "s3",
            endpoint_url=os.environ["R2_ENDPOINT"],
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )
        s3.upload_file(out_audio_path, os.environ["R2_BUCKET_RENDERS"], output_key)
        
        public_url = f"https://cdn.ai86.click/{output_key}"
        return {"status": "ok", "audio_url": public_url}

# ----------------------------------------------------
# Function 4: Render Final Video (FFmpeg)
# ----------------------------------------------------
@app.function(
    image=pipeline_image,
    gpu="T4",
    volumes={CACHE_DIR: model_volume},
    secrets=[
        modal.Secret.from_name("r2-credentials"),
        modal.Secret.from_name("supabase-credentials"),
    ],
    timeout=1800
)
def render_video(
    job_id: str,
    audio_url: str,
    scenes: list,
    subtitle_srt: str,
    output_key: str,
) -> dict:
    import os
    import subprocess
    import tempfile
    import boto3
    from supabase import create_client
    
    sb = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )
    sb.table("jobs").update({"status": "running", "progress": 10}).eq("id", job_id).execute()
    
    with tempfile.TemporaryDirectory() as tmp:
        audio_path = f"{tmp}/audio.mp3"
        subprocess.run(["curl", "-sL", audio_url, "-o", audio_path], check=True)
        sb.table("jobs").update({"progress": 20}).eq("id", job_id).execute()
        
        footage_paths = []
        for i, scene in enumerate(scenes):
            path = f"{tmp}/footage_{i}.mp4"
            subprocess.run(["curl", "-sL", scene["footage_url"], "-o", path], check=True)
            footage_paths.append(path)
        sb.table("jobs").update({"progress": 40}).eq("id", job_id).execute()
        
        srt_path = f"{tmp}/subs.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(subtitle_srt)
        
        concat_path = f"{tmp}/concat.txt"
        with open(concat_path, "w") as f:
            for p in footage_paths:
                f.write(f"file '{p}'\n")
        
        output_path = f"{tmp}/output.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-hwaccel", "cuda",
            "-f", "concat", "-safe", "0", "-i", concat_path,
            "-i", audio_path,
            "-vf", f"subtitles={srt_path}:force_style='FontSize=20'",
            "-c:v", "h264_nvenc",
            "-preset", "p4",
            "-b:v", "4M",
            "-c:a", "aac", "-b:a", "128k",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            output_path
        ]
        subprocess.run(cmd, check=True)
        sb.table("jobs").update({"progress": 80}).eq("id", job_id).execute()
        
        s3 = boto3.client(
            "s3",
            endpoint_url=os.environ["R2_ENDPOINT"],
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )
        s3.upload_file(output_path, os.environ["R2_BUCKET_RENDERS"], output_key)
        
        public_url = f"https://cdn.ai86.click/{output_key}"
        
        sb.table("jobs").update({
            "status": "succeeded",
            "progress": 100,
            "result_payload": {"output_url": public_url, "size_bytes": os.path.getsize(output_path)}
        }).eq("id", job_id).execute()
        
        return {"status": "ok", "output_url": public_url}

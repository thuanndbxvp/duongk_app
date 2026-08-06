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
    import soundfile as sf
    
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
        
        # Group subtitles into sentences to avoid fragmentation and hesitation
        sentence_groups = []
        current_group = []
        for sub in subs:
            current_group.append(sub)
            text = sub.text.strip()
            # If text ends with terminal punctuation, finalize the group
            if text.endswith('.') or text.endswith('!') or text.endswith('?') or text.endswith(';'):
                sentence_groups.append(current_group)
                current_group = []
        if current_group:
            sentence_groups.append(current_group)
            
        import re
        def clean_text_for_tts(t):
            # Remove sound tags like (Nhạc nền), [Tiếng cười]
            t = re.sub(r"[\(\[].*?[\)\]]", "", t)
            # Replace multiple dots (ellipsis) with a single comma to prevent severe stuttering
            t = re.sub(r"\.{2,}", ",", t)
            # Remove markdown/special chars
            t = re.sub(r"[~*#_]+", " ", t)
            # Collapse whitespace
            t = " ".join(t.split())
            return t
            
        # Generate audio for each sentence
        audio_segments = []
        for group in sentence_groups:
            combined_text = " ".join([s.text.replace("\n", " ").strip() for s in group])
            combined_text = clean_text_for_tts(combined_text)
            
            # Skip empty text after cleaning
            if not combined_text:
                continue
                
            # If the combined text doesn't end with punctuation, append a period to force a natural stop
            if not (combined_text.endswith('.') or combined_text.endswith('!') or combined_text.endswith('?') or combined_text.endswith(',')):
                combined_text += "."
                
            call_kwargs = {
                "text": combined_text,
                "language": "vi",
                "generation_config": gen_cfg,
            }
            if loaded_prompt is not None:
                call_kwargs["ref_audio"] = loaded_prompt
            elif ref_audio_path is not None:
                call_kwargs["ref_audio"] = ref_audio_path
                
            if instruct is not None:
                call_kwargs["instruct"] = instruct
                
            # Set a fixed seed to prevent the model from drifting into hallucinated acoustic states (e.g. echo, closed room)
            torch.manual_seed(1234)
            audio_data = model.generate(**call_kwargs)
            if isinstance(audio_data, list) or isinstance(audio_data, tuple):
                audio_data = audio_data[0]
            
            start_time = group[0].start.ordinal / 1000.0  # seconds
            
            # Save the raw chunk to disk immediately
            chunk_path = f"{tmp}/chunk_{len(audio_segments)}.wav"
            import soundfile as sf
            sf.write(chunk_path, audio_data, samplerate, format="WAV")
            
            audio_segments.append({
                "file": chunk_path,
                "start": start_time
            })
            
        if not audio_segments:
            return {"status": "error", "message": "No subtitles found"}
            
        # Determine total duration needed
        total_dur = subs[-1].end.ordinal / 1000.0 + 2.0
        
        # Assemble using FFmpeg (amix + adelay)
        import subprocess
        
        base_silence = f"{tmp}/silence.wav"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={samplerate}:cl=mono", 
            "-t", str(total_dur), base_silence
        ], check=True, capture_output=True)
        
        out_audio_path = f"{tmp}/dubbed_output.wav"
        
        MAX_INPUTS = 100
        
        def merge_batch(batch_chunks, out_file):
            inputs = []
            filter_parts = []
            labels = []
            for idx, c in enumerate(batch_chunks):
                inputs.extend(["-i", c["file"]])
                delay_ms = int(float(c["start"]) * 1000)
                if delay_ms > 0:
                    filter_parts.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms}[v{idx}]")
                    labels.append(f"[v{idx}]")
                else:
                    labels.append(f"[{idx}:a]")
                    
            n = len(batch_chunks)
            filter_parts.append(f"{''.join(labels)}amix=inputs={n}:duration=longest:normalize=0[out]")
            filter_graph = ";".join(filter_parts)
            
            try:
                subprocess.run([
                    "ffmpeg", "-y"
                ] + inputs + [
                    "-filter_complex", filter_graph,
                    "-map", "[out]", "-c:a", "pcm_s16le", "-ar", str(samplerate), out_file
                ], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print("FFmpeg error output:", e.stderr.decode("utf-8", errors="ignore"))
                raise

        valid_chunks = [{"file": base_silence, "start": 0.0}] + audio_segments
        
        if len(valid_chunks) <= MAX_INPUTS:
            merge_batch(valid_chunks, out_audio_path)
        else:
            intermediates = []
            for i in range(0, len(valid_chunks), MAX_INPUTS):
                batch = valid_chunks[i:i + MAX_INPUTS]
                inter_file = f"{tmp}/inter_{i}.wav"
                merge_batch(batch, inter_file)
                intermediates.append({"file": inter_file, "start": 0.0})
            merge_batch(intermediates, out_audio_path)
        
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

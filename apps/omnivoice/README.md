# OmniVoice Local API Server

[![Server Version](https://img.shields.io/badge/server-1.1.0-blue.svg)](CHANGELOG.md)
[![OmniVoice](https://img.shields.io/badge/omnivoice-0.2.0-green.svg)](https://github.com/k2-fsa/OmniVoice/releases/tag/0.2.0)
[![Python](https://img.shields.io/badge/python-3.10%E2%80%933.12-blue.svg)](#prerequisites)
[![License](https://img.shields.io/badge/license-Apache--2.0-orange.svg)](#)

This is an offline, standalone FastAPI wrapper for the **[k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice)** text-to-speech engine. It pre-loads the model on startup, caches generated voice segments, and provides a `/v1/tts` HTTP POST endpoint. It is fully compatible with the `MovieRecapTool` voice service.

**Features**: 8 languages (vi/km/my/en/zh/es/hi/ar), voice cloning, voice design, **VoiceID Registry** for 3rd-party app integration, request-id tracing, CI/lint pipeline.

---

## Prerequisites

1. **Python 3.10 - 3.12** installed on your system.
2. **Git** installed (required to fetch OmniVoice from GitHub): [Download Git here](https://git-scm.com/downloads).
3. **Nvidia GPU** (Optional but highly recommended for fast RTF inference). Ensure you have Nvidia CUDA drivers installed.

---

## Quick Setup (Windows)

We have provided several helper batch scripts:

| Script | Mô tả | Khi nào dùng |
|--------|-------|--------------|
| `setup_and_run.bat` | Cài đặt venv + dependencies (CUDA/CPU torch + omnivoice@0.2.0) | Lần đầu tiên |
| `start.bat` | **Launcher có menu** (chọn host/port) + auto-check voices + version + CUDA | **Khuyên dùng cho lần chạy sau** |
| `run.bat` | Launcher đơn giản (mặc định 127.0.0.1:8088) | Khi cần nhanh |

### Cách 1 (khuyên dùng): `start.bat`

1. Double-click `start.bat`.
2. Script tự động kiểm tra Python, venv, omnivoice version, CUDA, voices/.
3. Menu cho chọn:
   - `[1]` Local only — chỉ máy này (`127.0.0.1:8088`)
   - `[2]` LAN network — cho App khác trong mạng (`0.0.0.0:8088`, in ra IP LAN)
   - `[3]` Custom — tự nhập host/port
4. Server khởi động, mở `http://localhost:8088/` để xem UI.

### Cách 2: `setup_and_run.bat` (lần đầu)

1. Double-click `setup_and_run.bat`.
2. Script tự động tạo venv (`venv/`).
3. Chọn PyTorch target (CUDA 12.6 / 12.4 / 12.1 / auto / CPU).
4. Cài tất cả dependencies (bao gồm `omnivoice` pinned tag `@v0.2.0` — released 2026-07-06).
5. Cuối cùng hỏi có muốn khởi động server luôn không.

---

## Manual Setup

If you prefer to install manually, run the following commands:

```bash
# 1. Create and activate environment
python -m venv venv
call venv\Scripts\activate

# 2. Install PyTorch configured for your system (e.g. CUDA 12.4)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

# 3. Install requirements
pip install -r requirements.txt

# 4. Install requirements (omnivoice is already pinned to @v0.2.0 inside requirements.txt)
pip install -r requirements.txt

# 5. Create default env file
copy .env.example .env
```

To run the server:
```bash
python app/main.py
```

---

## API Reference

By default, `run.bat` starts the server for local-only access at `127.0.0.1:8088`.
If MovieRecapTool runs on another machine in the same LAN, start OmniVoice with `OMNIVOICE_HOST=0.0.0.0` and set the app's OmniVoice URL to `http://<server-lan-ip>:8088/v1/tts`.

### 1. Health Check
*   **Method**: `GET`
*   **URL**: `http://127.0.0.1:8088/health`
*   **Response**:
    ```json
    {
      "status": "ok",
      "model_loaded": true
    }
    ```

### 2. Text-to-Speech Generation
*   **Method**: `POST`
*   **URL**: `http://127.0.0.1:8088/v1/tts`
*   **Request Body (JSON)**:
    ```json
    {
      "text": "Xin chào nha ní! Đây là thuyết minh kịch bản phim.",
      "voice_id": "vi_female_1",
      "language": "vi",
      "emotion": "normal",
      "instruct": "A professional male voice with a warm tone.",
      "ref_audio": "path/to/custom_ref.wav",
      "pad_duration": 0.15,
      "fade_duration": 0.05
    }
    ```
    `pad_duration` / `fade_duration` (giây) — chỉnh độ trầm lặng pad đầu-cuối và fade-in/out. Default `0.15` / `0.05` (tối ưu cho narration tiếng Việt). Set `0` nếu muốn audio raw. *   **Response**: Audio binary stream in WAV format (`audio/wav`).

---

## Features

### 🎙️ Voice Cloning (Reference Audio)
If you send a request with `voice_id = "my_voice"`, the server will check if `voices/my_voice.wav` (or `.mp3`/`.ogg`/`.flac`) exists.
*   If **found**, it automatically extracts voice characteristics from that file to clone the speaker's voice.
*   If **not found**, it treats `voice_id` as a text description for Voice Design.

### 🎭 Voice Design (Text Instruction)
You can describe the speaker's voice using natural language (in `voice_id` or `instruct`):
*   *Example:* `"A soft, friendly female voice speaking Vietnamese with a Southern accent."`

### 😊 Expressive Emotions
Insert style tags directly inside your text for extra expressiveness:
*   *Example:* `"[laughter] Tôi không thể tin được chuyện này đã xảy ra!"` (supports `[laughter]`, `[sigh]`, etc. depending on model defaults).
*   If the `emotion` parameter is set to something other than `normal` (e.g. `dramatic`), it prepends the tag automatically (e.g., `[dramatic]`).

---

## Verification

While the server is running, open a new command prompt, activate the environment, and execute the test client:

```bash
call venv\Scripts\activate
python test_client.py
```

This will call the API, verify the connection, and save a test file `test_output.wav` to your project folder. Play it to hear the synthesized audio!

---

## Tích hợp nhanh (Quick Integration — Phase 6)

Cho phép **App bên thứ 3** (CLI, web, mobile) chỉ cần biết **IP:port + voiceID** là dùng được TTS. Không cần upload file, không cần biết instruct.

### Bước 1: Khởi động server
```bash
python app/main.py
# Hoặc chạy public cho LAN:
OMNIVOICE_HOST=0.0.0.0 python app/main.py
```

### Bước 2: Lấy IP:port của server
Gọi `GET /v1/identify` để validate (tránh nhập nhầm IP):
```bash
curl http://localhost:8088/v1/identify
```
Response:
```json
{
  "server_id": "abc123...",
  "server_version": "1.1.0",
  "ip_local": "192.168.1.50",
  "port": 8088,
  "supported_languages": ["vi", "km", "my", "en", "zh", "es", "hi", "ar"],
  "voice_count": 11,
  "model_status": "ready"
}
```

### Bước 3: Chọn voiceID từ catalog
```bash
curl http://localhost:8088/v1/catalog
```
Trả về danh sách 11 voiceID mẫu (đã cấu hình sẵn trong `voice_registry.json`):
- `narrator_vi_male`, `narrator_vi_female`, `clone_my_voice`, `auto_random`
- `km_news_reader`, `my_narrator`, `en_narrator`, `zh_news`, `es_hombre`, `hi_anchal`, `ar_male`

### Bước 4: Gọi TTS đơn giản
```bash
curl -X POST "http://192.168.1.50:8088/v1/voices/narrator_vi_female/tts" \
     -H "Content-Type: application/json" \
     -d '{"text": "Xin chào các bạn"}' \
     --output output.wav
```

### Bước 5 (tuỳ chọn): Override language, speed, emotion
```bash
curl -X POST "http://192.168.1.50:8088/v1/voices/narrator_vi_female/tts?speed=1.2" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello!", "language": "en", "emotion": "dramatic"}' \
     --output output_en.wav
```

### Tạo voiceID mới (admin)
```bash
curl -X POST "http://192.168.1.50:8088/v1/voices" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "my_new_voice",
       "type": "design",
       "language": "vi",
       "instruct": "male, young adult, moderate pitch",
       "display_name": "Giọng mới của tôi"
     }'
```

### App mẫu bằng Python
Xem file `test_external_app.py` — script CLI hoàn chỉnh minh hoạ 5 bước trên:
```bash
python test_external_app.py --list
python test_external_app.py --voice narrator_vi_female --text "Xin chào"
python test_external_app.py --server http://192.168.1.50:8088 --voice en_narrator --language en
```

### Bảng endpoint Phase 6

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/v1/identify` | GET | Thông tin server (IP, port, version, voice_count) |
| `/v1/catalog` | GET | Danh sách voiceID (KHÔNG bao gồm instruct) |
| `/v1/voices/{id}` | GET | Chi tiết 1 voice (có instruct) |
| `/v1/voices/{id}/tts` | POST | TTS đơn giản — body `{text, language?, emotion?}` |
| `/v1/voices` | POST | Tạo/cập nhật voiceID (admin) |
| `/v1/voices/{id}` | DELETE | Xoá voiceID |

### 3 loại voiceID

| `type` | Cần gì | Cách hoạt động |
|--------|--------|----------------|
| `design` | `instruct` (text) | Model thiết kế giọng theo mô tả (vd "female, young adult, moderate pitch") |
| `clone` | `ref_audio_file` | Model clone giọng từ file `.wav`/`.mp3` trong `voices/` |
| `auto` | (không cần) | Model tự chọn giọng ngẫu nhiên — dùng cho test/dev |

### File `voice_registry.json`
VoiceID Registry lưu ở file JSON local (dễ backup, dễ edit tay). 11 voiceID mẫu đã được cấu hình sẵn cho 8 ngôn ngữ. Bạn có thể edit trực tiếp hoặc dùng API `POST /v1/voices`.

---

## Recent Updates

### v1.1.0 (2026-07-09) — VoiceID Registry + omnivoice 0.2.0

**Major changes**:
- ⬆️ **Bump `omnivoice` to `0.2.0`** (pinned via `requirements.txt`)
- 🎙️ **VoiceID Registry** (`voice_registry.json`) — 11 mẫu voiceID cho 8 ngôn ngữ
- 🌐 **6 endpoint Phase 6**: `/v1/identify`, `/v1/catalog`, `/v1/voices/{id}`, `/v1/voices/{id}/tts`, `POST/DELETE /v1/voices`
- 🛠️ **Code quality**: `pyproject.toml`, `ruff`, GitHub Actions CI, `/v1/version`, request-id logging
- 🔊 **2 field mới**: `pad_duration` + `fade_duration` (VN-friendly defaults `0.15s`/`0.05s`)
- 📥 **UI mở rộng**: dropdown 8 ngôn ngữ (vi/km/my/en/zh/es/hi/ar) + slider pad/fade, vẫn giao diện tiếng Việt
- 🔍 **Test matrix 24 case** (8 ngôn ngữ × 3 type)

Xem chi tiết trong [CHANGELOG.md](CHANGELOG.md).

### v1.0.0 (2026-04-02) — Initial release
- FastAPI server với 5 endpoint cơ bản
- Voice cloning + voice design
- UI tiếng Việt cho 4 ngôn ngữ

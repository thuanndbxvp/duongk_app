# 🎙️ HƯỚNG DẪN TRIỂN KHAI & VẬN HÀNH TOÀN DIỆN OMNIVOICE STUDIO (AI86)

> **MỤC ĐÍCH**: Đây là cẩm nang kỹ thuật chi tiết nhất dành cho **Developer** hoặc **AI Coding Assistant** để triển khai, vận hành, kiểm thử, tích hợp và khắc phục sự cố hệ thống **OmniVoice Studio (`voice.ai86.click`)**.

---

## 1. 🏗️ Tổng Quan Kiến Trúc (System Architecture)

Hệ thống OmniVoice Studio hoạt động theo mô hình **Hybrid Microservices**:

```
[ Người dùng / Trình duyệt / Desktop App ]
                     │
                     │  (HTTPS: https://voice.ai86.click)
                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│             CPU VPS: REVERSE PROXY & GATEWAY (Docker Compose)               │
│                                                                             │
│  ├── Caddy Web Server (Tự động cấp chứng chỉ SSL HTTPS Let's Encrypt)       │
│  └── Container `omnivoice` (FastAPI Python 3.11, Port 8088):               │
│        ├── Giao diện Web Studio (HTML5 / Vanilla CSS / Modern JS)           │
│        ├── Quản lý danh mục giọng (`voice_registry.json`)                   │
│        ├── Lưu trữ file âm thanh mẫu (`voices/` - Mounted Persistent Disk)  │
│        └── Điều phối request gọi Modal Serverless GPU                       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (Modal Python SDK Client / gRPC)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 MODAL.COM SERVERLESS GPU (ai-dubbing-pipeline)              │
│                                                                             │
│  ├── 🌟 VieNeu-TTS v3 Turbo: Chuyên xử lý tiếng Việt chuẩn, tự nhiên         │
│  ├── 📻 OmniVoice Core: Chuyên Voice Design đa ngôn ngữ                     │
│  ├── 🎬 SRT Dubbing Engine: Ghép giọng khớp timecode phụ đề `.srt`          │
│  └── 💾 Modal Volume (`ai-models-cache`): Lưu trữ weights model & cache     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 📂 Cấu Trúc Mã Nguồn & Thư Mục Dữ Liệu

| Đường dẫn tệp / thư mục | Vai trò & Nhiệm vụ |
|---|---|
| `apps/omnivoice/app/main.py` | FastAPI server: API endpoints `/v1/tts`, `/v1/catalog`, `/v1/voices`, `/v1/dubbing`, `/api/upload-ref`. |
| `apps/omnivoice/app/templates/index.html` | Toàn bộ giao diện Web Studio (Tabs: TTS Studio, Voice Cloning, SRT Dubbing, Voice Design). |
| `apps/omnivoice/voice_registry.json` | Danh bạ lưu toàn bộ thông tin giọng hệ thống và giọng người dùng đã clone. |
| `apps/omnivoice/voices/` | Thư mục chứa các file âm thanh mẫu tham chiếu (.wav, .mp3) dùng để nhân bản giọng. |
| `modal_functions/dubbing_pipeline.py` | Toàn bộ code chạy trên Modal GPU (load model VieNeu, OmniVoice, xử lý audio). |
| `docker-compose.prod.yml` | Cấu hình Docker Compose trên VPS (có volume mount bảo toàn dữ liệu). |

---

## 3. 🚀 Quy Trình Triển Khai (Step-by-Step Deployment)

### PHẦN A: Triển Khai GPU Pipeline lên Modal.com

Mỗi khi chỉnh sửa code trong file `modal_functions/dubbing_pipeline.py` hoặc cập nhật model:

1. **Mở PowerShell tại máy dev (`D:\appDK`)**:
   ```powershell
   # Thiết lập UTF-8 để không bị lỗi ký tự tiếng Việt
   $env:PYTHONUTF8=1
   ```

2. **Đăng nhập Modal (chỉ cần làm lần đầu)**:
   ```powershell
   modal setup
   ```

3. **Deploy ứng dụng Modal**:
   ```powershell
   modal deploy modal_functions/dubbing_pipeline.py
   ```
   > ⏱️ *Modal sẽ tự động build image, nạp weights vào Volume `ai-models-cache` và cấp phát GPU T4/A10G khi có request.*

---

### PHẦN B: Triển Khai Web Gateway lên CPU VPS (`voice.ai86.click`)

Mỗi khi cập nhật giao diện `index.html`, thêm endpoint trong `main.py`, hoặc chỉnh sửa cấu hình Docker:

1. **Bước 1: Commit và Push code lên GitHub**:
   ```powershell
   git add .
   git commit -m "feat(omnivoice): mô tả cập nhật"
   git push origin main
   ```

2. **Bước 2: Chạy lệnh Go-Live 1-Click**:
   ```powershell
   python update.py omnivoice
   ```
   > 💡 *Script `update.py` sẽ tự động SSH vào VPS (`202.92.7.227`), chạy `git pull`, rebuild container `omnivoice` và khởi động lại dịch vụ trong vòng 10 giây.*

---

## 4. 🎛️ Các Tính Năng & Cách Vận Hành

### 1. Studio Text-to-Speech (TTS)
* **2 Lõi Engine**:
  * **🌟 VieNeu-TTS v3 Turbo (Khuyên dùng)**: Phát âm tiếng Việt chuẩn xác, ngắt nghỉ tự nhiên. Hỗ trợ 3 thẻ cảm xúc: `[cười]`, `[thở dài]`, `[hắng giọng]`.
  * **📻 OmniVoice**: Hỗ trợ đa ngôn ngữ và tạo giọng bằng câu mô tả văn bản (Voice Design).
* **Tốc độ đọc**: Tuỳ chỉnh từ `0.5x` đến `2.0x`.

### 2. Nhân bản giọng nói (Zero-Shot Voice Cloning)
* **Cách thực hiện**:
  1. Vào tab **"👤 Nhân bản giọng"**.
  2. Tải lên file âm thanh mẫu rõ tiếng (khoảng 5 - 15 giây, định dạng `.wav` hoặc `.mp3`).
  3. Đặt Tên hiển thị và Voice ID (hệ thống tự động gợi ý).
  4. Nhấn **"🚀 Bắt đầu nhân bản & Lưu"**.
* **Đặc tính dữ liệu**: Giọng được lưu vĩnh viễn vào `voice_registry.json` và thư mục `voices/` trên ổ cứng VPS. Người dùng F5 hoặc restart container đều không bị mất.

### 3. Lồng tiếng phụ đề (SRT Dubbing)
* **Cách thực hiện**:
  1. Vào tab **"🎬 Lồng tiếng SRT"**.
  2. Tải lên file `.srt` (phụ đề đã chuẩn hóa mốc thời gian).
  3. Chọn Giọng đọc và Engine mong muốn.
  4. Nhấn **"⚡ Bắt đầu lồng tiếng"** ➔ Hệ thống sẽ tự động ghép từng câu khớp chính xác với timecode của video.

---

## 5. 🔌 Danh Sách REST API Dành Cho Tích Hợp Ngoài

Hệ thống cung cấp sẵn các API chuẩn RESTful cho Web / Mobile / Desktop Client kết nối:

### 1. `GET /v1/catalog` — Lấy danh mục giọng
```bash
curl -s https://voice.ai86.click/v1/catalog
```

### 2. `POST /v1/tts` — Sinh giọng đọc (Direct Stream)
```bash
curl -X POST https://voice.ai86.click/v1/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Xin chào, đây là giọng đọc thử nghiệm từ hệ thống AI86.",
    "voice_id": "ban_mai",
    "engine": "vieneu",
    "speed": 1.0
  }' \
  --output test_speech.wav
```

### 3. `POST /api/upload-ref` — Tải file mẫu lên server
```bash
curl -X POST https://voice.ai86.click/api/upload-ref \
  -F "file=@/path/to/voice_sample.wav"
```

### 4. `POST /v1/voices` — Đăng ký giọng clone mới
```bash
curl -X POST https://voice.ai86.click/v1/voices \
  -H "Content-Type: application/json" \
  -d '{
    "id": "giong_chu_sau",
    "type": "clone",
    "ref_audio_file": "voice_sample.wav",
    "display_name": "Chú Sáu Miền Tây",
    "language": "vi"
  }'
```

---

## 6. 🩺 Hướng Dẫn Xử Lý Sự Cố (Troubleshooting Playbook)

### 🔴 Sự cố 1: Lỗi "TorchCodec is required for load_with_torchcodec"
* **Nguyên nhân**: Bản `torchaudio` v2.9+ trên Modal mặc định tìm `torchcodec` khi load audio.
* **Cách xử lý**: Đảm bảo `modal_functions/dubbing_pipeline.py` đã cài `torchcodec` trong Image definition và có patch fallback sử dụng `soundfile`.

### 🔴 Sự cố 2: Giọng clone bị mất sau khi khởi động lại VPS
* **Nguyên nhân**: Quên mount volume cho container `omnivoice`.
* **Cách xử lý**: Kiểm tra file `docker-compose.prod.yml` phải có cấu hình:
  ```yaml
  volumes:
    - ./apps/omnivoice/voices:/app/voices
    - ./apps/omnivoice/voice_registry.json:/app/voice_registry.json
  ```

### 🔴 Sự cố 3: Giọng nói bị lặp từ / nói lắp (Hallucination)
* **Nguyên nhân**: Khóa cố định seed (`torch.manual_seed`) trong vòng lặp sinh autoregressive.
* **Cách xử lý**: Để seed ngẫu nhiên cho mỗi lần sinh giọng clone để đảm bảo ngữ điệu tự nhiên.

### 🔴 Sự cố 4: Modal báo lỗi Timeout (vượt quá 300s)
* **Cách xử lý**: Tăng tham số `timeout=1200` (20 phút) trong decorator `@app.function` của hàm `dub_srt` trên Modal.

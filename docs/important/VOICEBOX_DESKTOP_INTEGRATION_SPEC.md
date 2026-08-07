# 📋 TÀI LIỆU KỸ THUẬT: TÍCH HỢP VOICEBOX DESKTOP APP VỚI HẠ TẦNG MODAL.COM & AI86
### (CHẾ ĐỘ THUẦN LOCAL STORAGE & DIRECT STREAMING — KHÔNG CẦN CLOUD R2)

> **MỤC TIÊU**: Hướng dẫn kỹ thuật chi tiết dành cho **AI Coding Assistant** hoặc **Developer** để đóng gói / tinh chỉnh ứng dụng Desktop **Voicebox (Tauri / Rust)** kết nối trực tiếp với hạ tầng **Serverless GPU (Modal.com)** và **API Gateway (`voice.ai86.click`)** đang chạy sẵn của hệ sinh thái AI86.
>
> 💡 *Mô hình*: **Hybrid Desktop-First (Client siêu nhẹ ~25MB, lưu trữ 100% Local Disk + Cloud GPU Modal siêu tốc qua Direct Bytes Stream)**.

---

## 1. 🏗️ Tổng Quan Kiến Trúc (Architecture Overview)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DESKTOP CLIENT (Tauri + Rust + UI)                    │
│  - Lưu trữ 100% trên Local Disk (File mẫu, Project Timeline, Audio sinh ra)   │
│  - Phím tắt toàn hệ thống (Global Hotkey Dictation: Ctrl+Space / Cmd+Space)  │
│  - Multi-track Timeline Studio (Stories DAW)                                 │
│  - Bộ chọn Engine (VieNeu-TTS v3 Turbo / OmniVoice) & Voice Catalog        │
│  - Quản lý API Key người dùng (ai86.click Token)                            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (HTTPS REST API / Direct Binary Stream WAV)
                                       │ 🚀 KHÔNG CẦN QUA CLOUDFLARE R2
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                GATEWAY & REGISTRY SERVER (https://voice.ai86.click)          │
│  - Cung cấp Catalog giọng nói (System + Cloned Voices)                      │
│  - Tiếp nhận Text + Parameters, chuyển tiếp tức thì sang Modal GPU          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (Modal Python SDK Client)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MODAL.COM SERVERLESS GPU (ai-dubbing-pipeline)           │
│  ├── 🌟 synthesize_vieneu (VieNeu-TTS v3 Turbo: Tiếng Việt tự nhiên)        │
│  ├── 📻 synthesize_voice  (OmniVoice: Voice Design đa ngôn ngữ)             │
│  ├── ⚡ cache_voice_prompt (Tính toán Prompt Vector cho Clone Voice)         │
│  └── 🎬 dub_srt           (Lồng tiếng phụ đề SRT chuyên nghiệp)             │
│                                                                             │
│  👉 Trả trực tiếp Raw WAV Bytes trong RAM về Gateway -> Stream về Desktop   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 📂 Cơ Chế Lưu Trữ & Quản Lý File Thuần Local (Local Storage Strategy)

Ứng dụng Desktop **Voicebox** sẽ hoạt động theo chuẩn **Local-First**, toàn bộ dữ liệu lưu trữ trực tiếp trên ổ cứng người dùng:

| Loại Dữ Liệu | Vị trí lưu trữ trên máy người dùng (Local Disk) | Mục đích |
|---|---|---|
| **Audio Cache** | `%APPDATA%/voicebox-ai86/cache/` *(Win)* hoặc `~/Library/Caches/voicebox-ai86/` *(Mac)* | Lưu file `.wav` tạm thời nhận từ Modal để phát tức thì trên timeline. |
| **Voice Clone Samples** | `%APPDATA%/voicebox-ai86/clones/` | Lưu các file âm thanh mẫu (.wav, .mp3) mà người dùng thu âm hoặc import. |
| **Stories / Projects** | `%APPDATA%/voicebox-ai86/projects/` | Lưu file dự án kịch bản, các track âm thanh, marker timeline. |
| **Local Settings** | `%APPDATA%/voicebox-ai86/config.json` | Lưu API Key, hotkey tuỳ chỉnh, engine mặc định (`vieneu`). |

---

## 3. 🔌 Các Thông Số Hạ Tầng Dùng Chung (Existing Infrastructure Parameters)

Dưới đây là các thông số hạ tầng đang hoạt động mà Desktop App sẽ kết nối:

### A. Domain & API Endpoints
* **Voice Studio Gateway Base URL**: `https://voice.ai86.click`
* **Main API Base URL**: `https://api.ai86.click`

### B. Modal.com Serverless Pipeline
* **Modal App Name**: `ai-dubbing-pipeline`
* **Các hàm Remote Function trên Modal**:
  1. `synthesize_vieneu`:
     - **Tham số**: `text` (str), `reference_audio_url` (str | None), `voice_preset` (str | None), `speed` (float = 1.0), `denoise` (bool = True).
  2. `synthesize_voice`:
     - **Tham số**: `text` (str), `reference_audio_url` (str | None), `reference_prompt_url` (str | None), `instruct` (str | None), `speed` (float = 1.0).
  3. `cache_voice_prompt`:
     - **Tham số**: `reference_audio_url` (str), `output_key` (str).
  4. `dub_srt`:
     - **Tham số**: `srt_content` (str), `voice_id` (str), `reference_audio_url` (str | None), `merge_mode` (str = "native"), `engine` (str = "vieneu").

---

## 4. 📡 Chi Tiết API Specs Dành Cho Desktop Client

Desktop App gọi các endpoint REST tiêu chuẩn sau của Gateway `https://voice.ai86.click`:

### 1. Lấy danh sách giọng đọc (Catalog)
* **Method**: `GET`
* **Path**: `https://voice.ai86.click/v1/catalog`
* **Response**:
```json
{
  "count": 8,
  "voices": [
    { "id": "ban_mai", "type": "clone", "display_name": "Ban Mai (Nữ miền Bắc)", "language": "vi" },
    { "id": "lan_trinh", "type": "clone", "display_name": "Lan Trinh (Nữ miền Nam)", "language": "vi" },
    { "id": "minhquan_vb", "type": "clone", "display_name": "Minh Quân (Nam miền Bắc)", "language": "vi" },
    { "id": "thao_trinh", "type": "clone", "display_name": "Thảo Trinh (Nữ miền Nam)", "language": "vi" }
  ]
}
```

---

### 2. Sinh giọng đọc Text-to-Speech (TTS) — Direct Stream
* **Method**: `POST`
* **Path**: `https://voice.ai86.click/v1/tts`
* **Headers**: `Content-Type: application/json`
* **Body**:
```json
{
  "text": "Xin chào, đây là giọng đọc từ ứng dụng Voicebox kết nối hệ thống AI86.",
  "voice_id": "ban_mai",
  "engine": "vieneu",
  "emotion": "normal",
  "speed": 1.0
}
```
* **Ghi chú về `engine`**:
  * `"vieneu"` *(Khuyên dùng cho Tiếng Việt)*: Sử dụng VieNeu-TTS v3 Turbo. Hỗ trợ các thẻ cảm xúc: `[cười]`, `[thở dài]`, `[hắng giọng]`.
  * `"omnivoice"`: Sử dụng OmniVoice (Hỗ trợ Voice Design tự do qua trường `"instruct"`).
* **Response**: **Direct Binary Stream** của file âm thanh (`Content-Type: audio/wav`).
* **Desktop Client Handling**: Đọc response stream thành mảng `Uint8Array`, lưu thẳng vào file `%APPDATA%/voicebox-ai86/cache/<hash>.wav` và nạp vào player timeline để phát ngay lập tức.

---

### 3. Tải file âm thanh mẫu để nhân bản giọng (Upload Reference Audio)
* **Method**: `POST`
* **Path**: `https://voice.ai86.click/api/upload-ref`
* **Headers**: `Content-Type: multipart/form-data`
* **Form Data**:
  * `file`: File âm thanh mẫu (.wav, .mp3, .flac) từ 5 - 15 giây.
* **Response**:
```json
{
  "success": true,
  "filename": "giong_mau_bac_ba_1723019283.wav",
  "original_name": "giong_mau_bac_ba.wav",
  "size": 524288
}
```

---

### 4. Đăng ký & Lưu Voice Clone vào hệ thống
* **Method**: `POST`
* **Path**: `https://voice.ai86.click/v1/voices`
* **Headers**: `Content-Type: application/json`
* **Body**:
```json
{
  "id": "bac_ba_ke_chuyen",
  "type": "clone",
  "ref_audio_file": "giong_mau_bac_ba_1723019283.wav",
  "display_name": "Bác Ba Kể Chuyện",
  "language": "vi"
}
```

---

### 5. Lồng tiếng theo file phụ đề (.SRT Dubbing)
* **Method**: `POST`
* **Path**: `https://voice.ai86.click/v1/dubbing`
* **Headers**: `Content-Type: multipart/form-data`
* **Form Data**:
  * `srt_file`: File phụ đề `.srt`.
  * `voice_id`: ID giọng cần đọc (ví dụ: `ban_mai`).
  * `engine`: `"vieneu"` hoặc `"omnivoice"`.
  * `merge_mode`: `"native"` (khớp thời gian chuẩn).
  * `speed`: `1.0`.
* **Response**: Direct Binary Stream file audio hoàn chỉnh đã khớp timecode (`audio/wav`).

---

## 5. 🛠️ Hướng Dẫn Từng Bước Cho AI Coding (Implementation Guide)

Khi giao repo `https://github.com/jamiepine/voicebox` cho AI Coding, chỉ định các bước thực hiện như sau:

### Bước 1: Điều chỉnh Tầng Network Client trong Voicebox
* Mặc định Voicebox gửi request tới `http://127.0.0.1:17493` (local Python backend).
* Chỉnh sửa cấu hình Provider / Base URL trong file cấu hình client (TypeScript/Rust) trỏ sang:
  ```typescript
  export const AI86_VOICE_API = "https://voice.ai86.click";
  ```
* Bỏ qua việc tự khởi động local Python server nếu chạy ở chế độ **Cloud Engine (Modal)**.

### Bước 2: Tích hợp Engine Selector & Emotion Chips
* Trên giao diện Studio của Voicebox, thêm bộ chọn Engine:
  * **🌟 VieNeu-TTS v3 Turbo (Tiếng Việt tốt nhất)** ➔ Gửi `"engine": "vieneu"`.
  * **📻 OmniVoice (Voice Design đa ngôn ngữ)** ➔ Gửi `"engine": "omnivoice"`.
* Bổ sung các Emotion Chips nhanh cho VieNeu-TTS: `[cười]`, `[thở dài]`, `[hắng giọng]`.

### Bước 3: Ghi nhận Binary Stream vào Local Disk Cache
* Khi Desktop nhận được stream WAV từ `https://voice.ai86.click/v1/tts`, lưu tạm vào thư mục cache của OS:
  ```typescript
  import { appCacheDir, join } from '@tauri-apps/api/path';
  import { writeBinaryFile } from '@tauri-apps/plugin-fs';

  async function saveTtsStreamToLocal(blob: Blob, filename: string): Promise<string> {
      const cacheDir = await appCacheDir();
      const filePath = await join(cacheDir, filename);
      const arrayBuffer = await blob.arrayBuffer();
      await writeBinaryFile(filePath, new Uint8Array(arrayBuffer));
      return filePath;
  }
  ```
* Trả file path cục bộ cho timeline DAW (Stories multi-track) để người dùng cắt ghép mượt mà, không bị delay mạng khi preview.

### Bước 4: Đóng gói Installer Desktop Siêu Nhẹ
* Sử dụng lệnh build tiêu chuẩn của Tauri:
  ```bash
  npm run tauri build
  ```
* Kết quả thu được file installer `.msi` / `.exe` (Windows) hoặc `.dmg` (macOS) có dung lượng chỉ khoảng **15 - 30 MB**, hoàn toàn không chứa model AI nặng và không phụ thuộc Cloudflare R2.

---

## 6. ✅ Checklist Kiểm Thử (Verification Criteria)

1. [ ] Khởi động Desktop App không báo lỗi thiếu PyTorch/CUDA local hay lỗi R2 key.
2. [ ] Gọi `GET https://voice.ai86.click/v1/catalog` tải danh sách giọng thành công.
3. [ ] Nhập văn bản tiếng Việt, bấm Generate -> Nhận stream WAV lưu về thư mục cache local và phát trong vòng **1-3 giây**.
4. [ ] Kéo thả file âm thanh mẫu để clone giọng -> Giọng mới xuất hiện ngay trên Desktop UI.
5. [ ] Đóng app, mở lại -> Danh sách giọng clone và dự án timeline vẫn tồn tại nguyên vẹn trên ổ cứng local.

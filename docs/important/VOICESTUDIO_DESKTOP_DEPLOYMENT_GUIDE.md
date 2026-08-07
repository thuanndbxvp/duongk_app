# 🎙️ HƯỚNG DẪN TRIỂN KHAI VOICESTUDIO (DESKTOP APP) KẾT NỐI MODAL GPU & GATEWAY AI86

> **DỰ ÁN**: Chuyển đổi mã nguồn mở [**debpalash/VoiceStudio**](https://github.com/debpalash/VoiceStudio) thành **Ứng dụng Desktop thương mại siêu nhẹ (~30 MB)**, kết nối trực tiếp với cụm **Serverless GPU (Modal.com)** và **Trạm soát vé / Gateway (`https://voice.ai86.click`)**.
>
> 🎯 **Mục tiêu**: Máy người dùng không cần GPU vẫn có thể: **Lồng tiếng video điện ảnh (Cinematic Dubbing)**, **Tách nhạc nền Demucs**, **Nhân bản giọng nói** và **Tạo sách nói hàng loạt**.

---

## 1. 🏗️ Tổng Quan Kiến Trúc (Hybrid Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DESKTOP CLIENT: VOICESTUDIO (Tauri v2 + React)                 │
│  - Giao diện: React + TypeScript + Tailwind (Trích xuất từ repo gốc)        │
│  - Lưu trữ: 100% trên Local Disk (File video, file audio, project, cache)   │
│  - Đăng nhập / Xác thực: Nhập API Key (`ai86_live_xxx`) trong Settings       │
│  - Các Studio: TTS Studio, Voice Cloning, Video Dubbing, Audiobook         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (1) HTTPS Request + Bearer Token
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 TRẠM SOÁT VÉ & GATEWAY (https://voice.ai86.click)           │
│                                                                             │
│  ├── 🔑 Xác thực API Key & Kiểm tra số dư Credits (Supabase DB)            │
│  ├── 🛑 Nếu hết tiền -> Báo HTTP 402 "Nạp thêm Credits"                    │
│  ├── ⚡ Nếu đủ tiền -> Gọi sang Modal GPU bằng Secret nội bộ               │
│  └── 💳 Sau khi Modal xong -> Trừ Credits, Ghi Log & Stream Audio về App   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (Modal Python SDK Client / gRPC)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 MODAL.COM SERVERLESS GPU (ai-dubbing-pipeline)              │
│                                                                             │
│  ├── 🌟 synthesize_vieneu: VieNeu-TTS v3 Turbo (Tiếng Việt siêu tự nhiên)   │
│  ├── 📻 synthesize_voice:  OmniVoice Core (Voice Design & Đa ngôn ngữ)      │
│  ├── 🎬 dub_srt:           Lồng tiếng khớp timecode phụ đề                  │
│  └── 🎵 demucs_separate:   Tách giọng nói & giữ nguyên nhạc nền video       │
│                                                                             │
│  👉 Trả trực tiếp Binary Stream WAV / MP3 về Gateway                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 📂 Cấu Trúc Thư Mục Dữ Liệu Trên Máy Người Dùng (Local Storage)

VoiceStudio sẽ hoạt động theo mô hình **Local-First**, không cần Cloud R2:

| Loại Dữ Liệu | Đường Dẫn Local Disk (Windows) | Đường Dẫn Local Disk (macOS) |
|---|---|---|
| **Audio & Video Cache** | `%APPDATA%/VoiceStudio/cache/` | `~/Library/Caches/VoiceStudio/` |
| **Voice Clone Samples** | `%APPDATA%/VoiceStudio/clones/` | `~/Library/Application Support/VoiceStudio/clones/` |
| **Dubbing Projects** | `%APPDATA%/VoiceStudio/projects/` | `~/Library/Application Support/VoiceStudio/projects/` |
| **User Settings** | `%APPDATA%/VoiceStudio/settings.json` | `~/Library/Application Support/VoiceStudio/settings.json` |

---

## 3. 🛠️ Hướng Dẫn Từng Bước Dành Cho AI Coding (Implementation Steps)

### BƯỚC 1: Clone Repo & Loại Bỏ Python Sidecar Local
Repo gốc của `VoiceStudio` có chứa một sidecar Python để chạy AI local. Chúng ta sẽ **loại bỏ sidecar này** để app giảm dung lượng từ 15GB xuống còn 30MB:

1. **Clone repository**:
   ```bash
   git clone https://github.com/debpalash/VoiceStudio.git
   cd VoiceStudio
   ```
2. **Cấu hình `src-tauri/tauri.conf.json`**:
   * Xóa bỏ cấu hình bundle Python sidecar trong mục `bundle > externalBin`.
   * Cấp quyền mạng cho Tauri gọi đến domain API của chúng ta:
     ```json
     {
       "app": {
         "security": {
           "csp": "default-src 'self'; connect-src 'self' https://voice.ai86.click https://api.ai86.click"
         }
       }
     }
     ```

---

### BƯỚC 2: Cấu Hình API Client & Trạm Soát Vé (Gateway Middleware)

Tạo một file quản lý API Client tập trung tại `src/services/apiClient.ts`:

```typescript
// src/services/apiClient.ts
export const GATEWAY_URL = "https://voice.ai86.click";

export async function getApiKey(): Promise<string> {
  const settings = localStorage.getItem("ai86_settings");
  return settings ? JSON.parse(settings).apiKey || "" : "";
}

export async function requestTTS(payload: {
  text: string;
  voice_id: string;
  engine: "vieneu" | "omnivoice";
  speed?: number;
}): Promise<Blob> {
  const apiKey = await getApiKey();
  if (!apiKey) {
    throw new Error("Vui lòng nhập AI86 API Key trong phần Cài đặt!");
  }

  const response = await fetch(`${GATEWAY_URL}/v1/tts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      text: payload.text,
      voice_id: payload.voice_id,
      engine: payload.engine,
      speed: payload.speed || 1.0
    })
  });

  if (response.status === 402) {
    throw new Error("Tài khoản của bạn đã hết Credits. Vui lòng nạp thêm tại ai86.click!");
  }

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Lỗi tạo giọng nói");
  }

  return await response.blob();
}
```

---

### BƯỚC 3: Tích Hợp Engine Selector & VieNeu-TTS Tiếng Việt

Trong giao diện TTS Studio (`src/components/TtsEditor.tsx`), thêm bộ chọn Engine:

1. **Thêm Option chọn Engine**:
   * `🌟 VieNeu-TTS v3 Turbo` (Mặc định cho Tiếng Việt) ➔ Gửi `"engine": "vieneu"`.
   * `📻 OmniVoice Core` (Hỗ trợ Voice Design) ➔ Gửi `"engine": "omnivoice"`.

2. **Thêm Emotion Chips nhanh cho VieNeu-TTS**:
   * Nút chèn `[cười]`
   * Nút chèn `[thở dài]`
   * Nút chèn `[hắng giọng]`

---

### BƯỚC 4: Tích Hợp Tính Năng Lồng Tiếng Phim (Cinematic Video Dubbing)

Trong tab Dubbing Studio:
1. Người dùng chọn file Video trên máy tính (.mp4, .mkv).
2. Tauri trích xuất track audio ra file `.wav` nhẹ ngay trên máy (bằng FFmpeg local siêu tốc).
3. Gửi file audio + phụ đề `.srt` lên Gateway:
   ```typescript
   export async function requestDubbing(srtFile: File, voiceId: string): Promise<Blob> {
     const apiKey = await getApiKey();
     const formData = new FormData();
     formData.append("srt_file", srtFile);
     formData.append("voice_id", voiceId);
     formData.append("engine", "vieneu");
     formData.append("merge_mode", "native");

     const res = await fetch(`${GATEWAY_URL}/v1/dubbing`, {
       method: "POST",
       headers: { "Authorization": `Bearer ${apiKey}` },
       body: formData
     });

     if (res.status === 402) throw new Error("Hết credits lồng tiếng!");
     return await res.blob();
   }
   ```
4. Khi nhận được audio stream từ Modal, Desktop App tự động ghép track audio mới vào Video gốc của người dùng mà **không cần upload cả video nặng 1-2GB lên cloud**.

---

### BƯỚC 5: Đóng Gói Bộ Cài Desktop Siêu Nhẹ (Tauri Build)

1. Cài đặt các dependencies:
   ```bash
   npm install
   ```
2. Build ứng dụng Desktop (Windows / macOS / Linux):
   ```bash
   npm run tauri build
   ```
3. **Kết quả**:
   * File cài đặt **`.msi` / `.exe` (Windows)** hoặc **`.dmg` (macOS)** được tạo ra trong `src-tauri/target/release/bundle/`.
   * Dung lượng bộ cài: **Chỉ ~25 MB - 35 MB**.

---

## 4. 💰 Cách Thức Hoạt Động Của Trạm Soát Vé (Billing Logic)

Trạm soát vé trên Gateway (`https://voice.ai86.click`) sẽ xử lý thanh toán như sau:

| Thao tác người dùng | Cách tính phí (Credits) | Xử lý khi hết tiền |
|---|---|---|
| **Tạo TTS Tiếng Việt (VieNeu)** | 1 ký tự = 1 Credit | Báo lỗi `402 Payment Required`, hướng dẫn link nạp tiền. |
| **Nhân bản giọng (Voice Clone)** | 10.000 Credits / 1 giọng clone | Chặn không cho gọi Modal tính prompt vector. |
| **Lồng tiếng phim (SRT Dubbing)** | 5.000 Credits / 1 phút video | Khóa (Hold) tạm thời, nếu Modal lỗi thì hoàn lại 100%. |

---

## 5. ✅ Checklist Nghiệm Thu Sản Phẩm

1. [ ] Cài đặt file `.msi` / `.exe` trên máy tính sạch (không có Python/CUDA) chạy mượt 100%.
2. [ ] Mở Settings nhập API Key -> Kiểm tra số dư Credits hiển thị chính xác.
3. [ ] Bấm sinh giọng TTS -> Nhận file âm thanh trong vòng **1 - 3 giây**.
4. [ ] Tải video và file phụ đề `.srt` vào Dubbing Studio -> Xuất ra video đã lồng tiếng khớp khẩu hình.
5. [ ] Người dùng hết Credits -> App chặn lại thông minh và không làm tốn chi phí GPU Modal.

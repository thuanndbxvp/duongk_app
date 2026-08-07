# 🛡️ KIẾN TRÚC KỸ THUẬT: "TRẠM SOÁT VÉ" (API GATEWAY, AUTHENTICATION & BILLING SYSTEM)

> **MỤC ĐÍCH**: Đây là tài liệu thiết kế kỹ thuật chi tiết nhất dành cho **AI Coding Assistant** hoặc **Developer** để triển khai hệ thống **Xác thực (Authentication)**, **Quản lý API Key**, **Kiểm tra số dư (Pre-flight Quota Check)**, **Trừ tiền tự động (Billing & Ledger)** và **Bảo vệ hạ tầng GPU Modal.com** chống lạm dụng/xài chùa.
>
> 💡 *Tận dụng 100% hạ tầng sẵn có*: **FastAPI (CPU VPS `202.92.7.227`) + Supabase DB + Redis Cache + Modal Serverless GPU**.

---

## 1. 🏗️ Tổng Quan Kiến Trúc Phân Tầng (Architectural Layout)

### ⚠️ Nguyên tắc an ninh bất di bất dịch:
* **Tuyệt đối KHÔNG BAO GIỜ cấp URL hoặc Token Modal cho Client (Desktop/Web/Extension)**.
* Toàn bộ Client chỉ được phép giao tiếp với **Trạm soát vé** (`https://voice.ai86.click` hoặc `https://api.ai86.click`) thông qua **API Key cá nhân** (`Authorization: Bearer ai86_live_...`).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER (Desktop App / Web Browser)                 │
│  - Người dùng lưu API Key: `ai86_live_9f8a7b6c5d4e...`                     │
│  - Gửi Request: Text / File phụ đề / File mẫu âm thanh                      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (1) HTTPS Request + Bearer API Key
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│        TRẠM SOÁT VÉ (API GATEWAY & BILLING MIDDLEWARE TRÊN CPU VPS)         │
│                                                                             │
│  ├── [Gác cổng 1] Redis Rate Limiter: Chống spam DDoS (Tối đa 10 req/s)     │
│  ├── [Gác cổng 2] Auth Resolver: Hash SHA-256 Key -> Truy vấn User Supabase │
│  ├── [Gác cổng 3] Pre-flight Pricing: Tính toán số ký tự / số phút audio    │
│  │                 └─► Đủ tiền? -> Tạm khóa (Hold) số Credits trong DB      │
│  │                 └─► Thiếu tiền? -> Trả ngay HTTP 402 (Không gọi Modal)  │
│  │                                                                          │
│  ├── [Điều phối] Gọi Modal GPU bằng Private Credentials nội bộ              │
│  │                                                                          │
│  └── [Hậu kiểm & Ghi sổ]                                                    │
│        ├─► Thành công: Commit trừ tiền vĩnh viễn + Ghi Log Usage             │
│        └─► Thất bại (Timeout/Lỗi Model): Tự động Rollback hoàn 100% tiền    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (2) Modal Private Call (gRPC)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   MODAL.COM SERVERLESS GPU (Được bảo vệ 100%)               │
│  - VieNeu-TTS v3 Turbo / OmniVoice / Demucs Dubbing                         │
│  - Trả về Raw Binary WAV Bytes trong RAM                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 🗄️ Cấu Trúc Bảng Dữ Liệu Trong Supabase (Database Schema)

Tận dụng và mở rộng hệ thống migration sẵn có trong `supabase/migrations/`:

### A. Bảng Quản lý API Key (`user_api_keys`)
```sql
CREATE TABLE IF NOT EXISTS user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT 'Default Desktop Key',
    key_hash TEXT NOT NULL UNIQUE,       -- Lưu dạng SHA-256 hash của API key
    key_prefix TEXT NOT NULL,           -- Ví dụ: ai86_live_9f8a... (để hiển thị trên UI)
    rate_limit_per_minute INT DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_user_api_keys_hash ON user_api_keys(key_hash);
```

### B. Cấu hình bảng Bảng giá dịch vụ (`credit_pricing`)
```sql
-- Cập nhật bảng credit_pricing cho mảng Voice & Dubbing
INSERT INTO credit_pricing (job_type, credits, description) VALUES
  ('tts_char', 1, '1 Credit cho mỗi 1 ký tự text (VieNeu/OmniVoice)'),
  ('voice_clone_create', 10000, 'Phí tạo và phân tích Prompt Vector cho 1 giọng Clone'),
  ('dubbing_per_second', 100, '100 Credits cho mỗi giây lồng tiếng phụ đề SRT'),
  ('demucs_vocal_split', 5000, 'Phí tách nhạc nền video bằng AI Demucs')
ON CONFLICT (job_type) DO UPDATE SET credits = EXCLUDED.credits;
```

### C. Hàm Atomic Deduct / Hold Credits (Chống Race Condition đa luồng)
```sql
CREATE OR REPLACE FUNCTION hold_tts_credits(
    p_user_id UUID,
    p_required_credits INT,
    p_job_type TEXT,
    p_metadata JSONB DEFAULT '{}'::jsonb
) RETURNS TABLE(success BOOLEAN, transaction_id UUID, current_balance INT) AS $$
DECLARE
    v_balance INT;
    v_tx_id UUID;
BEGIN
    -- Khóa hàng (Row Lock) của user để tránh 2 request trừ tiền cùng lúc
    SELECT credits INTO v_balance FROM users WHERE id = p_user_id FOR UPDATE;
    
    IF v_balance IS NULL THEN
        RETURN QUERY SELECT FALSE, NULL::UUID, 0;
        RETURN;
    END IF;
    
    IF v_balance < p_required_credits THEN
        RETURN QUERY SELECT FALSE, NULL::UUID, v_balance;
        RETURN;
    END IF;
    
    -- Tạm trừ số credits
    UPDATE users SET credits = credits - p_required_credits, updated_at = NOW() WHERE id = p_user_id;
    
    -- Ghi nhận giao dịch trạng thái 'hold'
    INSERT INTO credit_transactions (user_id, amount, job_type, metadata)
    VALUES (p_user_id, -p_required_credits, p_job_type, jsonb_build_object('status', 'held', 'meta', p_metadata))
    RETURNING id INTO v_tx_id;
    
    RETURN QUERY SELECT TRUE, v_tx_id, (v_balance - p_required_credits);
END;
$$ LANGUAGE plpgsql VOLATILE;
```

---

## 3. 🛡️ Quy Trình 6 Bước Xử Lý Tại Trạm Soát Vé (FastAPI Middleware Lifecycle)

Khi có bất kỳ request nào gửi đến `POST /v1/tts` hoặc `POST /v1/dubbing`:

```
[Request Đến] 
     │
     ▼
[Bước 1: Parse Token] ──► Không có Token? ──────────────────────► [Trả về 401 Unauthorized]
     │
     ▼
[Bước 2: Redis Cache] ──► Token hợp lệ? (Cache 5 phút) ─────────► [Lấy User ID & Số dư]
     │
     ▼
[Bước 3: Tính Tiền]   ──► Độ dài text = 1200 ký tự -> Cần 1200 Credits
     │
     ▼
[Bước 4: Hold Credit] ──► Số dư < 1200? ────────────────────────► [Trả về 402 Insufficient Funds]
     │                    └─► Không bao giờ kích hoạt Modal GPU!
     ▼
[Bước 5: Chạy Modal]  ──► Gọi Modal GPU (T4/A10G)
     │
     ├── ❌ Modal Lỗi/Timeout ───────────────────────────────────► [Rollback trả lại 1200 Credits + Báo 500]
     │
     ▼
[Bước 6: Ghi Log & Stream]
     ├── Commit vĩnh viễn giao dịch vào bảng `credit_transactions`
     ├── Ghi 1 dòng vào `api_usage_logs`
     └── Stream Binary Audio WAV về cho Client
```

---

## 4. 💻 Mã Nguồn Triển Khai Mẫu Trên FastAPI (`apps/omnivoice/app/main.py`)

Dưới đây là đoạn code hoàn chỉnh mà AI Coding sẽ nhúng vào Backend FastAPI:

```python
# apps/omnivoice/app/auth_billing.py
import hashlib
import json
import time
from fastapi import Header, HTTPException, Depends
from supabase import create_client, Client
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

async def verify_billing_access(
    authorization: str = Header(None),
    text: str = "",
    job_type: str = "tts_char"
) -> dict:
    """
    Dependency gác cổng: Xác thực API Key và Hold Credits trước khi chạy GPU.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"error": "MISSING_API_KEY", "message": "Vui lòng cung cấp API Key qua Header 'Authorization: Bearer <key>'"}
        )
    
    raw_key = authorization.replace("Bearer ", "").strip()
    key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
    
    # 1. Truy vấn Key trong Supabase DB
    res = supabase.table("user_api_keys").select("user_id, is_active").eq("key_hash", key_hash).execute()
    if not res.data or not res.data[0]["is_active"]:
        raise HTTPException(
            status_code=403,
            detail={"error": "INVALID_API_KEY", "message": "API Key không hợp lệ hoặc đã bị khóa"}
        )
    
    user_id = res.data[0]["user_id"]
    
    # 2. Tính số Credits cần thiết
    char_count = len(text)
    required_credits = max(char_count * 1, 10)  # Tối thiểu 10 credits / 1 request
    
    # 3. Gọi Stored Procedure để Atomic Hold Credits
    rpc_res = supabase.rpc("hold_tts_credits", {
        "p_user_id": user_id,
        "p_required_credits": required_credits,
        "p_job_type": job_type,
        "p_metadata": {"char_count": char_count}
    }).execute()
    
    hold_data = rpc_res.data[0] if rpc_res.data else None
    
    if not hold_data or not hold_data["success"]:
        current_bal = hold_data["current_balance"] if hold_data else 0
        raise HTTPException(
            status_code=402,
            detail={
                "error": "INSUFFICIENT_CREDITS",
                "message": f"Số dư không đủ. Bạn cần {required_credits} Credits nhưng chỉ còn {current_bal} Credits.",
                "current_balance": current_bal,
                "required_credits": required_credits,
                "topup_url": "https://ai86.click/billing"
            }
        )
    
    return {
        "user_id": user_id,
        "tx_id": hold_data["transaction_id"],
        "required_credits": required_credits,
        "char_count": char_count
    }
```

### Cách áp dụng vào endpoint TTS (`/v1/tts`):
```python
from fastapi.responses import StreamingResponse
import io

@app.post("/v1/tts")
async def handle_tts(
    req: TTSRequest,
    auth_ctx: dict = Depends(verify_billing_access)
):
    start_time = time.time()
    tx_id = auth_ctx["tx_id"]
    user_id = auth_ctx["user_id"]
    
    try:
        # Gọi sang Modal GPU (Đã được đảm bảo khách hàng có đủ tiền)
        wav_bytes = call_modal_synthesize(
            text=req.text,
            voice_id=req.voice_id,
            engine=req.engine,
            speed=req.speed
        )
        
        # Cập nhật log giao dịch thành công (Commit)
        supabase.table("credit_transactions").update({
            "metadata": json.dumps({"status": "completed", "latency_ms": int((time.time() - start_time) * 1000)})
        }).eq("id", tx_id).execute()
        
        return StreamingResponse(io.BytesIO(wav_bytes), media_type="audio/wav")
        
    except Exception as e:
        # ⚠️ NẾU MODAL LỖI: Tự động hoàn trả tiền lại cho khách hàng ngay lập tức!
        supabase.rpc("release_credits", {"p_user_id": user_id, "p_job_id": tx_id}).execute()
        raise HTTPException(status_code=500, detail=f"Lỗi suy luận GPU: {str(e)}")
```

---

## 5. 🖥️ Giao Diện Tạo & Quản Lý API Key Trên Web (`ai86.click`)

Trên Web Dashboard của khách hàng (`apps/web`):

1. **Mục Cài Đặt ➔ "API Keys & Desktop App"**:
   * Nút **"Tạo API Key Mới"** -> Sinh chuỗi ngẫu nhiên dạng `ai86_live_xxxxxxxxxxxxxxxx`.
   * Hiển thị key 1 lần duy nhất để người dùng copy vào ứng dụng Desktop.
   * Hiển thị số dư **Credits còn lại** và lịch sử sử dụng thời gian thực.
2. **Cơ chế Nạp Tiền (Top-up)**:
   * Quét mã VietQR / MoMo / Thẻ tín dụng.
   * Tiền vào tài khoản ➔ Webhook cộng `credits` trong Supabase ➔ Desktop App tự động cập nhật số dư tức thì.

---

## 6. ✅ Checklist Nghiệm Thu Trạm Soát Vé

1. [ ] Gửi request không có Header `Authorization` ➔ Bị chặn ngay bằng mã `HTTP 401`.
2. [ ] Gửi request với API Key giả / đã bị khóa ➔ Bị chặn ngay bằng mã `HTTP 403`.
3. [ ] Tài khoản còn 500 Credits, gửi đoạn văn 2.000 ký tự ➔ Bị chặn bằng mã `HTTP 402`, **không có bất kỳ request nào gửi sang Modal GPU**.
4. [ ] Tài khoản còn 10.000 Credits, gửi đoạn văn 500 ký tự ➔ Nhận file âm thanh sau 1.5s, số dư trong database giảm chính xác còn 9.500 Credits.
5. [ ] Giả lập ngắt mạng Modal GPU ➔ Hệ thống tự động hoàn tiền 100% về tài khoản của khách, không bị trừ oan.

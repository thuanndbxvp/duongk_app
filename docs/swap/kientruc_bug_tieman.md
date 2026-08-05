# Phân tích Điểm mờ (Ambiguities) trong Tài liệu Kiến trúc YouTube AI SaaS

Sau khi review kỹ tài liệu, tôi thấy đây là một PRD tốt về mặt cấu trúc, nhưng còn **nhiều điểm mờ nghiêm trọng** sẽ khiến AI Coding tạo ra code sai hoặc không chạy được. Tôi sẽ phân tích theo 3 lớp: **(A) Điểm mờ chung**, **(B) Điểm mờ theo Module**, **(C) Chiến lược 2 Phase + mô hình "API do bạn cung cấp, tính theo Credit"**.

---

## A. NHỮNG ĐIỂM MỜ CHUNG (CROSS-CUTTING CONCERNS)

### A1. Thiếu Contract giữa FastAPI ↔ Next.js ↔ Celery
Tài liệu nói "Next.js API routes to communicate with the FastAPI backend" nhưng **không định nghĩa**:
- Next.js gọi FastAPI trực tiếp từ client, hay proxy qua Next.js API Route (BFF pattern)?
- Auth token flow: Supabase JWT được verify ở đâu? (Next.js middleware? FastAPI dependency?)
- CORS policy, domain deployment (mono-repo hay tách repo?)

👉 **AI Coding sẽ tự chọn 1 trong 3 cách và có thể sai** — cần chốt: **BFF pattern** (Next.js → FastAPI) hay **Direct call** (Client → FastAPI với Supabase JWT trong header).

### A2. Cơ chế Job Queue & Realtime chưa rõ
- Bạn có 2 lựa chọn trong tài liệu: **Polling** (`GET /api/research/{job_id}`) VÀ **WebSocket** (Module 2.3). Chọn cả hai sẽ làm code phức tạp gấp đôi.
- Chưa định nghĩa **bảng `jobs`** trong DB để track trạng thái Celery task (task_id, status, progress, result, error).
- Chưa nói rõ dùng **Redis Pub/Sub** hay **Supabase Realtime** để push update.

👉 Đề xuất: **Dùng Supabase Realtime** subscribe vào bảng `content_projects.status` → tránh phải build WebSocket riêng.

### A3. Schema DB thiếu các bảng quan trọng
Các bảng bị bỏ sót:
- `credit_transactions` — Log mọi lần cộng/trừ credit (bắt buộc cho audit & billing).
- `jobs` — Track Celery task async.
- `api_usage_logs` — Log mỗi lần gọi OpenAI/Gemini/Pexels để tính chi phí thực (rất quan trọng với mô hình "bạn cung cấp API").
- `subscriptions` / `plans` — Nếu có gói cước Free/Pro/Agency thì cần bảng riêng, không nhúng vào `users`.

### A4. Row Level Security (RLS) chưa có policy cụ thể
Bạn nói "bật RLS" nhưng không viết policy → AI sẽ **quên hoặc viết policy sai** → lộ data giữa các user. Cần yêu cầu tạo file `supabase/policies.sql` với policy mẫu cho từng bảng.

### A5. Không có Error Handling Contract
- Format lỗi trả về từ FastAPI (dùng `HTTPException` chuẩn nào?).
- Retry policy khi OpenAI/Pexels fail.
- Rollback credit khi job fail giữa chừng (cực kỳ quan trọng!).

### A6. Thiếu Rate Limiting & Abuse Protection
Với mô hình bạn trả tiền API, một user malicious có thể spam → đốt credit của bạn. Cần: rate limit theo user + hard cap theo giờ/ngày.

### A7. Cấu trúc thư mục Monorepo chưa định nghĩa
AI Coding sẽ tự tạo cấu trúc lung tung. Nên chốt ví dụ:
```
/apps
  /web         (Next.js)
  /api         (FastAPI)
  /worker      (Celery)
/packages
  /shared-types  (Pydantic ↔ TypeScript)
/supabase
  /migrations
  /policies
```

### A8. Thiếu Type Contract giữa Frontend và Backend
`scenes_data` là JSONB — nhưng schema JSON không được declare bằng **Pydantic (Python) + Zod (TS)** đồng bộ → sẽ vỡ khi refactor.

---

## B. ĐIỂM MỜ THEO TỪNG MODULE

### 🟨 Module 1 — Nghiên cứu Ngách

| # | Điểm mờ | Câu hỏi cần trả lời |
|---|---------|---------------------|
| B1.1 | **Ngưỡng "5M views"** | Con số này lấy từ đâu? Có phải config được không? Có khác nhau theo ngách (Kids vs Finance) không? |
| B1.2 | **YouTube Data API quota** | Quota chỉ 10,000 units/ngày. Lấy top 100 kênh sẽ tiêu tốn bao nhiêu unit? Có cache 24h không? |
| B1.3 | **Cách "mở rộng để lấy Top 100 kênh"** | Là lấy từ 50-100 video ban đầu? Hay crawl thêm? Thuật toán rank theo Sub hay theo View? |
| B1.4 | **"Video liên quan trong 30 ngày qua"** | Search theo `relevance` hay `viewCount`? `publishedAfter` chính xác thế nào (UTC hay theo user timezone)? |
| B1.5 | **Prompt sinh 5 tiêu đề** | Chưa có prompt template, ràng buộc format output (JSON schema)? |
| B1.6 | **Xử lý keyword tiếng Việt** | Có dịch sang tiếng Anh trước không? YouTube search behavior khác nhau theo `regionCode`/`relevanceLanguage`. |

---

### 🟨 Module 2 — Content Engine

#### Phase 2.1 — Style DNA Extraction

| # | Điểm mờ |
|---|---------|
| B2.1.1 | **Lấy transcript bằng cách nào?** `youtube-transcript-api`? `yt-dlp`? Hay Whisper để STT? — Mỗi cách có chi phí/độ tin cậy khác nhau. |
| B2.1.2 | **"3-5 video viral nhất" định nghĩa thế nào?** — Cao view nhất? View/Sub ratio? Trong bao lâu? |
| B2.1.3 | **Schema chuẩn của `style_dna_profile` JSON** — Tài liệu chỉ nói chung chung "cấu trúc Hook, nhịp điệu, từ vựng". Cần **JSON Schema cụ thể** (VD: `{hook_patterns: [], vocabulary_tier: "casual/formal", sentence_length_avg: 12, ...}`). Không có schema → LLM trả về format khác nhau mỗi lần → không dùng được. |
| B2.1.4 | **Nếu kênh không có transcript** (video không caption)? Fallback? |

#### Phase 2.2 — Script Generation

| # | Điểm mờ |
|---|---------|
| B2.2.1 | **Độ dài script mong muốn?** Video 5 phút hay 15 phút? Tokens giới hạn? |
| B2.2.2 | **"Quy trình từng phần" là gì?** Chunking? Outline → Draft → Refine? |
| B2.2.3 | **User có được edit script trước khi phân rã cảnh không?** Nếu có → cần state machine: `draft → user_reviewed → scene_breakdown`. |
| B2.2.4 | **Ngôn ngữ đầu ra** — tiếng Việt hay đa ngôn ngữ? |

#### Phase 2.3 — Scene Breakdown *(quan trọng nhất)*

| # | Điểm mờ |
|---|---------|
| B2.3.1 | **`estimated_duration` tính bằng cách nào?** LLM đoán, hay tính bằng số từ / WPM (words-per-minute)? |
| B2.3.2 | **Nếu Pexels/Pixabay không có kết quả cho `search_keyword`?** Fallback (thử keyword khác, dùng image thay video, dùng AI image gen)? |
| B2.3.3 | **License / Attribution** — Pexels yêu cầu attribution cho một số case. Có track không? |
| B2.3.4 | **Xử lý phim/ảnh trùng lặp giữa các scene?** — Nếu 3 scene cùng keyword "person thinking" → sẽ trả về cùng 1 video → chán. Cần dedup. |
| B2.3.5 | **Aspect ratio & resolution** — Video YouTube 16:9 hay Shorts 9:16? Ảnh hưởng đến filter API. |
| B2.3.6 | **User có được swap footage không?** Nếu có → cần endpoint `PATCH /projects/{id}/scenes/{scene_id}/asset`. |

---

## C. VẤN ĐỀ CHIẾN LƯỢC — CHIA PHASE & MÔ HÌNH "BẠN CUNG CẤP API"

### C1. Rủi ro khi làm Phase 1 (Module 1-2) trước Phase 2 (Module 0)

Bạn định làm **Module 1-2 trước, Module 0 (User) sau**. Đây là quyết định **có rủi ro cao** nếu không kỷ luật:

**✅ Cái được:**
- Test được core value proposition (Nghiên cứu + Kịch bản) nhanh.
- Không tốn effort làm auth/billing khi chưa chắc feature hoạt động.

**❌ Cái mất (nếu không xử lý ngay từ đầu):**
1. **Toàn bộ query DB sẽ không có `user_id`** → khi thêm auth sau sẽ phải refactor rất nhiều query & RLS policy.
2. **Không có credit system** → không test được logic trừ tiền, tới Phase 2 mới thêm sẽ vỡ các flow đã build.
3. **Không có rate limit** → nếu deploy demo → user spam → bạn cháy ví API.

### 🎯 Đề xuất: **"Module 0-Lite" trong Phase 1**

Thay vì bỏ hẳn Module 0 sang Phase 2, hãy làm một **skeleton tối thiểu ngay Phase 1**:

| Có ngay Phase 1 (Lite) | Đẩy sang Phase 2 (Full) |
|------------------------|--------------------------|
| Bảng `users` với `user_id`, `credits` (mock giá trị lớn) | Đăng ký/Đăng nhập UI hoàn chỉnh |
| Supabase Auth **email/password cơ bản** | OAuth Google/Facebook |
| RLS policy đầy đủ | Trang Profile, đổi password |
| Middleware trừ credit (đã hoạt động) | Trang mua credit, Stripe |
| Bảng `credit_transactions` | Gói Free/Pro/Agency với limit khác nhau |
| Hard-coded 1 tier "internal_test" | UI quản lý subscription |

👉 Như vậy Phase 2 chỉ là **build UI + billing gateway**, không phải refactor logic.

---

### C2. Mô hình "Bạn cung cấp API, user trả bằng Credit" — ĐIỂM MỜ LỚN NHẤT

Đây là mô hình phức tạp cần thiết kế cực kỹ. Các câu hỏi bạn **phải** trả lời trước khi code:

#### C2.1 — Định giá Credit (Pricing Model)
- **1 credit = bao nhiêu USD?** (VD: 1 credit = $0.01)
- **Bảng giá cho từng action:**
  ```
  - Nghiên cứu ngách (Module 1): ? credits
  - Tạo Style DNA (Phase 2.1): ? credits (đắt vì gọi LLM nhiều lần)
  - Sinh Script (Phase 2.2): ? credits (dựa trên độ dài?)
  - Phân rã cảnh + Pexels (Phase 2.3): ? credits (dựa trên số scenes?)
  ```
- **Fix price hay dynamic price?** — Nếu dynamic (theo token thực tế) thì user không predict được. Nếu fix thì bạn có thể lỗ khi user dùng nhiều.

#### C2.2 — Chi phí API cần track
Bạn cần biết **giá vốn** cho mỗi action. Ví dụ 1 script:
| API | Chi phí ước tính |
|-----|------------------|
| GPT-4o input 5k tokens + output 3k tokens | ~$0.045 |
| YouTube Data API | Free (nhưng có quota) |
| Pexels API | Free (nhưng có rate limit) |
| Whisper (nếu STT transcript) | $0.006/phút |

👉 **Bảng `api_usage_logs`** phải log: `user_id`, `action_type`, `provider`, `input_tokens`, `output_tokens`, `cost_usd`, `credits_charged`, `margin`.

#### C2.3 — Chống lạm dụng (Abuse)
- **Concurrent job limit** — 1 user chỉ được chạy tối đa N job đồng thời (VD: Free=1, Pro=3).
- **Daily cap** — Kể cả còn credit, mỗi user tối đa X action/ngày.
- **Sanity check** — Nếu user request tạo script "1 triệu từ" → chặn.
- **BYOK Option (Bring Your Own Key)** — Nên có tùy chọn cho power user nhập key của họ để không tốn credit của bạn → giảm rủi ro cho bạn.

#### C2.4 — Idempotency & Rollback Credit
- **Trừ credit trước hay sau khi job thành công?**
  - Trừ trước → an toàn cho bạn nhưng phải rollback khi fail.
  - Trừ sau → dễ bị race condition (user spam nhiều job cùng lúc khi hết credit).
- 👉 Đề xuất: **Hold-then-Commit pattern** (giống thanh toán thẻ):
  ```
  1. HOLD credit khi tạo job (status = pending)
  2. COMMIT khi job xong (status = completed)
  3. RELEASE (hoàn lại) khi job fail
  ```

#### C2.5 — Bảo mật API Key của bạn
- Key OpenAI/Gemini phải lưu trong **environment variable** hoặc **Supabase Vault** — không được commit code.
- Chỉ **Celery Worker** được đọc key, **FastAPI web layer** không được có key trong runtime → nếu bị RCE cũng không leak key.

---

## D. TÓM TẮT — CHECKLIST TRƯỚC KHI ĐƯA CHO AI CODING

Trước khi paste tài liệu vào Cursor/Cline, tôi khuyên bạn **bổ sung/quyết định 12 điểm** sau:

1. ✅ Chốt **BFF pattern hay Direct call** giữa Next.js ↔ FastAPI.
2. ✅ Bổ sung 4 bảng: `jobs`, `credit_transactions`, `api_usage_logs`, `plans`.
3. ✅ Viết **JSON Schema cụ thể** cho `style_dna_profile` và `scenes_data`.
4. ✅ Viết **RLS policy mẫu** cho ít nhất 1 bảng làm template.
5. ✅ Quyết định **Polling vs Supabase Realtime** (nên chọn Realtime).
6. ✅ Định nghĩa **cấu trúc monorepo** rõ ràng.
7. ✅ **Prompt template** cho từng LLM task (Style DNA, Script Gen, Scene Breakdown) — kèm few-shot examples.
8. ✅ Bảng **giá credit chi tiết** cho từng action + logic Hold-Commit-Release.
9. ✅ **Rate limit rules** (per user, per hour, per action).
10. ✅ Chốt **strategy transcript** (youtube-transcript-api, yt-dlp, hay Whisper).
11. ✅ Chốt **fallback strategy** cho Pexels (no result → thử keyword khác → dùng ảnh → AI gen).
12. ✅ **Module 0-Lite** trong Phase 1 (auth cơ bản + credit skeleton + RLS) thay vì bỏ hẳn.

---

## 🚀 Bước tiếp theo — Bạn muốn tôi làm gì?

Tôi có thể giúp bạn một trong các việc sau (chọn 1 để tôi làm sâu):

**(1)** Viết lại toàn bộ tài liệu PRD bản v2 với đầy đủ các điểm mờ đã được giải quyết → thành file `.md` sẵn sàng đưa vào Cursor.

**(2)** Chỉ tập trung thiết kế **Credit & Billing System** (bảng DB, hold-commit-release flow, pricing sheet, log format).

**(3)** Viết **JSON Schema chi tiết** cho `style_dna_profile` + `scenes_data` + Prompt template cho 3 LLM task.

**(4)** Thiết kế **Phase 1 Roadmap** chi tiết: các sprint, các file cần tạo trước, thứ tự implement để tối ưu cho AI Coding chạy tuần tự.

Bạn muốn tôi đi sâu vào hướng nào?
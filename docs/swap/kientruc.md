Dưới đây là **Tài liệu Đặc tả Kiến trúc và Yêu cầu Kỹ thuật (Technical PRD & Architecture Spec)** được thiết kế chuẩn mực, tối ưu hóa để bạn đưa trực tiếp vào các công cụ AI Coding (như Cursor, GitHub Copilot, hoặc Cline) nhằm thực thi việc tạo mã nguồn (code generation).

Tài liệu này tập trung vào Module 0 (Quản lý User), Module 1 (Nghiên cứu), và Module 2 (Kịch bản & Phân rã cảnh), sử dụng stack công nghệ hiện đại.

---

# TÀI LIỆU ĐẶC TẢ KIẾN TRÚC HỆ THỐNG YOUTUBE AI SAAS

## 1. TỔNG QUAN HỆ THỐNG (TECH STACK)

* **Frontend:** Next.js (App Router), React, TailwindCSS, Shadcn UI.
* **Backend (REST API):** Python (FastAPI).
* **Background Workers:** Celery + Redis (Xử lý các tác vụ AI và cào dữ liệu mất thời gian).
* **Database & Auth:** Supabase (PostgreSQL + Row Level Security).
* **AI Models:** OpenAI (GPT-4o) hoặc Google Gemini (1.5 Pro) cho logic phân tích; API bên thứ 3 (Pexels/Pixabay) cho Footage.

---

## 2. THIẾT KẾ CƠ SỞ DỮ LIỆU (DATABASE SCHEMA - SUPABASE)

Hệ thống cần các bảng (Tables) chính sau. Cần bật RLS (Row Level Security) để `user_id` chỉ truy cập được dữ liệu của chính họ.

### `users` (Quản lý Người dùng)

* `id` (UUID, Primary Key): Link với Supabase Auth.
* `email` (String).
* `credits` (Integer): Số dư tín dụng để sử dụng tính năng.
* `tier` (String): Gói cước (Free, Pro, Agency).
* `max_assistants` (Integer): Giới hạn số "Trợ lý kênh" được tạo.
* `created_at` (Timestamp).

### `channel_assistants` (Trợ lý Kênh - Lưu trữ Style DNA)

* `id` (UUID, Primary Key).
* `user_id` (UUID, Foreign Key).
* `name` (String): Tên gợi nhớ (VD: Trợ lý phong cách Kurzgesagt).
* `seed_channel_url` (String): Link kênh kim chỉ nam.
* `style_dna_profile` (JSONB): Lưu kết quả bóc tách văn phong, từ vựng, cấu trúc hook.
* `created_at` (Timestamp).

### `market_research` (Module 1 - Lưu lịch sử nghiên cứu ngách)

* `id` (UUID, Primary Key).
* `user_id` (UUID, Foreign Key).
* `keyword` (String): Từ khóa tìm kiếm.
* `total_monthly_views` (BigInt): Tổng view 30 ngày (Dùng để validate > 5.7M).
* `is_viable` (Boolean): Đạt chuẩn hay không.
* `top_competitors` (JSONB): Mảng chứa Top 100 kênh đối thủ (channel_id, title, subs).
* `suggested_titles` (JSONB): Mảng các ý tưởng tiêu đề.

### `content_projects` (Module 2 - Quản lý Kịch bản & Tài nguyên)

* `id` (UUID, Primary Key).
* `user_id` (UUID, Foreign Key).
* `assistant_id` (UUID, Foreign Key): Trợ lý kênh được sử dụng.
* `topic` (String): Chủ đề video.
* `raw_script` (Text): Kịch bản thô do AI sinh ra.
* `scenes_data` (JSONB): **Cấu trúc lõi của phân rã cảnh** (Lưu mảng JSON chứa chi tiết từng cảnh, xem phần dưới).
* `status` (String): `draft`, `generating`, `completed`.

---

## 3. MÔ TẢ TÍNH NĂNG VÀ LUỒNG NGHIỆP VỤ (BUSINESS LOGIC)

### Module 0: Quản lý Người dùng & Tín dụng (User & Billing Management)

* **Tính năng:**
* Xác thực (Đăng ký/Đăng nhập) qua Supabase Auth.
* Hệ thống trừ Credit (Credit Deduction System): Mỗi hành động nặng (Nghiên cứu ngách, Sinh kịch bản) sẽ gọi một middleware trừ 1 lượng credit nhất định.
* Quản lý giới hạn Trợ lý: Kiểm tra biến `max_assistants` trước khi cho phép tạo mới.



### Module 1: Định vị & Khai phá (Discovery & Validation)

* **Input (Từ UI):** `keyword` (Từ khóa ngách).
* **Xử lý (FastAPI + Worker):**
1. Gọi YouTube Data API v3 tìm 50-100 video liên quan trong 30 ngày qua.
2. Tính tổng `total_monthly_views`. Nếu `< 5M`, trả về thông báo lỗi "Thị trường quá nhỏ".
3. Nếu hợp lệ, tiếp tục trích xuất `channelId` và mở rộng để lấy danh sách Top 100 kênh (xếp theo lượng Sub giảm dần).
4. Gọi LLM đọc tiêu đề của 100 video top đầu và sinh ra 5 ý tưởng Tiêu đề (Titles) mới có tỷ lệ click cao.


* **Output (Lưu DB & Trả về UI):** Bảng báo cáo dung lượng thị trường và danh sách đối thủ. Trừ Credit.

### Module 2: Động cơ Nội dung & Phân rã Cảnh (Content Engine)

Module này được chia làm 3 Phase hoạt động theo cơ chế hàng đợi (Queue) để tránh timeout.

**Phase 2.1: Tạo Trợ lý Kênh (Style DNA Extraction)**

* **Input:** URL kênh kim chỉ nam.
* **Xử lý:** Worker lấy Transcript của 3-5 video viral nhất của kênh này -> Gửi qua LLM với Prompt "Anti-AI Slop" để bóc tách cấu trúc Hook, nhịp điệu, bộ từ vựng -> Lưu thành `style_dna_profile` dạng JSON.

**Phase 2.2: Sinh Kịch Bản (Script Generation)**

* **Input:** Chủ đề (`topic`) + Trợ lý đã chọn (`assistant_id`).
* **Xử lý:** LLM nhận chủ đề và viết kịch bản hoàn chỉnh (hoặc theo quy trình từng phần) tuân thủ tuyệt đối văn phong trong `style_dna_profile`. Lưu vào `raw_script`.

**Phase 2.3: Phân rã Cảnh & Đạo diễn Tài nguyên (Scene Breakdown & Asset Fetching)** *[TÍNH NĂNG QUAN TRỌNG NHẤT]*

* **Input:** `raw_script` vừa tạo.
* **Xử lý:**
1. **Scene Breakdown (LLM Task):** Ép LLM đọc kịch bản và phân rã thành một mảng JSON chuẩn xác. Cấu trúc yêu cầu LLM trả về:
```json
[
  {
    "scene_id": 1,
    "text": "Bạn có bao giờ tự hỏi...",
    "estimated_duration": 4.5,
    "visual_context": "Hình ảnh một người đang suy nghĩ, phong cách cinematic",
    "search_keyword": "person thinking cinematic",
    "asset_type_needed": "video" // hoặc "image"
  },
  // ... scenes tiếp theo
]

```


2. **Asset Fetching (Worker Task):** Vòng lặp code Python chạy qua từng object trong mảng JSON trên.
* Lấy `search_keyword` gọi API của Pexels hoặc Pixabay.
* Bóc tách URL của file MP4 (hoặc JPG) tốt nhất.
* Cập nhật mảng JSON, thêm trường `"download_url": "https://..."` vào từng scene.




* **Output (Lưu DB):** Cập nhật trường `scenes_data` trong bảng `content_projects`. Gửi thông báo WebSocket hoặc trả API cho Frontend báo trạng thái "Hoàn thành".

---

## 4. DANH SÁCH API ENDPOINTS YÊU CẦU (CHO AI CODING)

Dưới đây là các route FastAPI mà AI cần tạo:

**Auth & Users:**

* `GET /api/users/me` -> Lấy thông tin user, số dư credit.

**Module 1 (Nghiên cứu):**

* `POST /api/research/validate` -> Body: `{keyword: string}`. Khởi tạo Job trong Celery.
* `GET /api/research/{job_id}` -> Polling trạng thái nghiên cứu.
* `GET /api/research/history` -> Lấy lịch sử các ngách đã nghiên cứu.

**Module 2 (Trợ lý & Kịch bản):**

* `POST /api/assistants/create` -> Body: `{seed_channel_url: string, name: string}`. Trích xuất DNA.
* `GET /api/assistants` -> Lấy danh sách trợ lý của User.
* `POST /api/projects/generate` -> Body: `{topic: string, assistant_id: UUID}`. Chạy ngầm Phase 2.2 và Phase 2.3.
* `GET /api/projects/{project_id}` -> Trả về kịch bản và chuỗi JSON `scenes_data` đã kèm link B-roll.

---

## 5. HƯỚNG DẪN PROMPT CHO AI CODING (DÀNH CHO BẠN)

Khi đưa tài liệu này vào Cursor hoặc Cline, bạn hãy đính kèm prompt sau:

> "You are an Expert Full-Stack Developer. Review this Architectural Spec for a YouTube AI SaaS. Start by creating the Supabase SQL schema migrations. Then, initialize the FastAPI backend structure, specifically focusing on the Celery Worker logic for Module 2 Phase 2.3 (Scene Breakdown and Pexels API fetching). Finally, set up the Next.js API routes to communicate with the FastAPI backend."
> "You are an Expert Full-Stack Developer. Review this Architectural Spec for a YouTube AI SaaS. Start by creating the Supabase SQL schema migrations. Then, initialize the FastAPI backend structure, specifically focusing on the Celery Worker logic for Module 2 Phase 2.3 (Scene Breakdown and Pexels API fetching). Finally, set up the Next.js API routes to communicate with the FastAPI backend."

## Phần 2 — PLAN XÂY DỰNG ADMIN PANEL

Sau khi hoàn thành Phần 1, viết một plan riêng cho việc xây admin panel (cpanel).

### 2.1 Phạm vi tính năng (MVP)
Admin panel MVP phải có 4 nhóm chức năng:

**A. Quản trị User**
- List user (search, filter theo tier/status/created_at)
- Xem chi tiết 1 user (profile, credit history, job history, project count)
- Thêm user thủ công (dành cho invite/comp account)
- Sửa user (đổi tier, đổi email, đổi max_assistants)
- Xoá user (soft delete với cascade cleanup)
- Ban/unban user
- Impersonate user (để debug)

**B. Quản trị Credit**
- Tăng/giảm credit của bất kỳ user nào (với ghi log lý do bắt buộc)
- Xem credit ledger toàn hệ thống
- Xem transaction history theo user
- Thống kê: tổng credit đã issue / đã spent / đang hold / refunded
- Export CSV credit report theo khoảng thời gian
- Cấu hình pricing table (bao nhiêu credit cho mỗi action)

**C. Quản trị API Key của các AI provider**
- CRUD API keys cho: OpenAI, Gemini, Cohere, ElevenLabs, YouTube Data API (multi-key rotation), Pexels, Pixabay, Unsplash, Modal, Supabase service role, R2 credentials
- Rotate key an toàn (không mất downtime)
- Test connectivity cho từng key
- Monitor usage/cost theo key (tích hợp với `api_usage_logs`)
- Alert khi 1 key gần hết quota/budget

**D. Cấu hình Routing Service (quan trọng nhất)**
Đây là tính năng cho phép admin quyết định **mỗi nghiệp vụ sẽ được xử lý ở đâu**. Ví dụ với tác vụ "tách subtitle từ YouTube video":
- Option 1: gọi API bên thứ 3 (Supadata, Youtube-Transcript.io)
- Option 2: chạy local trên CPU VPS (youtube-transcript-api)
- Option 3: chạy trên GPU VPS (Whisper self-hosted)
- Option 4: chạy trên Modal.com serverless GPU

Yêu cầu:
- UI cho phép chọn primary provider + fallback chain cho mỗi nghiệp vụ
- Config được lưu trong bảng `service_routing_config` và hot-reload không cần restart worker
- Có toggle "enabled/disabled" cho từng provider
- Có priority/weight nếu muốn load-balance
- Preview cost estimate cho mỗi lựa chọn

Danh sách nghiệp vụ cần routing config:
- Transcript extraction
- LLM (script generation, mimic rules, persona)
- Embedding (VN vs EN)
- Emotion classifier
- FFmpeg render
- TTS
- Thumbnail vision analysis
- Footage search (Pexels/Pixabay/Unsplash)

### 2.2 Kiến trúc kỹ thuật của Admin Panel

Đề xuất và giải thích lựa chọn:
- Standalone Next.js app (`apps/admin`) hay tích hợp vào app chính (`/admin` route với role check)?
- Auth: dùng chung Supabase Auth với role `admin` trong `users.role`? Hay tách RBAC riêng với bảng `admin_users`?
- Database: dùng chung schema hay tách schema `admin` riêng?
- Realtime: có cần realtime dashboard không?
- Audit log: log mọi hành động admin vào bảng `admin_audit_logs`

### 2.3 Database Schema cần thêm

Đề xuất SQL migration cho:
- `admin_users` hoặc thêm column `role` vào `users`
- `admin_audit_logs` (ai làm gì lúc nào)
- `service_routing_config` (routing rules per feature)
- `api_provider_keys` (encrypted API keys với version/rotation)
- `pricing_config` (credit price per action, có thể dynamic)

### 2.4 API Endpoints cho Admin

Liệt kê endpoint cụ thể:
Copy
GET /api/admin/users GET /api/admin/users/:id POST /api/admin/users PATCH /api/admin/users/:id DELETE /api/admin/users/:id POST /api/admin/users/:id/adjust-credit GET /api/admin/credit/ledger GET /api/admin/api-keys POST /api/admin/api-keys POST /api/admin/api-keys/:id/test GET /api/admin/routing-config PATCH /api/admin/routing-config/:feature GET /api/admin/audit-logs GET /api/admin/dashboard/stats

Copy(bổ sung thêm nếu cần)

### 2.5 Security Requirements
- Admin panel chỉ accessible từ IP whitelist hoặc VPN (config bằng env)
- Mọi endpoint admin bắt buộc verify role + 2FA (nếu có)
- Mọi mutation phải log vào `admin_audit_logs` với `admin_id`, `action`, `target_id`, `before`, `after`, `ip`, `user_agent`
- API keys phải encrypt at rest (dùng Supabase Vault hoặc AES-256 với master key riêng)
- Không log giá trị API key raw ra console/Sentry
- Rate limit riêng cho endpoint admin

### 2.6 UI/UX Guidelines
- Dùng shadcn/ui + TailwindCSS (đồng nhất với app chính)
- Sidebar navigation với các mục: Dashboard, Users, Credits, API Keys, Routing, Audit Logs, Settings
- Dashboard trang chủ có: card thống kê (MRR, active users, jobs today, credits spent), biểu đồ traffic 7 ngày, top errors
- Confirm dialog cho mọi destructive action
- Toast notification cho mọi mutation
- Dark mode default (admin quen dark)

### 2.7 Roadmap thực thi (Sprint plan)

Chia thành sprint 1 tuần:

**Sprint A1 — Foundation (1 tuần)**
- Schema migration (admin_users, audit_logs, routing_config, api_provider_keys, pricing_config)
- RBAC middleware ở FastAPI (`require_admin` decorator)
- Admin auth flow (Supabase Auth với role check + optional 2FA)
- Layout admin panel (sidebar, header, breadcrumb)
- Dashboard trang chủ với 4 card thống kê cơ bản

**Sprint A2 — User & Credit Management (1 tuần)**
- CRUD user
- Search/filter/pagination
- Impersonate user
- Adjust credit + audit log
- Credit ledger view
- Export CSV

**Sprint A3 — API Key Management (1 tuần)**
- CRUD API keys với encryption
- Test connectivity endpoint per provider
- Usage/cost dashboard theo key
- Alert khi budget gần cạn

**Sprint A4 — Service Routing Config (1 tuần)**
- Schema `service_routing_config`
- UI chọn provider primary + fallback chain
- Hot-reload trong worker (Redis pub/sub hoặc polling)
- Cost estimate preview
- A/B testing giữa các provider (optional)

**Sprint A5 — Polish & Extended features (1 tuần)**
- Audit log viewer với search
- Advanced analytics dashboard
- Backup/restore config
- Documentation cho admin

### 2.8 Rủi ro & Mitigation

Liệt kê rủi ro cụ thể và cách xử lý, ví dụ:
- Race condition khi 2 admin cùng edit routing config → dùng optimistic locking
- Admin nhấn xoá user nhầm → soft delete + recovery window 7 ngày
- API key leak qua audit log → mask value khi ghi log
- Panel bị brute force → rate limit + IP whitelist

**Output plan Phần 2 lưu vào file:** `docs/plans/admin_panel_plan.md`

---

## Quy tắc thực thi

1. **KHÔNG viết code trước khi hoàn thành Phần 1**. Phải khảo sát codebase trước, hiểu rõ hiện trạng.
2. **Mọi phân tích phải có bằng chứng cụ thể** (file path, line number, quote code).
3. **KHÔNG hallucinate**. Nếu không chắc chắn về file/function nào, phải mở file đó ra đọc, không đoán.
4. **Output 2 file markdown** đúng path đã yêu cầu, không paste raw vào chat.
5. Nếu phát hiện điểm mờ trong quá trình khảo sát cần user quyết định, dừng lại và hỏi trước khi tiếp tục.
6. Ngôn ngữ output: **Tiếng Việt** (headings + nội dung), code + tên biến giữ nguyên English.

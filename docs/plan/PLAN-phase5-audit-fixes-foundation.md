# Kế hoạch Triển khai (PLAN): phase5-audit-fixes-foundation

## 1. Mục tiêu (Objective)
- **Mô tả ngắn gọn:** Khắc phục 4 vấn đề chặn (blockers) từ audit Phần 1 và scaffold RBAC + UI shell cho Admin Panel. Phase này KHÔNG thêm tính năng nghiệp vụ admin nào — chỉ là nền tảng để Phase 6+ mở rộng.
- **Giá trị cốt lõi:**
  1. Loại bỏ race-condition tiềm ẩn trên credit hold (duplicate SQL function).
  2. Vá lỗ hổng RLS trên bảng `transcripts` (leaky hiện tại).
  3. Có RBAC dependency `require_admin` sẵn sàng dùng cho Phase 6+ (User/Credit mgmt).
  4. Có `/admin` route với middleware check role + layout shell.
  5. Audit log infrastructure (`admin_audit_logs` table + service) sẵn sàng.

## 2. Kiến trúc lựa chọn (Architecture)

### Pattern: Foundation-only (không feature)
```
Migration 0022:
  ├─ DROP FUNCTION hold_credits(UUID, UUID, INT)  -- (xóa signature cũ từ 0006)
  ├─ ALTER TABLE users ADD role, max_assistants, banned_at, banned_reason, deleted_at, last_sign_in_at
  ├─ CREATE TABLE admin_audit_logs
  ├─ CREATE FUNCTION admin_adjust_credits(...)
  └─ CREATE FUNCTION soft_delete_user(...)

Backend:
  apps/api/dependencies/admin.py
    └─ require_admin(user_id: str = Depends(get_supabase_user)) -> str
       - Query users.role; raise 403 nếu not in ('admin','super_admin')

  apps/api/services/audit.py
    ├─ SENSITIVE_KEYS = re.compile(r'(key|token|secret|password|api_key)', re.I)
    ├─ mask_value(obj: dict) -> dict  (deep-copy với mask)
    └─ async log_admin_action(admin_id, action, target_type, target_id, before, after, ip, ua, reason)

  apps/api/services/credit_manager.py (THÊM helper, KHÔNG đụng class hiện tại):
    └─ def get_user_role(user_id: str) -> str

Frontend:
  apps/web/middleware.ts  (NEW)
    ├─ Match '/admin/*' hoặc '/api/admin/*'
    ├─ getSession() từ @supabase/ssr createServerClient
    ├─ Nếu chưa login → redirect('/login?next=...')
    └─ Nếu user.role not in (admin, super_admin) → redirect('/403')

  apps/web/app/(admin)/layout.tsx (NEW)
    ├─ AdminShell component
    ├─ Sidebar 240px: 9 menu items (placeholder, chỉ Dashboard active)
    ├─ TopBar: admin email + role badge + signout button
    └─ <main>{children}</main>

  apps/web/app/(admin)/admin/page.tsx (NEW) - Dashboard placeholder
    └─ 4 stat cards với dữ liệu hard-code "—"
```

### Luồng dữ liệu (Data flow)
- Request `/admin/users` → Next.js middleware → check session → query `users.role` từ Supabase (service_role bypass RLS) → if admin pass → render AdminShell → fetch data from FastAPI `/api/admin/users` (Phase 6 sẽ viết).
- Audit mọi mutation: helper `log_admin_action()` INSERT row vào `admin_audit_logs` (service_role client).
- RBAC check ở FastAPI: mỗi route admin `@require_admin` → nếu không phải admin → 403.

## 3. Lý do chọn & Các phương án đã loại trừ (Alternatives)

### Phương án A — Thêm column `admin` boolean vào `users` (ĐÃ LOẠI)
- **Lý do loại:** Không scale được (chỉ true/false, không có super_admin). User phân tích audit report Phase 2 đã chọn column `role TEXT` với 3 giá trị.

### Phương án B — Tạo bảng `admin_users` riêng (ĐÃ LOẠI)
- **Lý do loại:** User chọn column `role` trong `users`. Phase 2 đã confirm. Lý do: giảm JOIN, đơn giản hơn cho RBAC check.

### Phương án C — Xóa hoàn toàn migration 0006 và viết lại 0020 (ĐÃ LOẠI)
- **Lý do loại:** Migration history là immutable — xóa 0006 sẽ break người đã apply. Tốt hơn: thêm DROP FUNCTION ở 0022 (cleanup forward-compatible).

### Phương án D — Dùng shadcn/ui cho admin shell (ĐÃ LOẢI)
- **Lý do loại:** Repo hiện KHÔNG có shadcn/ui — chỉ có Tailwind + glass design system. Thêm shadcn vào giữa chừng sẽ tăng bundle ~150KB. Phase này dùng Tailwind thuần với class `.glass`, `.gradient-bg` đã có sẵn.

### Lý do chọn phương án hiện tại
- **Compatibility:** Migration 0022 forward-compatible (chỉ ADD/DROP FUNCTION, không xóa data).
- **Performance:** Index trên `users.role WHERE deleted_at IS NULL` (partial index) nhanh cho RBAC check.
- **Maintainability:** Tách `admin` dependency thành file riêng, không pollute `auth.py` hiện tại.

## 4. Đánh giá rủi ro (Risk Assessment)

| # | Rủi ro | Mức | Giảm thiểu |
|---|--------|-----|------------|
| 1 | `DROP FUNCTION` ở 0022 sai tên → fail migration | Trung bình | Step 1 dùng `DROP FUNCTION IF EXISTS hold_credits(uuid, uuid, int)`. Test trên local trước. |
| 2 | Migration 0022 chạy sau 0021 nhưng DB local đã có 0021 → không thấy function 0006 (vì 0020 đã override) | Thấp | DROP FUNCTION IF EXISTS để idempotent. |
| 3 | `require_admin` query `users.role` mỗi request → N+1 query | Trung bình | Step 6: cache role 60s trong memory (dict per user_id). |
| 4 | Middleware Next.js chặn `/admin` nhưng admin click vào link từ email → loop redirect | Thấp | Step 8: nếu đã login + đúng role, pass-through. Nếu chưa login, redirect `/login?next=/admin/users`. |
| 5 | Audit log ghi IP/UA lỗi nếu behind proxy | Trung bình | Step 7: ưu tiên `X-Forwarded-For` header nếu có. |
| 6 | Default `role='user'` khi ALTER TABLE ADD COLUMN không set default → fail cho existing rows | **Cao** | Step 3: dùng `ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user'`. |

## 5. Dự kiến nỗi lực (Estimation)

| Metric | Value |
|--------|-------|
| **Estimated LOC** | ~350 lines (SQL: 200, Python: 80, TypeScript: 70) |
| **Timeline** | 12 steps MSEW, ước tính 4-6 giờ Tier 2 thực thi + self-test |
| **Files touched** | 4 mới (migration, 3 file Python/TS), 3 sửa (users.py helper, .env.example) |

## 6. Phụ thuộc giữa các Step
- Step 1 phải xong trước Step 4 (tránh conflict function signature).
- Step 3 phải xong trước Step 5, 6, 7 (cần column `role` tồn tại).
- Step 5 phải xong trước Step 6 (`require_admin` gọi `get_user_role`).
- Step 6-7 độc lập nhau.
- Step 8-10 là frontend, độc lập với backend steps 1-7.
- Step 11-12 là integration verify, phải cuối cùng.

# Kế hoạch Triển khai (PLAN): phase6-admin-user-credit

## 1. Mục tiêu (Objective)
- **Mô tả ngắn gọn:** Sprint A2 — User & Credit Management cho Admin Panel. 13 endpoint backend + 3 trang admin UI + sidebar update.
- **Giá trị cốt lõi:**
  1. Admin có data thật để test (Phase 1 đã có 7 endpoint user-facing, giờ admin đọc được).
  2. Adjust credit + ban user + soft delete + impersonate đều có audit log.
  3. Credit ledger toàn hệ thống + Export CSV cho finance team.

## 2. Kiến trúc lựa chọn (Architecture)

### Pattern: Layered CRUD với RBAC + audit
```
[Web admin UI] 
  → fetch /api/admin/users/[id]/adjust-credit (Next.js proxy)
    → FastAPI POST /api/admin/users/{id}/adjust-credit
      → Depends(require_admin) → verify role admin/super_admin
      → request.client.host in ADMIN_ALLOWED_IPS (optional, mock trong dev)
      → RPC admin_adjust_credits(p_admin_id, p_user_id, p_delta, p_reason)
      → log_admin_action('credit.adjust', before, after, reason)
      → return {new_balance, tx_id}
```

### Cấu trúc file
```
apps/api/routers/
  admin_users.py       (NEW)   - 9 endpoints user management
  admin_credit.py      (NEW)   - 4 endpoints credit ledger
  admin_pricing.py     (NEW)   - 2 endpoints pricing config

apps/web/app/(admin)/admin/
  users/
    page.tsx           (NEW)   - User list table
    [id]/
      page.tsx         (NEW)   - User detail tabs
  credits/
    page.tsx           (NEW)   - Ledger + stats

apps/web/app/api/admin/
  users/
    route.ts                              (NEW) - GET list + POST create
    [id]/route.ts                         (NEW) - GET one + PATCH
    [id]/adjust-credit/route.ts           (NEW) - POST adjust
  credits/ledger/route.ts                 (NEW) - GET ledger

apps/web/app/(admin)/
  layout.tsx            (UPDATE) - Enable Users + Credits sidebar items
```

## 3. Lý do chọn & Các phương án đã loại trừ (Alternatives)

### Phương án A — Gộp tất cả admin endpoint vào 1 file `admin.py` (ĐÃ LOẢI)
- **Lý do loại:** Convention repo là 1 router/feature. Tách thành `admin_users`, `admin_credit`, `admin_pricing` để dễ maintain.

### Phương án B — Dùng shadcn/ui cho admin UI (ĐÃ LOẠI)
- **Lý do loại:** Repo chưa có shadcn. Tailwind + glass system hiện có đủ tốt cho MVP. Sprint A2 chỉ cần CRUD table.

### Phương án C — Real-time audit log qua Supabase Realtime (ĐÃ LOẠI)
- **Lý do loại:** Plan có ghi nhưng Phase 6 chỉ cần ghi vào table. UI list thì poll mỗi 30s là đủ. Phase 7+ mới thêm realtime.

### Phương án D — Full impersonate JWT signing (ĐÃ LOẠI một phần)
- **Lý do loại:** Supabase Auth admin API cần service_role + signing key. Phase 6 viết **stub** (return mock token). Phase 7+ mới full impl.

### Lý do chọn phương án hiện tại
- **Convention:** Theo pattern Phase 1 (5 routers riêng, mount vào main).
- **Audit-first:** Mọi mutation đều qua `log_admin_action()`.
- **MVP scope:** Đủ để admin demo Phase 6, Phase 7+ thêm advanced.

## 4. Đánh giá rủi ro (Risk Assessment)

| # | Rủi ro | Mức | Giảm thiểu |
|---|--------|-----|------------|
| 1 | Mock admin JWT fail → verify RBAC fail | **Cao** | Step 1-3 chỉ gọi `require_admin` (Phase 5 đã cache role). Smoke test dùng `Bearer mock-token` + patch `get_supabase_admin` + `get_user_role`. |
| 2 | Audit log ghi sai `before/after` (không snapshot trước) | Trung bình | Mỗi mutation endpoint: query `before` → apply update → query `after` → log cả 2. |
| 3 | Soft delete làm mất data | Trung bình | Endpoint `DELETE /api/admin/users/{id}` chỉ set `deleted_at = NOW()`, KHÔNG xóa row. RPC `soft_delete_user` (0022) đã có. |
| 4 | Adjust credit với delta = -9999999 làm balance âm | Thấp | RPC `admin_adjust_credits` KHÔNG check balance. Tier 2 nên validate ở UI (max delta ±10000). Phase 6 thêm validation ở endpoint. |
| 5 | Export CSV dump toàn bộ ledger (10M rows) → OOM | Thấp | Step 2 giới hạn date range (max 1 năm) + pagination hint trong response header. |
| 6 | Impersonate token bị lạm dụng | **Cao** | Phase 6 chỉ return mock token (`{token: 'mock-impersonate-token', expires_at: now+15min}`). Phase 7+ mới sign JWT thật. |
| 7 | Web proxy admin bypass RBAC ở FastAPI | **Cao** | Web proxy chỉ pass-through, KHÔNG check role. FastAPI `require_admin` là single source of truth. |

## 5. Dự kiến nỗi lực (Estimation)

| Metric | Value |
|--------|-------|
| **Estimated LOC** | ~900 lines (450 Python + 350 TypeScript + 100 markdown) |
| **Timeline** | 11 steps MSEW, ước tính 8-10 giờ Tier 2 thực thi + verify |
| **Files touched** | 11 NEW + 2 UPDATE (main.py + layout.tsx) |

## 6. Phụ thuộc giữa các Step
- Step 1-3 (3 routers backend) độc lập nhau → Tier 2 có thể parallel nếu muốn.
- Step 4 (mount) phải sau Step 1-3.
- Step 5-6 (4 web proxy) độc lập với backend → có thể parallel với Step 1-4.
- Step 7-9 (3 trang admin) phụ thuộc web proxy → sau Step 5-6.
- Step 10 (sidebar update) sau Step 7-9 (để enable sau khi trang tồn tại).
- Step 11 (verify) cuối cùng.
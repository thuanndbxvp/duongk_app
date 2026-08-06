# Kế hoạch Triển khai (PLAN): phase2-ui-polish

## 1. Mục tiêu (Objective)
- **Mô tả ngắn gọn:** Đồng bộ dark theme (glass system) cho 5 trang legacy trong `apps/web/app/(dashboard)/` còn dùng Tailwind class "light" (`bg-white`, `text-gray-*`, `bg-gray-*`, `text-blue-600`).
- **Giá trị cốt lõi:**
  1. Visual consistency: Toàn bộ user-facing pages đều dùng dark glass theme.
  2. Tăng UX: User không còn "chớp mắt" khi navigate giữa `/projects/new` (dark) và `/assistants/[id]` (light).
  3. Tăng tính chuyên nghiệp của sản phẩm trước khi ra mắt user thật.

## 2. Kiến trúc lựa chọn (Architecture)

### Pattern: Token replacement (không thêm tính năng)
```
Mapping cố định (không thay đổi):

| CŨ (light)                  | MỚI (dark glass)                                 |
|-----------------------------|--------------------------------------------------|
| bg-white                    | glass (hoặc glass-strong)                        |
| bg-white/[0.04]            | bg-white/[0.04] (GIỮ NGUYÊN — đã đúng tone)    |
| text-gray-500              | text-[var(--fg-tertiary)]                        |
| text-gray-600              | text-[var(--fg-tertiary)]                        |
| text-gray-100              | bg-[var(--surface)]                              |
| bg-gray-50                 | hover:bg-[var(--surface-hover)]                  |
| bg-gray-100                | bg-[var(--surface)]                              |
| bg-gray-200                | bg-[var(--surface)]                              |
| text-blue-600              | text-[var(--brand-300)]                          |
| bg-blue-600                | bg-[var(--brand-500)]                            |
| text-orange-600            | text-[var(--brand-400)]                          |
| text-red-600               | text-red-400 (đỏ tone tối cho dark mode)         |
| rounded-lg shadow border   | glass rounded-2xl                                |
| border                     | border border-[var(--glass-border)]              |
| italic (giữ nguyên)        | italic (giữ nguyên)                              |
```

### Luồng thay đổi
- Từng file: đọc → identify tất cả occurrences của class cũ → thay bằng class mới theo mapping → save.
- KHÔNG thay đổi indentation, prop order, comment, import.
- KHÔNG thay đổi JSX structure (chỉ sửa string `className`).

## 3. Lý do chọn & Các phương án đã loại trừ (Alternatives)

### Phương án A — Áp dụng CSS `dark:` modifier Tailwind thay vì đổi sang token variable (ĐÃ LOẠI)
- **Lý do loại:** Hệ thống hiện KHÔNG dùng `dark:` modifier (single dark mode hardcoded). Thêm `dark:` sẽ tạo 2 theme và gây nhầm lẫn. Pattern hiện tại dùng CSS variables (chạm vào `:root`).

### Phương án B — Thay vì sửa từng file, viết CSS global override trong `globals.css` (ĐÃ LOẠI)
- **Lý do loại:** Tailwind class cũ (`bg-white`, `text-gray-500`) có specificity cao hơn CSS class thường. Phải dùng `!important` → khó maintain. Trực tiếp sửa từng file clean hơn.

### Phương án C — Refactor toàn bộ sang shadcn/ui (ĐÃ LOẠI)
- **Lý do loại:** Out of scope. Repo chưa có shadcn. Tăng bundle ~150KB. Phase 2 chỉ polish.

### Lý do chọn phương án hiện tại
- **Minimal change:** Chỉ thay `className` string. Không động vào logic.
- **Visual consistency:** Cùng token variables với `projects/new/page.tsx` (đã reference).
- **Maintainability:** Sau này thêm page mới, dev sẽ copy pattern này.

## 4. Đánh giá rủi ro (Risk Assessment)

| # | Rủi ro | Mức | Giảm thiểu |
|---|--------|-----|------------|
| 1 | Tailwind purge loại class nếu chưa thấy trong source | Thấp | Tất cả class mới đều dùng cho element có sẵn, hoặc đã có ở file khác. |
| 2 | Lỡ tay thay đổi logic JSX ngoài `className` | Trung bình | MSEW Step 1-5 chỉ ghi đúng dòng className cần đổi, dùng `StrReplace` với `old_string` rất cụ thể. |
| 3 | Visual regression: layout vỡ do padding/border-radius thay đổi | Thấp | Thay `rounded-lg` → `rounded-2xl` chỉ cho card có `bg-white`; giữ `rounded-lg` cho `p-3 border` (textarea). |
| 4 | Loading state đổi class mà server component đang render → flicker | Thấp | Loading state ở Step 4, 5 dùng className đơn giản `min-h-screen flex items-center justify-center` (đã chuẩn). |
| 5 | `text-red-600` ở `analysis/[id]/page.tsx` line 53 dùng cho error — đổi thành `text-red-400` có thể giảm contrast | Thấp | `text-red-400` vẫn readable trên dark bg. Có thể test nhanh. |

## 5. Dự kiến nỗi lực (Estimation)

| Metric | Value |
|--------|-------|
| **Estimated LOC changed** | ~30 dòng (chỉ `className` strings) |
| **Timeline** | 6 steps MSEW, ước tính 1-2 giờ Tier 2 thực thi + verify |
| **Files touched** | 5 files (tất cả đều UPDATE, không tạo mới) |

## 6. Phụ thuộc giữa các Step
- Step 1-5 độc lập nhau (mỗi file một step riêng) → Tier 2 có thể parallel nếu muốn.
- Step 6 (verify) cuối cùng, scan toàn bộ 5 file.
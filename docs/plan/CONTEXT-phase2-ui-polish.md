# Bối cảnh Hệ thống (CONTEXT): phase2-ui-polish

## 1. Tri thức Tổng hợp
- **Báo cáo Audit Phần 1:** `docs/audit/codebase_audit_report.md` (mục 1.4 ghi nhận "CSS đồng bộ dark theme cho `/assistants/[id]`, `/analysis/[id]`, `/ideas/[id]`, `/jobs/[id]`, `/scripts/[id]`" — priority STT #15).
- **Style guide hệ thống:** Dark glass + CSS variables `--fg-secondary`, `--fg-tertiary`, `--brand-300`, `--glass-border`, `--surface`, `--surface-hover`. Pattern tham chiếu: `apps/web/app/(dashboard)/projects/new/page.tsx` đã chuyển sang glass (xem dòng 35-50).
- **Bảng màu đã chuẩn hoá:** Xem `apps/web/app/globals.css` (sử dụng biến CSS).

## 2. Codebase Analysis (via Grep — đã chạy thủ công)

### Discovery — Các file còn dùng class Tailwind "light" cũ
| File | Line | Class cần đổi | Class chuẩn thay thế |
|------|------|---------------|----------------------|
| `apps/web/app/(dashboard)/assistants/[id]/page.tsx` | 60 | `text-blue-600 hover:underline` | `text-[var(--brand-300)] hover:text-[var(--brand-400)]` |
| `apps/web/app/(dashboard)/assistants/[id]/page.tsx` | 66, 104, 114 | `bg-white rounded-lg shadow border` | `glass rounded-2xl` |
| `apps/web/app/(dashboard)/assistants/[id]/page.tsx` | 77, 83, 89, 95 | `text-gray-500` | `text-[var(--fg-tertiary)]` |
| `apps/web/app/(dashboard)/assistants/[id]/page.tsx` | 90 | `text-orange-600` | `text-[var(--brand-400)]` |
| `apps/web/app/(dashboard)/assistants/[id]/page.tsx` | 117, 131 | `text-gray-500 italic` | `text-[var(--fg-tertiary)] italic` |
| `apps/web/app/(dashboard)/assistants/[id]/page.tsx` | 124 | `border rounded hover:bg-gray-50` | `border border-[var(--glass-border)] rounded-lg hover:bg-[var(--surface-hover)]` |
| `apps/web/app/(dashboard)/assistants/[id]/page.tsx` | 136 | `bg-gray-100 rounded-full` | `bg-[var(--surface)] rounded-full` |
| `apps/web/app/(dashboard)/analysis/[assistant_id]/page.tsx` | 32, 64 | `text-blue-600 hover:underline` | `text-[var(--brand-300)] hover:text-[var(--brand-400)]` |
| `apps/web/app/(dashboard)/analysis/[assistant_id]/page.tsx` | 36 | `text-center py-16 bg-white rounded-lg border` | `text-center py-16 glass rounded-2xl` |
| `apps/web/app/(dashboard)/analysis/[assistant_id]/page.tsx` | 41 | `text-gray-500` | `text-[var(--fg-tertiary)]` |
| `apps/web/app/(dashboard)/analysis/[assistant_id]/page.tsx` | 53 | `text-red-600` | `text-red-400` (giữ đỏ nhưng tone tối hơn cho dark mode) |
| `apps/web/app/(dashboard)/ideas/[assistant_id]/page.tsx` | 51 | `text-blue-600 hover:underline` | `text-[var(--brand-300)] hover:text-[var(--brand-400)]` |
| `apps/web/app/(dashboard)/ideas/[assistant_id]/page.tsx` | 61 | `text-sm text-gray-500 mt-1` | `text-sm text-[var(--fg-tertiary)] mt-1` |
| `apps/web/app/(dashboard)/ideas/[assistant_id]/page.tsx` | 70 | `text-center py-16 bg-white rounded-lg border` | `text-center py-16 glass rounded-2xl` |
| `apps/web/app/(dashboard)/ideas/[assistant_id]/page.tsx` | 75 | `text-gray-500` | `text-[var(--fg-tertiary)]` |
| `apps/web/app/(dashboard)/jobs/[id]/page.tsx` | 47 | `return <div>Loading...</div>` (chưa có dark class) | `<div className="min-h-screen flex items-center justify-center text-[var(--fg-secondary)]">Loading…</div>` |
| `apps/web/app/(dashboard)/jobs/[id]/page.tsx` | 57 | `w-full bg-gray-200 rounded-full h-2` | `w-full bg-[var(--surface)] rounded-full h-2` |
| `apps/web/app/(dashboard)/jobs/[id]/page.tsx` | 59 | `bg-blue-600 h-2 rounded-full` | `bg-[var(--brand-500)] h-2 rounded-full` |
| `apps/web/app/(dashboard)/scripts/[id]/page.tsx` | 22 | `<div>Loading...</div>` | `<div className="min-h-screen flex items-center justify-center text-[var(--fg-secondary)]">Loading…</div>` |
| `apps/web/app/(dashboard)/scripts/[id]/page.tsx` | 27 | `text-gray-600 mb-6` | `text-[var(--fg-tertiary)] mb-6` |
| `apps/web/app/(dashboard)/scripts/[id]/page.tsx` | 32-46 | `p-3 border rounded` | `p-3 border border-[var(--glass-border)] rounded-lg bg-[var(--surface)]/50` |

### Related Symbols (qua Grep `bg-white`)
- `apps/web/app/(dashboard)/projects/new/page.tsx:65` — `bg-white/[0.04]` (ĐÃ OK — dùng trong input dark glass).
- `apps/web/app/(dashboard)/assistants/[id]/page.tsx` — file cần sửa.
- `apps/web/app/(dashboard)/analysis/[assistant_id]/page.tsx` — file cần sửa.
- `apps/web/app/(dashboard)/ideas/[assistant_id]/page.tsx` — file cần sửa.

### File dùng làm reference pattern
- `apps/web/app/(dashboard)/projects/new/page.tsx` — đã dùng `glass`, `glass-strong`, `[var(--brand-300)]`, `[var(--brand-500)]`, `[var(--fg-secondary)]`. Pattern chuẩn để các file khác copy theo.

## 3. Các File liên quan và Vai trò

### Files cần sửa (5 files)
- `apps/web/app/(dashboard)/assistants/[id]/page.tsx` — Trang chi tiết assistant. Đang dùng `bg-white` cho header + actions + recent jobs. Cần đổi sang `glass` + token variables.
- `apps/web/app/(dashboard)/analysis/[assistant_id]/page.tsx` — Trang deep analysis. Empty state còn `bg-white`. Link back còn `text-blue-600`.
- `apps/web/app/(dashboard)/ideas/[assistant_id]/page.tsx` — Trang ideas. Empty state còn `bg-white`. Link back còn `text-blue-600`.
- `apps/web/app/(dashboard)/jobs/[id]/page.tsx` — Trang job progress. Progress bar còn `bg-gray-200` (track) + `bg-blue-600` (fill). Loading state không có dark styling.
- `apps/web/app/(dashboard)/scripts/[id]/page.tsx` — Trang script editor. Textarea còn border thường, không glass. Loading state không có dark styling.

### Components KHÔNG đụng (chúng đã dùng dark glass đúng)
- `apps/web/components/assistant-actions.tsx` (dùng trong assistants/[id])
- `apps/web/components/analysis/analysis-tabs.tsx`
- `apps/web/components/ideas/ideas-list.tsx`
- `apps/web/components/sub-progress-list.tsx`
- `apps/web/components/scene-timeline.tsx`

### Style tokens (đã định nghĩa sẵn)
- `glass`, `glass-strong` — class dùng `backdrop-blur` + border subtle + bg surface.
- `--brand-300`, `--brand-400`, `--brand-500` — gradient primary.
- `--fg-secondary`, `--fg-tertiary` — text color scale.
- `--surface`, `--surface-hover` — card background.
- `--glass-border` — border color.
- `gradient-text` — heading gradient.

## 4. Dependencies
- **External:** Không thêm package mới. Chỉ sửa Tailwind class.
- **Internal:** Không đụng component nào.

## 5. Ràng buộc (Constraints)
- **Môi trường:** Windows 10/11 (PowerShell 7).
- **Line Ending:** CRLF (giữ nguyên).
- **Visual consistency:** Dùng đúng token variables, KHÔNG hardcode color hex (tránh drift giữa các file).
- **No regression:** Tất cả tính năng JSX (button onClick, link href, fetch logic) PHẢI giữ nguyên. Phase 2 chỉ thay className.
- **KHÔNG đụng `projects/new/page.tsx`** — file này đã OK, chỉ dùng làm reference.

## 6. Tiêu chí Phase này hoàn thành (xem ACCEPTANCE)
- 0 occurrences `bg-white`, `text-gray-`, `bg-gray-`, `text-blue-600` trong 5 file polish.
- Tất cả 5 file sử dụng đúng pattern `glass` + token variables.
- TS compile 0 errors.
- Tất cả logic nghiệp vụ (fetch, redirect, button) KHÔNG đổi.
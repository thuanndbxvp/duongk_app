# Phân bổ Kỹ năng (SKILL-ROUTING): phase2-ui-polish

## 1. Chiến lược tổng thể (Overall Strategy)
Phase 2 là **cosmetic-only** (UI Polish). Không thêm tính năng, không sửa logic. Mục tiêu duy nhất: đồng bộ dark theme.

Skill chính: `ui-styling` (Tailwind + tokens). Tham chiếu `aesthetic` cho visual consistency. Không dùng `backend-development` hay `databases`.

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | Sửa `assistants/[id]/page.tsx` (header + actions + recent jobs) | `ui-styling` | `aesthetic` | `frontend-development` | Chuyển 8 class Tailwind light → dark token |
| Step 2 | Sửa `analysis/[assistant_id]/page.tsx` (empty state + link back) | `ui-styling` | `aesthetic` | `frontend-development` | Chuyển 4 class light → dark token |
| Step 3 | Sửa `ideas/[assistant_id]/page.tsx` (empty state + link back) | `ui-styling` | `aesthetic` | `frontend-development` | Chuyển 4 class light → dark token |
| Step 4 | Sửa `jobs/[id]/page.tsx` (loading + progress bar) | `ui-styling` | `aesthetic` | `frontend-development` | Chuyển 3 class + bổ sung dark loading |
| Step 5 | Sửa `scripts/[id]/page.tsx` (loading + textarea) | `ui-styling` | `aesthetic` | `frontend-development` | Chuyển 4 class + bổ sung dark loading |
| Step 6 | Verify: 0 occurrences light classes + TS compile 0 errors | `debugging` | `code-review` | `ui-styling` | Final QA |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)
- `aesthetic`: Cross-check visual harmony giữa các trang polish với `projects/new/page.tsx` (reference).
- `code-review`: Scan Scope Creep — Phase 2 chỉ đổi className, KHÔNG đổi logic.
- `debugging`: Nếu dev server báo hydration error do class không tồn tại (Tailwind purge).

## 4. Cấm kỹ (Forbidden)
- ❌ **CẤM** đụng `apps/web/app/(dashboard)/projects/new/page.tsx` (đã OK).
- ❌ **CẤM** đụng bất kỳ component nào (`assistant-actions`, `analysis-tabs`, `ideas-list`, `sub-progress-list`, `scene-timeline`).
- ❌ **CẤM** sửa logic JSX (onClick, onChange, href, fetch, redirect, useState).
- ❌ **CẤM** hardcode màu hex (#FFFFFF, #000000). PHẢI dùng CSS variables.
- ❌ **CẤM** thêm dependency mới.
- ❌ **CẤM** sửa file khác ngoài 5 file liệt kê ở Step 1-5.
- ❌ **CẤM** đổi tên class (ví dụ: tự ý đổi `glass` thành `glass-card`).
# Tiêu chí Nghiệm thu (ACCEPTANCE): phase2-ui-polish

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### File 1: `apps/web/app/(dashboard)/assistants/[id]/page.tsx`
- [ ] **0** occurrences `bg-white` trong file.
- [ ] **0** occurrences `text-gray-500`, `text-gray-600` trong file.
- [ ] **0** occurrences `text-blue-600` trong file.
- [ ] **0** occurrences `bg-gray-50`, `bg-gray-100`, `bg-gray-200` trong file.
- [ ] **0** occurrences `text-orange-600` trong file.
- [ ] Có ≥ 4 occurrences `[var(--brand-300)]`, `[var(--brand-400)]`, `[var(--fg-tertiary)]`, `[var(--surface)]`, `[var(--surface-hover)]`, `[var(--glass-border)]`.
- [ ] Có ≥ 3 occurrences class `glass` (cho header card, actions card, recent jobs card).
- [ ] Header card (line 66) dùng class `glass rounded-2xl p-6 mb-6` thay vì `bg-white rounded-lg shadow border p-6 mb-6`.
- [ ] Actions card (line 104) dùng class `glass rounded-2xl p-6 mb-6`.
- [ ] Recent jobs card (line 114) dùng class `glass rounded-2xl p-6`.
- [ ] Back link (line 60) dùng class `text-[var(--brand-300)] hover:text-[var(--brand-400)]`.
- [ ] Status badge (line 136) dùng class `bg-[var(--surface)]`.
- [ ] Job link (line 124) có `border-[var(--glass-border)]` và `hover:bg-[var(--surface-hover)]`.

### File 2: `apps/web/app/(dashboard)/analysis/[assistant_id]/page.tsx`
- [ ] **0** occurrences `bg-white` trong file.
- [ ] **0** occurrences `text-gray-500`, `text-gray-600` trong file.
- [ ] **0** occurrences `text-blue-600` trong file.
- [ ] **0** occurrences `text-red-600` trong file.
- [ ] Empty state (line 36) dùng class `text-center py-16 glass rounded-2xl mt-6`.
- [ ] Back link (line 32, 64) dùng class `text-[var(--brand-300)] hover:text-[var(--brand-400)]`.
- [ ] Empty hint (line 41) dùng `text-[var(--fg-tertiary)]`.
- [ ] Error message (line 53) dùng `text-red-400` thay vì `text-red-600`.

### File 3: `apps/web/app/(dashboard)/ideas/[assistant_id]/page.tsx`
- [ ] **0** occurrences `bg-white` trong file.
- [ ] **0** occurrences `text-gray-500`, `text-gray-600` trong file.
- [ ] **0** occurrences `text-blue-600` trong file.
- [ ] Empty state (line 70) dùng class `text-center py-16 glass rounded-2xl`.
- [ ] Stats line (line 61) dùng `text-[var(--fg-tertiary)]`.
- [ ] Empty hint (line 75) dùng `text-[var(--fg-tertiary)]`.
- [ ] Back link (line 51) dùng `text-[var(--brand-300)] hover:text-[var(--brand-400)]`.

### File 4: `apps/web/app/(dashboard)/jobs/[id]/page.tsx`
- [ ] **0** occurrences `bg-gray-200`, `bg-gray-100` trong file.
- [ ] **0** occurrences `bg-blue-600` trong file.
- [ ] Loading state (line 47) dùng class `min-h-screen flex items-center justify-center text-[var(--fg-secondary)]`.
- [ ] Progress track (line 57) dùng `bg-[var(--surface)]`.
- [ ] Progress fill (line 59) dùng `bg-[var(--brand-500)]`.

### File 5: `apps/web/app/(dashboard)/scripts/[id]/page.tsx`
- [ ] **0** occurrences `text-gray-600` trong file.
- [ ] **0** occurrences `p-3 border rounded` (chỉ) trong file.
- [ ] Loading state (line 22) dùng class `min-h-screen flex items-center justify-center text-[var(--fg-secondary)]`.
- [ ] Topic subtitle (line 27) dùng `text-[var(--fg-tertiary)]`.
- [ ] 3 textarea (line 32, 39, 46) dùng class `w-full p-3 border border-[var(--glass-border)] rounded-lg bg-[var(--surface)]/50 text-white focus:outline-none focus:border-[var(--brand-400)]`.

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

- **Visual consistency:** Tất cả 5 file dùng cùng pattern với `projects/new/page.tsx` (đã OK).
- **No regression:** Logic JSX (useState, useEffect, fetch, redirect, onClick) KHÔNG đổi.
- **File KHÔNG đụng:**
  - `projects/new/page.tsx` (đã OK, dùng làm reference).
  - Tất cả component (`assistant-actions`, `analysis-tabs`, `ideas-list`, `sub-progress-list`, `scene-timeline`).
  - Tất cả file khác ngoài 5 file liệt kê.
- **Không hardcode color hex:** Tất cả màu sắc phải qua CSS variable `[var(--...)]`.
- **Không thêm dependency mới.**

## 3. Mục tiêu Test Coverage
- **N/A** — Phase 2 là cosmetic, không có unit test.

## 4. Các bước Manual Verification (Windows PowerShell)

### Bước 1: Grep 0 light class trong 5 file
```powershell
cd d:\appDK\apps\web
$files = @(
  "app/(dashboard)/assistants/[id]/page.tsx",
  "app/(dashboard)/analysis/[assistant_id]/page.tsx",
  "app/(dashboard)/ideas/[assistant_id]/page.tsx",
  "app/(dashboard)/jobs/[id]/page.tsx",
  "app/(dashboard)/scripts/[id]/page.tsx"
)

foreach ($f in $files) {
  $light = (Get-Content $f | Select-String "bg-white|text-gray-|text-blue-600|bg-gray-|bg-blue-600|text-orange-600" | Measure-Object -Line).Lines
  $token = (Get-Content $f | Select-String "var\(--" | Measure-Object -Line).Lines
  Write-Host "$f | light=$light token=$token"
}
```
**Expected:** Mỗi file: `light=0`, `token≥2`.

### Bước 2: TS compile
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit
```
**Expected:** 0 errors.

### Bước 3: Visual smoke test (optional, cần browser)
```powershell
cd d:\appDK\apps\web
pnpm dev
```
Mở browser:
- `http://localhost:3000/assistants/<id>` — header card dark, không còn nền trắng chói.
- `http://localhost:3000/analysis/<id>` — empty state dark, error text đỏ tone tối.
- `http://localhost:3000/ideas/<id>` — empty state dark, stats text tertiary.
- `http://localhost:3000/jobs/<id>` — progress bar dùng brand color, loading state center screen.
- `http://localhost:3000/scripts/<id>` — textarea có bg surface + border, loading center.

### Bước 4: Regression check (visual so với projects/new)
- Mở `http://localhost:3000/projects/new` (đã OK) và 1 trang polish. So sánh: cùng tone dark, cùng card style glass, cùng brand color.

## 5. Định nghĩa "Hoàn thành Phase"
Tất cả 6 MSEW step phải PASS verify command của riêng nó, VÀ 4 manual verification ở trên pass.

Khi pass → Tier 2 ghi báo cáo vào file `docs/audit/AUDIT-REPORT-phase2-ui-polish.md` (theo template `AUDIT-REPORT.template.md`) và thông báo cho Planner.
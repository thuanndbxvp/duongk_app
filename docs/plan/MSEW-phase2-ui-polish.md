# MSEW: phase2-ui-polish

## Prerequisites (Điều kiện tiên quyết)
- **Đọc CONTEXT:** `docs/plan/CONTEXT-phase2-ui-polish.md`
- **Đọc PLAN:** `docs/plan/PLAN-phase2-ui-polish.md`
- **Reference file:** `apps/web/app/(dashboard)/projects/new/page.tsx` (đã polish đúng chuẩn)
- **Branch:** main
- **Working dir:** `d:\appDK`
- **Line Ending:** CRLF
- **Quy tắc:** Phase 2 chỉ thay `className` string. KHÔNG đụng logic JSX. KHÔNG thêm tính năng.

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | Sửa `assistants/[id]/page.tsx` | `ui-styling` | `aesthetic` | `frontend-development` |
| 2 | Sửa `analysis/[assistant_id]/page.tsx` | `ui-styling` | `aesthetic` | `frontend-development` |
| 3 | Sửa `ideas/[assistant_id]/page.tsx` | `ui-styling` | `aesthetic` | `frontend-development` |
| 4 | Sửa `jobs/[id]/page.tsx` | `ui-styling` | `aesthetic` | `frontend-development` |
| 5 | Sửa `scripts/[id]/page.tsx` | `ui-styling` | `aesthetic` | `frontend-development` |
| 6 | Self-verify toàn bộ | `debugging` | `code-review` | `ui-styling` |

## Files KHÔNG được đụng (Do Not Touch)
- `apps/web/app/(dashboard)/projects/new/page.tsx` — reference đã OK.
- `apps/web/components/assistant-actions.tsx`
- `apps/web/components/analysis/analysis-tabs.tsx`
- `apps/web/components/ideas/ideas-list.tsx`
- `apps/web/components/sub-progress-list.tsx`
- `apps/web/components/scene-timeline.tsx`
- Mọi file khác ngoài 5 file trong Step 1-5.

---

## Mapping Bắt buộc (dùng xuyên suốt Phase 2)

| CŨ | MỚI |
|------|------|
| `bg-white` (cho card) | `glass` |
| `bg-white` (cho empty state) | `glass` |
| `text-gray-500` | `text-[var(--fg-tertiary)]` |
| `text-gray-600` | `text-[var(--fg-tertiary)]` |
| `bg-gray-50` (hover) | `hover:bg-[var(--surface-hover)]` |
| `bg-gray-100` | `bg-[var(--surface)]` |
| `bg-gray-200` | `bg-[var(--surface)]` |
| `text-blue-600` (link) | `text-[var(--brand-300)]` |
| `bg-blue-600` (progress fill) | `bg-[var(--brand-500)]` |
| `text-orange-600` (accent) | `text-[var(--brand-400)]` |
| `text-red-600` (error) | `text-red-400` |
| `rounded-lg shadow border p-6` (card) | `glass rounded-2xl p-6` |
| `rounded-lg border` (empty state) | `glass rounded-2xl` |
| `p-3 border rounded` (input/textarea) | `p-3 border border-[var(--glass-border)] rounded-lg bg-[var(--surface)]/50` |

---

## Micro-Steps

### Step 1: Sửa `apps/web/app/(dashboard)/assistants/[id]/page.tsx`
**File:** `apps/web/app/(dashboard)/assistants/[id]/page.tsx`
**Vị trí:** Sửa 8 occurrences ở line 60, 66, 77, 83, 89, 90, 95, 104, 114, 117, 124, 131, 136.
**Skill Invocation:**
  - **Primary:** `ui-styling`.
  - **Reference:** `aesthetic`.
  - **Fallback:** `frontend-development`.

**Pre-check (Grep):**
- `grep -n "bg-white\|text-gray-\|text-blue-\|bg-gray-\|text-orange-" "apps/web/app/(dashboard)/assistants/[id]/page.tsx"` → expect 13 matches.

**Code cần thay (dùng `StrReplace` 8 lần — mỗi `old_string` cụ thể cho từng dòng):**

**Thay 1 — line 60 (back link):**
```typescript
        <Link href="/assistants" className="text-blue-600 hover:underline">
```
**Đổi thành:**
```typescript
        <Link href="/assistants" className="text-[var(--brand-300)] hover:text-[var(--brand-400)]">
```

**Thay 2 — line 66 (header card):**
```typescript
      <div className="bg-white rounded-lg shadow border p-6 mb-6">
```
**Đổi thành:**
```typescript
      <div className="glass rounded-2xl p-6 mb-6">
```

**Thay 3 — line 77, 83, 95 (label "Subscribers"/"Videos"/"Status"):**
```typescript
                <div className="text-gray-500">Subscribers</div>
```
**Đổi thành:**
```typescript
                <div className="text-[var(--fg-tertiary)]">Subscribers</div>
```

**Thay 4 — line 89 (label "Viral"):**
```typescript
                <div className="text-gray-500">Viral</div>
```
**Đổi thành:**
```typescript
                <div className="text-[var(--fg-tertiary)]">Viral</div>
```

**Thay 5 — line 90 (viral count):**
```typescript
                <div className="font-semibold text-orange-600">
```
**Đổi thành:**
```typescript
                <div className="font-semibold text-[var(--brand-400)]">
```

**Thay 6 — line 104 (actions card):**
```typescript
      <div className="bg-white rounded-lg shadow border p-6 mb-6">
```
**Đổi thành:**
```typescript
      <div className="glass rounded-2xl p-6 mb-6">
```

**Thay 7 — line 114 (recent jobs card):**
```typescript
      <div className="bg-white rounded-lg shadow border p-6">
```
**Đổi thành:**
```typescript
      <div className="glass rounded-2xl p-6">
```

**Thay 8 — line 117 (empty jobs message):**
```typescript
          <p className="text-gray-500 italic">Chưa có job nào.</p>
```
**Đổi thành:**
```typescript
          <p className="text-[var(--fg-tertiary)] italic">Chưa có job nào.</p>
```

**Thay 9 — line 124 (job link):**
```typescript
                className="block p-3 border rounded hover:bg-gray-50"
```
**Đổi thành:**
```typescript
                className="block p-3 border border-[var(--glass-border)] rounded-lg hover:bg-[var(--surface-hover)]"
```

**Thay 10 — line 131 (job date):**
```typescript
                    <div className="text-xs text-gray-500">
```
**Đổi thành:**
```typescript
                    <div className="text-xs text-[var(--fg-tertiary)]">
```

**Thay 11 — line 136 (status badge):**
```typescript
                      <span className="px-2 py-1 bg-gray-100 rounded-full capitalize">
```
**Đổi thành:**
```typescript
                      <span className="px-2 py-1 bg-[var(--surface)] rounded-full capitalize">
```

**KHÔNG được sửa:**
- Imports (line 1-5).
- Interface Assistant/Job (line 7-28).
- Hàm `formatSubs` (line 51-55).
- Logic `apiFetch` (line 41-49).
- Các props truyền vào component.

**Verify command (PowerShell):**
```powershell
cd d:\appDK\apps\web
# Check 0 occurrences of light classes
Get-Content "app/(dashboard)/assistants/[id]/page.tsx" | Select-String "bg-white|text-gray-|text-blue-600|bg-gray-" | Measure-Object -Line
```

**Expected output:** Count = 0.

---

### Step 2: Sửa `apps/web/app/(dashboard)/analysis/[assistant_id]/page.tsx`
**File:** `apps/web/app/(dashboard)/analysis/[assistant_id]/page.tsx`
**Vị trí:** 4 occurrences ở line 32, 36, 41, 53, 64.
**Skill Invocation:**
  - **Primary:** `ui-styling`.
  - **Reference:** `aesthetic`.
  - **Fallback:** `frontend-development`.

**Pre-check (Grep):**
- `grep -n "bg-white\|text-gray-\|text-blue-\|text-red-" "apps/web/app/(dashboard)/analysis/[assistant_id]/page.tsx"` → expect 4 matches.

**Code cần thay (4 lần `StrReplace`):**

**Thay 1 — line 32 (back link trong empty state):**
```typescript
          className="text-blue-600 hover:underline"
```
**Đổi thành:**
```typescript
          className="text-[var(--brand-300)] hover:text-[var(--brand-400)]"
```

**Thay 2 — line 36 (empty state container):**
```typescript
        <div className="text-center py-16 bg-white rounded-lg border mt-6">
```
**Đổi thành:**
```typescript
        <div className="text-center py-16 glass rounded-2xl mt-6">
```

**Thay 3 — line 41 (empty state hint):**
```typescript
          <p className="text-gray-500 mb-6">
```
**Đổi thành:**
```typescript
          <p className="text-[var(--fg-tertiary)] mb-6">
```

**Thay 4 — line 53 (error message):**
```typescript
        <p className="text-red-600">Failed to load analysis.</p>
```
**Đổi thành:**
```typescript
        <p className="text-red-400">Failed to load analysis.</p>
```

**Thay 5 — line 64 (back link ở success state):**
```typescript
        className="text-blue-600 hover:underline"
```
**Đổi thành:**
```typescript
        className="text-[var(--brand-300)] hover:text-[var(--brand-400)]"
```

**KHÔNG được sửa:**
- Imports.
- `notFound()`, `redirect()` calls.
- `apiFetch` logic.
- `<AnalysisTabs>` props.

**Verify command:**
```powershell
Get-Content "app/(dashboard)/analysis/[assistant_id]/page.tsx" | Select-String "bg-white|text-gray-|text-blue-600|text-red-600" | Measure-Object -Line
```

**Expected output:** Count = 0.

---

### Step 3: Sửa `apps/web/app/(dashboard)/ideas/[assistant_id]/page.tsx`
**File:** `apps/web/app/(dashboard)/ideas/[assistant_id]/page.tsx`
**Vị trí:** 4 occurrences ở line 51, 61, 70, 75.
**Skill Invocation:**
  - **Primary:** `ui-styling`.
  - **Reference:** `aesthetic`.
  - **Fallback:** `frontend-development`.

**Pre-check (Grep):**
- `grep -n "bg-white\|text-gray-\|text-blue-" "apps/web/app/(dashboard)/ideas/[assistant_id]/page.tsx"` → expect 4 matches.

**Code cần thay (4 lần `StrReplace`):**

**Thay 1 — line 51 (back link):**
```typescript
        className="text-blue-600 hover:underline"
```
**Đổi thành:**
```typescript
        className="text-[var(--brand-300)] hover:text-[var(--brand-400)]"
```

**Thay 2 — line 61 (stats line):**
```typescript
          <p className="text-sm text-gray-500 mt-1">
```
**Đổi thành:**
```typescript
          <p className="text-sm text-[var(--fg-tertiary)] mt-1">
```

**Thay 3 — line 70 (empty state container):**
```typescript
        <div className="text-center py-16 bg-white rounded-lg border">
```
**Đổi thành:**
```typescript
        <div className="text-center py-16 glass rounded-2xl">
```

**Thay 4 — line 75 (empty state hint):**
```typescript
          <p className="text-gray-500 mb-6">
```
**Đổi thành:**
```typescript
          <p className="text-[var(--fg-tertiary)] mb-6">
```

**KHÔNG được sửa:**
- Imports.
- `notFound()`, `redirect()`.
- `IdeasList`, `RegenerateButton` props.

**Verify command:**
```powershell
Get-Content "app/(dashboard)/ideas/[assistant_id]/page.tsx" | Select-String "bg-white|text-gray-|text-blue-600" | Measure-Object -Line
```

**Expected output:** Count = 0.

---

### Step 4: Sửa `apps/web/app/(dashboard)/jobs/[id]/page.tsx`
**File:** `apps/web/app/(dashboard)/jobs/[id]/page.tsx`
**Vị trí:** 3 occurrences ở line 47, 57, 59.
**Skill Invocation:**
  - **Primary:** `ui-styling`.
  - **Reference:** `aesthetic`.
  - **Fallback:** `frontend-development`.

**Pre-check (Grep):**
- `grep -n "bg-gray-\|bg-blue-\|Loading" "apps/web/app/(dashboard)/jobs/[id]/page.tsx"` → expect 3 matches.

**Code cần thay (3 lần `StrReplace`):**

**Thay 1 — line 47 (loading state):**
```typescript
  if (!job) return <div>Loading...</div>;
```
**Đổi thành:**
```typescript
  if (!job) return <div className="min-h-screen flex items-center justify-center text-[var(--fg-secondary)]">Loading…</div>;
```

**Thay 2 — line 57 (progress track):**
```typescript
        <div className="w-full bg-gray-200 rounded-full h-2">
```
**Đổi thành:**
```typescript
        <div className="w-full bg-[var(--surface)] rounded-full h-2">
```

**Thay 3 — line 59 (progress fill):**
```typescript
          className="bg-blue-600 h-2 rounded-full transition-all"
```
**Đổi thành:**
```typescript
          className="bg-[var(--brand-500)] h-2 rounded-full transition-all"
```

**KHÔNG được sửa:**
- `useEffect`, `supabase.channel`, `setJob`.
- `SubProgressList` props.

**Verify command:**
```powershell
Get-Content "app/(dashboard)/jobs/[id]/page.tsx" | Select-String "bg-gray-|bg-blue-600" | Measure-Object -Line
```

**Expected output:** Count = 0.

---

### Step 5: Sửa `apps/web/app/(dashboard)/scripts/[id]/page.tsx`
**File:** `apps/web/app/(dashboard)/scripts/[id]/page.tsx`
**Vị trí:** 4 occurrences ở line 22, 27, 32, 39, 46.
**Skill Invocation:**
  - **Primary:** `ui-styling`.
  - **Reference:** `aesthetic`.
  - **Fallback:** `frontend-development`.

**Pre-check (Grep):**
- `grep -n "Loading\|text-gray-\|p-3 border rounded" "apps/web/app/(dashboard)/scripts/[id]/page.tsx"` → expect 4 matches.

**Code cần thay (4 lần `StrReplace`):**

**Thay 1 — line 22 (loading state):**
```typescript
  if (!script) return <div>Loading...</div>;
```
**Đổi thành:**
```typescript
  if (!script) return <div className="min-h-screen flex items-center justify-center text-[var(--fg-secondary)]">Loading…</div>;
```

**Thay 2 — line 27 (topic subtitle):**
```typescript
  <p className="text-gray-600 mb-6">Chủ đề: {script.topic}</p>
```
**Đổi thành:**
```typescript
  <p className="text-[var(--fg-tertiary)] mb-6">Chủ đề: {script.topic}</p>
```

**Thay 3 — line 32 (hook textarea):**
```typescript
            className="w-full p-3 border rounded h-32"
```
**Đổi thành:**
```typescript
            className="w-full p-3 border border-[var(--glass-border)] rounded-lg bg-[var(--surface)]/50 text-white focus:outline-none focus:border-[var(--brand-400)] h-32"
```

**Thay 4 — line 39 (body textarea):**
```typescript
            className="w-full p-3 border rounded h-96"
```
**Đổi thành:**
```typescript
            className="w-full p-3 border border-[var(--glass-border)] rounded-lg bg-[var(--surface)]/50 text-white focus:outline-none focus:border-[var(--brand-400)] h-96"
```

**Thay 5 — line 46 (cta textarea):**
```typescript
            className="w-full p-3 border rounded h-24"
```
**Đổi thành:**
```typescript
            className="w-full p-3 border border-[var(--glass-border)] rounded-lg bg-[var(--surface)]/50 text-white focus:outline-none focus:border-[var(--brand-400)] h-24"
```

**KHÔNG được sửa:**
- `useState`, `useEffect`, `fetch`.
- `SceneTimeline` props.

**Verify command:**
```powershell
Get-Content "app/(dashboard)/scripts/[id]/page.tsx" | Select-String "text-gray-600|p-3 border rounded" | Measure-Object -Line
```

**Expected output:** Count = 0.

---

### Step 6: Self-verify toàn bộ
**Skill Invocation:**
  - **Primary:** `debugging`.
  - **Reference:** `code-review`.
  - **Fallback:** `ui-styling`.

**Verify commands (PowerShell):**
```powershell
# 1) 0 occurrences of light classes trong 5 file
cd d:\appDK\apps\web
$files = @(
  "app/(dashboard)/assistants/[id]/page.tsx",
  "app/(dashboard)/analysis/[assistant_id]/page.tsx",
  "app/(dashboard)/ideas/[assistant_id]/page.tsx",
  "app/(dashboard)/jobs/[id]/page.tsx",
  "app/(dashboard)/scripts/[id]/page.tsx"
)

$totalLight = 0
foreach ($f in $files) {
  $count = (Get-Content $f | Select-String "bg-white|text-gray-|text-blue-600|bg-gray-|bg-blue-600" | Measure-Object -Line).Lines
  Write-Host "$f : $count"
  $totalLight += $count
}
Write-Host "TOTAL: $totalLight"

# 2) Confirm token variables đã được dùng
foreach ($f in $files) {
  $count = (Get-Content $f | Select-String "var\(--(brand|fg|surface|glass)" | Measure-Object -Line).Lines
  Write-Host "$f (token usage): $count"
}

# 3) TS compile
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"
```

**Expected output:**
- TOTAL = 0
- Mỗi file có ít nhất 2-3 token variable matches
- 0 errors TS

**Nếu bất kỳ check nào fail:**
- Invoke skill `debugging`.
- Ghi vào `BLOCKERS.md` với format:
  ```
  ## Step X failure
  - Verify command: ...
  - Expected: ...
  - Actual: ...
  - Hypothesized cause: ...
  ```

---

## Definition of Done cho Phase này
- 0 occurrences `bg-white`, `text-gray-*`, `bg-gray-*`, `text-blue-600`, `bg-blue-600`, `text-orange-600` trong 5 file polish.
- Tất cả 5 file sử dụng đúng pattern `glass` + CSS variables.
- TS compile 0 errors.
- Tất cả logic nghiệp vụ (fetch, redirect, button onClick) KHÔNG đổi.
- File `projects/new/page.tsx` KHÔNG bị đụng.
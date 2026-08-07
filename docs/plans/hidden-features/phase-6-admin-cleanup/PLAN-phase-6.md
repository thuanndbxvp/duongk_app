# Phase 6 — Admin Tools + Cleanup

> **Goal**: Build admin pages (backup, traffic, MFA) + cleanup database columns.
> **Effort**: 3 ngày
> **Risk**: LOW
> **Prerequisite**: P1
> **Source**: `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` §4.B (DB), §3.1.F (admin)

---

## 1. Vấn đề

### Admin endpoints
Backend đã implement admin tools:
- `GET /api/admin/backup` — generate config backup JSON
- `POST /api/admin/backup` — restore from JSON
- `GET /api/admin/traffic` — traffic stats (last 7 days)
- `GET /api/admin/users` — user list with stats
- `POST /api/admin/mfa` — MFA enroll (fixed in P1)
- `GET /api/admin/mfa` — MFA status
- `DELETE /api/admin/mfa` — disable MFA

Không có UI.

### Database cleanup
Audit phát hiện ~12 columns unused:
- `voice_profiles.tone`, `pitch`, `speed` — không hiển thị
- `projects.archived_at`, `deleted_at` — chỉ có UI archived
- `scripts.last_token_count` — không hiển thị
- etc.

2 options:
1. Thêm UI để display/edit
2. Drop columns (DB migration)

Tier 2 chọn approach dựa trên business value.

## 2. Acceptance Criteria

### 2.1 Admin backup page

- [ ] `/admin/backup` route
- [ ] Auth gate: chỉ admin mới access
- [ ] "Generate backup" button → GET /api/admin/backup → download JSON
- [ ] "Restore from backup" → file upload → POST /api/admin/backup
- [ ] Show last backup timestamp

### 2.2 Admin traffic page

- [ ] `/admin/traffic` route
- [ ] Auth gate: admin only
- [ ] Chart: requests/day (last 7 days)
- [ ] Top endpoints by traffic
- [ ] Error rate gauge
- [ ] Active users count

### 2.3 Admin users page

- [ ] `/admin/users` route
- [ ] Auth gate: admin only
- [ ] User list table (email, created, projects count, last active)
- [ ] Filter by status (active/inactive/banned)
- [ ] Click user → detail

### 2.4 Admin MFA page

- [ ] `/admin/mfa` route (user-facing, not admin)
- [ ] Show MFA status (enabled/disabled)
- [ ] Enroll button → POST /api/admin/mfa → QR code + backup codes
- [ ] Disable button → confirm → DELETE /api/admin/mfa

### 2.5 Database cleanup

- [ ] Decision matrix cho 12 columns: keep+UI vs drop
- [ ] Migration file nếu drop
- [ ] Update ORM models
- [ ] Update tests

### 2.6 Tests

- [ ] Component tests cho admin pages
- [ ] Auth gate tests
- [ ] Integration tests

## 3. Implementation Outline

### 3.1 Admin layout (with auth gate)

**File: `apps/web/app/(admin)/admin/layout.tsx` (MỚI)**

```tsx
import { redirect } from "next/navigation";
import { getAuthToken, getCurrentUser } from "@/lib/auth";

export default async function AdminLayout({ children }) {
  const token = await getAuthToken();
  const user = await getCurrentUser(token);

  if (!user || user.role !== "admin") {
    redirect("/dashboard");
  }

  return (
    <div className="flex">
      <aside className="w-64 bg-gray-900 text-white p-4">
        <h2 className="font-bold mb-4">Admin</h2>
        <nav className="space-y-2">
          <Link href="/admin/backup">Backup</Link>
          <Link href="/admin/traffic">Traffic</Link>
          <Link href="/admin/users">Users</Link>
        </nav>
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
```

### 3.2 Admin backup page

**File: `apps/web/app/(admin)/admin/backup/page.tsx` (MỚI)**

```tsx
import { BackupManager } from "@/components/admin/backup-manager";

export default function AdminBackupPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Backup & Restore</h1>
      <BackupManager />
    </div>
  );
}
```

**File: `apps/web/components/admin/backup-manager.tsx` (MỚI)**

```tsx
"use client";
import { useState } from "react";

export function BackupManager() {
  const [isDownloading, setIsDownloading] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      const r = await fetch("/api/admin/backup");
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `backup-${new Date().toISOString()}.json`;
      a.click();
    } finally {
      setIsDownloading(false);
    }
  };

  const handleRestore = async (file: File) => {
    if (!confirm("Restore sẽ ghi đè lên config hiện tại. Tiếp tục?")) return;
    setIsRestoring(true);
    try {
      const text = await file.text();
      const r = await fetch("/api/admin/backup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: text,
      });
      if (r.ok) alert("Restore thành công");
      else alert("Lỗi: " + (await r.text()));
    } finally {
      setIsRestoring(false);
    }
  };

  return (
    <div className="space-y-4">
      <button onClick={handleDownload} disabled={isDownloading} className="btn btn-primary">
        {isDownloading ? "Đang generate..." : "Download Backup"}
      </button>
      <label className="btn btn-secondary">
        {isRestoring ? "Đang restore..." : "Restore from File"}
        <input
          type="file"
          accept=".json"
          onChange={(e) => e.target.files?.[0] && handleRestore(e.target.files[0])}
          className="hidden"
        />
      </label>
    </div>
  );
}
```

### 3.3 Admin traffic page (chart)

**File: `apps/web/app/(admin)/admin/traffic/page.tsx` (MỚI)**

```tsx
import { TrafficChart } from "@/components/admin/traffic-chart";

export default async function AdminTrafficPage() {
  const token = await getAuthToken();
  const r = await fetch("http://api:8000/api/admin/traffic", {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  const data = await r.json();

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Traffic (last 7 days)</h1>
      <TrafficChart data={data} />
    </div>
  );
}
```

### 3.4 DB cleanup migration

**File: `supabase/migrations/20260808-drop-unused-columns.sql` (MỚI)**

```sql
-- Decision: DROP columns không có UI và không có business value
ALTER TABLE voice_profiles DROP COLUMN IF EXISTS pitch;
ALTER TABLE voice_profiles DROP COLUMN IF EXISTS tone;
ALTER TABLE scripts DROP COLUMN IF EXISTS last_token_count;

-- Decision: KEEP columns có UI partial
-- projects.archived_at: giữ (UI archived sẽ được add trong tương lai)
```

## 4. Files thay đổi

| File | Action | LOC |
|---|---|---|
| `apps/web/app/(admin)/admin/layout.tsx` | MỚI | +30 |
| `apps/web/app/(admin)/admin/backup/page.tsx` | MỚI | +20 |
| `apps/web/app/(admin)/admin/traffic/page.tsx` | MỚI | +30 |
| `apps/web/app/(admin)/admin/users/page.tsx` | MỚI | +50 |
| `apps/web/app/(admin)/admin/mfa/page.tsx` | MỚI | +30 |
| `apps/web/components/admin/backup-manager.tsx` | MỚI | +60 |
| `apps/web/components/admin/traffic-chart.tsx` | MỚI | +60 |
| `apps/web/components/admin/user-table.tsx` | MỚI | +50 |
| `apps/web/components/admin/mfa-setup.tsx` | MỚI | +80 |
| `supabase/migrations/20260808-drop-unused-columns.sql` | MỚI | +20 |
| `apps/api/models/voice_profile.py` | SỬA | -10 |
| `apps/api/models/script.py` | SỬA | -5 |
| `tests/web/components/admin/*.test.tsx` | MỚI | +100 |
| `tests/api/test_admin_endpoints.py` | MỚI | +60 |

## 5. Test plan

```bash
pytest tests/web/components/admin/ -v
pytest tests/api/test_admin_endpoints.py -v
bash scripts/run_e2e_local.sh
```

## 6. Done when

- [ ] 4 admin pages exist
- [ ] Auth gate works
- [ ] DB cleanup migration applied
- [ ] All tests pass
- [ ] Coverage ≥80%
- [ ] Tier 1 sign-off
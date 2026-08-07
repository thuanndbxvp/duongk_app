# Phase 1 — Quick Wins

> **Goal**: Stabilize codebase, fix drift, add high-impact small features.
> **Effort**: 2 ngày
> **Risk**: LOW
> **Prerequisite**: None
> **Source**: `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` §3.2, §5.1, §7.1

---

## 1. Vấn đề

Audit phát hiện 3 loại vấn đề quick-fix:

1. **Endpoint drift** — frontend gọi URL mà backend không handle (12 cases)
2. **Cancel render job** — backend có route nhưng không có UI button (UX critical)
3. **Dead services** — 6 files không ai import (cleanup code)

## 2. Acceptance Criteria

### 2.1 Drift fixes

- [ ] Verify 12 drift endpoints bằng E2E test (auto-skip Supabase dependency)
- [ ] Sửa 3 cases có backend đang gọi sai path:
  - `POST /api/insights/{id}/approve` → đổi FE call thành `POST /api/insights/{id}/decision` (backend đã có từ T02)
  - `POST /api/batches/{id}/cancel` → xác minh backend route, fix mismatch
  - `POST /api/admin/mfa/enroll` → đổi FE call thành `POST /api/admin/mfa`
- [ ] Ghi lại 9 cases còn lại trong audit log (không ảnh hưởng user)

### 2.2 Cancel Render Job UI

- [ ] Component `<CancelRenderButton>` trong `apps/web/components/cancel-render-button.tsx`
- [ ] Hiển thị button "Hủy render" chỉ khi `status === 'running'`
- [ ] Click → mở `<ConfirmDialog>` → confirm → call `POST /api/jobs/{job_id}/cancel`
- [ ] Sau cancel: poll status cho đến `cancelled` (max 30s)
- [ ] Wire vào `<VideoPreview>` component (đã nằm trong pipeline workspace)
- [ ] Test: cancel render đang chạy, verify status đổi → MP4 không corrupt

### 2.3 Dead services cleanup

- [ ] Decision matrix cho 6 services:
  - `backup.py` → KEEP (sẽ dùng trong P6 admin)
  - `usage_tracker.py` → KEEP (chờ Phase 7)
  - `config_watcher.py` → WIRE it (P1 task) hoặc document defer
  - `media_pipeline.py` → KEEP (FFmpeg helpers centralization)
  - `youtube.py` → REMOVE (không cần, transcript dùng engine khác)
  - `comments_provider.py` → KEEP (used by `ingest_comments.py` task)
- [ ] Nếu KEEP: thêm `__all__` declaration, add docstring header, ensure pytest covers
- [ ] Nếu REMOVE: delete file, remove imports, update tests

### 2.4 config_watcher.py wire

- [ ] Trong `apps/worker/celery_app.py`: thêm `worker_ready` signal hook → `start_watcher()` background thread
- [ ] Log: `[config_watcher] Started on worker boot`
- [ ] Test: thay đổi routing config qua DB → verify worker in-memory cache invalidated trong <5s

## 3. Implementation Outline

### 3.1 File: `apps/web/components/cancel-render-button.tsx` (MỚI)

```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ConfirmDialog } from "@/components/confirm-dialog";

interface Props {
  projectId: string;
  jobId: string;
  status: string;
}

export function CancelRenderButton({ projectId, jobId, status }: Props) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  if (status !== "running" && status !== "pending") return null;

  const handleCancel = async () => {
    setIsLoading(true);
    try {
      const r = await fetch(`/api/jobs/${jobId}/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (!r.ok) throw new Error(`Cancel failed: ${r.status}`);
      // Poll status for cancellation confirmation
      const poll = setInterval(async () => {
        const statusRes = await fetch(`/api/jobs/${jobId}`);
        const data = await statusRes.json();
        if (data.status === "cancelled") {
          clearInterval(poll);
          setIsLoading(false);
          setIsOpen(false);
          router.refresh();
        }
      }, 2000);
      setTimeout(() => clearInterval(poll), 30000); // 30s max
    } catch (e) {
      setIsLoading(false);
      alert("Không thể hủy render: " + (e as Error).message);
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="btn btn-danger"
        disabled={isLoading}
      >
        Hủy render
      </button>
      <ConfirmDialog
        isOpen={isOpen}
        title="Hủy render?"
        message="Render hiện tại sẽ bị dừng. Output file (nếu có) sẽ bị xóa."
        onConfirm={handleCancel}
        onCancel={() => setIsOpen(false)}
        isLoading={isLoading}
      />
    </>
  );
}
```

### 3.2 File: `apps/web/components/video-preview.tsx` (SỬA)

Thêm `<CancelRenderButton>` vào render job hiện tại:

```tsx
// In VideoPreview component, find where render job is displayed:
{currentJob && (
  <div className="render-status">
    <h3>Render: {currentJob.status}</h3>
    <CancelRenderButton
      projectId={projectId}
      jobId={currentJob.id}
      status={currentJob.status}
    />
  </div>
)}
```

### 3.3 Drift fixes

**File: `apps/web/app/(dashboard)/assistants/[id]/insights/page.tsx` (SỬA)**

```tsx
// Before (line 31):
await fetch(`/api/insights/${id}/approve`, { method: "POST" });

// After:
await fetch(`/api/insights/${id}/decision`, {
  method: "POST",
  body: JSON.stringify({ decision: "approved" })
});
```

Tương tự cho `/to-project` (verify path, fix nếu drift).

### 3.4 config_watcher wire

**File: `apps/worker/celery_app.py` (SỬA)**

```python
from celery.signals import worker_ready

@worker_ready.connect
def start_config_watcher(**kwargs):
    """Start config watcher on worker boot."""
    try:
        from apps.worker.services.config_watcher import start_watcher
        start_watcher()
        logger.info("[config_watcher] Started on worker boot")
    except Exception as e:
        logger.warning(f"[config_watcher] Failed to start: {e}")
```

### 3.5 Remove dead service

**File: `apps/api/services/youtube.py` (REMOVE)**

```bash
# Verify no imports
grep -r "from apps.api.services.youtube" apps/ tests/
# If empty: delete file
git rm apps/api/services/youtube.py
```

## 4. Files thay đổi

| File | Action | LOC |
|---|---|---|
| `apps/web/components/cancel-render-button.tsx` | MỚI | +60 |
| `apps/web/components/video-preview.tsx` | SỬA | +10 |
| `apps/web/app/(dashboard)/assistants/[id]/insights/page.tsx` | SỬA | +5 |
| `apps/worker/celery_app.py` | SỬA | +15 |
| `apps/api/services/youtube.py` | REMOVE | -100 |
| `tests/web/components/test_cancel_render_button.tsx` | MỚI | +40 |
| `tests/worker/test_config_watcher_boot.py` | MỚI | +25 |

## 5. Test plan

```bash
# Frontend
pytest tests/web/components/test_cancel_render_button.tsx -v

# Backend
pytest tests/worker/test_config_watcher_boot.py -v

# E2E (verify drift fixed)
bash scripts/run_e2e_local.sh
```

## 6. Done when

- [ ] 12 drift endpoints verified, 3 fixed, 9 documented
- [ ] Cancel Render button works end-to-end
- [ ] Dead services cleanup decision matrix cho 6 files
- [ ] config_watcher starts on worker boot
- [ ] All tests pass (≥80% coverage)
- [ ] README cho tier 2 reflect changes

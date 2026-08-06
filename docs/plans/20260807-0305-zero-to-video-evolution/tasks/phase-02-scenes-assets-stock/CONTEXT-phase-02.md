# Bối cảnh Hệ thống (CONTEXT): Phase 02 — Scene Studio, Asset Management & Stock Search

## 1. Tri thức Tổng hợp
- **Đường dẫn Repomix Bundle:** `.\CONTEXT_BUNDLE.md`
- **Phase plan gốc:** `D:\appDK\docs\plans\20260807-0305-zero-to-video-evolution\phase-02-scenes-assets-stock.md`
- **Master plan:** `D:\appDK\docs\plans\20260807-0305-zero-to-video-evolution\plan.md`

## 2. Codebase Analysis (qua CodeGraph MCP)

### Discovery (từ `codegraph_explore`)
- Module `apps/web/components/scene-timeline.tsx`: hiện chỉ là list dọc các scene; cần thay bằng Scene Studio có editor + asset drawer.
- Module `apps/worker/services/scene_breaker.py`: chia paragraph + B-roll keywords; output chưa stable.
- Module `apps/worker/tasks/scene_breakdown.py`: dịch keyword VN→EN.

### Related Symbols
- `SceneTimeline` at `apps/web/components/scene-timeline.tsx`
- `SceneBreaker` at `apps/worker/services/scene_breaker.py`
- `scene_breakdown` at `apps/worker/tasks/scene_breakdown.py`
- `assets` table (Supabase) — chưa có schema production asset domain.

### Callers / Callees
- `SceneTimeline`: hiển thị từ project workspace page.
- `SceneBreaker`: được `script_generate` gọi sau khi có script.
- `scene_breakdown`: gọi `SceneBreaker` → map sang scene contract versioned.

## 3. Các File liên quan và Vai trò

### Modify
- `apps/worker/services/scene_breaker.py`: chuẩn hoá output có `scene_id` + schema_version.
- `apps/worker/tasks/scene_breakdown.py`: output scene contract v1.
- `apps/web/components/scene-timeline.tsx`: thay bằng Scene Studio (component mới sẽ tạo ở file khác, file này có thể giữ như wrapper).
- `apps/api/routers/projects.py`: bổ sung endpoints asset.

### Create
- `supabase/migrations/0024_project_scenes_assets.sql`
- `apps/api/routers/assets.py`
- `apps/api/schemas/assets.py`
- `apps/worker/services/asset_providers/base.py`
- `apps/worker/services/asset_providers/upload.py`
- `apps/worker/services/asset_providers/pexels.py`
- `apps/worker/services/asset_providers/local_placeholder.py`
- `apps/worker/tasks/materialize_asset.py`
- `apps/web/components/scene-studio.tsx`
- `apps/web/components/asset-drawer.tsx`
- `tests/api/test_assets.py`
- `tests/worker/test_asset_providers.py`

## 4. Dependencies
- **External:** fastapi, sqlalchemy, httpx (cho Pexels), supabase, R2 client.
- **Internal:** `apps.worker.services.project_context` (từ Phase 01).

## 5. Ràng buộc (Constraints)
- **Môi trường:** Windows 10/11 PowerShell.
- **Line Ending:** CRLF.
- **Source immutable:** Asset gốc KHÔNG BAO GIỜ bị ghi đè; mọi biến thể là row mới trong `asset_variants`.
- **Soft delete:** Asset đang được timeline tham chiếu chỉ soft-delete, không xoá cứng.
- **Pexels attribution:** Mọi asset từ Pexels phải lưu `license.photographer`, `license.pexels_id`, `license.url`.
- **Không commit git push:** Chờ sếp duyệt (xem `\.claude\memory\no-git-push-until-done.md`).
- **AI image/video providers KHÔNG thuộc Phase 02:** Phase 05 mới triển khai.
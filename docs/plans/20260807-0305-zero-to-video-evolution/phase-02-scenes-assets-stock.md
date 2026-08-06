# Phase 02 — Scene Studio, Asset Management và Stock Search

## Context

- `apps/worker/services/scene_breaker.py` hiện chia paragraph và tạo B-roll keywords.
- `apps/worker/tasks/scene_breakdown.py` dịch keyword VN→EN.
- `apps/web/components/scene-timeline.tsx` hiện chỉ hiển thị danh sách scene.
- R2 đã có trong hệ thống nhưng chưa có production asset domain.

## Mục tiêu

Biến scene list thành Scene Studio: user kiểm duyệt narration/prompt, tìm stock, upload asset và gán asset cho từng scene.

## Data model

Tạo migration `0024_project_scenes_assets.sql` với:

- `project_scenes`: scene contract, order, narration, prompts, estimated/actual duration, status.
- `assets`: project/scene link, source, provider, storage key, mime, dimensions, duration, license metadata, checksum, status.
- `asset_variants`: original, normalized, preview, processed.
- `asset_provider_runs`: provider request, cost, status, error, provider response metadata.

Source asset immutable. Delete là soft delete khi asset đang được timeline tham chiếu.

## Asset provider contract

```text
search(query, media_type, orientation, page)
generate(prompt, config)
upload(file)
get_metadata(asset)
materialize(remote_asset)
delete(asset)
```

Implement trước:

- Upload provider.
- Pexels search/download qua API chính thức.
- Local/generated placeholder provider để test.

AI image/video provider để Phase 05.

## UI

- Thay `SceneTimeline` bằng Scene Studio.
- Scene card có narration, prompt, duration, asset slot, status.
- Asset drawer: upload, search, preview, select.
- Mapping scene → asset có thể thay đổi mà không đổi narration.
- Save draft và dirty state.

## Implementation steps

1. Chuẩn hóa output `SceneBreaker` thành scene contract có `scene_id` và schema version.
2. Tạo asset API: list, upload init, complete, search, attach, detach.
3. Tạo presigned upload/download URL cho R2.
4. Lưu checksum và metadata sau upload/materialize.
5. Thêm Pexels adapter với attribution/license metadata.
6. Tạo scene editor và asset drawer.
7. Thêm validation: scene thiếu asset, asset không hợp lệ, duration vượt project target.
8. Viết tests provider contract, RLS, signed URL và scene ordering.

## Acceptance criteria

- Mỗi scene có thể có 0..n assets trước khi render.
- User upload được media và thấy preview.
- User tìm Pexels, chọn kết quả và materialize vào R2.
- Retry download không tạo duplicate nhờ provider id/checksum.
- Scene reorder giữ stable `scene_id`.

## Guardrails

- Hiển thị license/attribution của stock source.
- Giới hạn MIME, size, duration và dimensions.
- Scan filename/content type; không tin extension.
- Presigned URL ngắn hạn.

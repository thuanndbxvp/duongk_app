# Kế hoạch Triển khai (PLAN): Phase 02 — Scene Studio

## 1. Mục tiêu
- **Mô tả ngắn gọn:** Biến scene list thành Scene Studio — user kiểm duyệt narration/prompt, tìm stock (Pexels), upload asset, gán asset cho scene, lưu draft và dirty state.
- **Giá trị cốt lõi:** Production asset domain hoàn chỉnh, scene reorder ổn định, license attribution rõ ràng.

## 2. Kiến trúc
- **Patterns/Design:**
  - **Adapter pattern** cho asset provider (interface: search, generate, upload, get_metadata, materialize, delete).
  - **Variant table** để track mọi biến thể (original, normalized, preview, processed).
  - **Idempotency** dựa trên `provider + external_id + checksum`.
  - **Soft delete** thông qua `deleted_at` timestamp.

- **Luồng đi:**
```text
Script → SceneBreaker → scene contract v1 → Scene Studio
  User actions:
    → Upload file → R2 signed URL PUT → assets row
    → Search Pexels → download via API → R2 → assets row + license metadata
    → Assign asset → scene_assets binding
```

## 3. Lý do chọn & Phương án đã loại trừ
- **Phương án A — Dùng tên file để map scene (ĐÃ LOẠI):** Phá khi reorder; Phase 02 yêu cầu stable `scene_id`.
- **Phương án B — Lưu asset trong JSONB trên project (ĐÃ LOẠI):** Không query được, không reuse được, không có variant tracking.
- **Phương án C — Bảng `assets` riêng + `asset_variants` (CHỌN):** Chuẩn hoá, query tốt, variant tracking rõ, license metadata đầy đủ.

**Lý do chọn C:**
- Chuẩn production, dễ query, RLS-friendly.
- Variant tracking cho upscale/normalize/cleanup sau này (Phase 05).
- Provider contract giúp Phase 05 chỉ cần thêm adapter.

## 4. Rủi ro

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Asset gốc bị ghi đè khi user upload lại | Cao | Source immutable: mỗi upload là row mới. UI hiển thị "Phiên bản hiện tại". |
| Pexels trả về asset đã xoá → 404 | Trung bình | Retry không tạo duplicate nhờ `provider + external_id` unique. |
| R2 signed URL lộ | Trung bình | TTL ≤ 15 phút cho upload, ≤ 5 phút cho download. |
| User upload file quá lớn | Trung bình | Validate size (image ≤ 20MB, video ≤ 200MB, audio ≤ 50MB) bằng Pydantic. |
| MIME không khớp extension | Thấp | Magic byte scan trước khi accept. |
| Asset gán cho nhiều scene | Thấp | Bảng `scene_assets` riêng (n-n). |

## 5. Nỗ lực
- **Estimated LOC:** ~1100 (SQL ~250, Python backend ~550, Next.js ~300).
- **Timeline:** 8 micro-steps, ước tính 4–5 ngày cho Tier 2.
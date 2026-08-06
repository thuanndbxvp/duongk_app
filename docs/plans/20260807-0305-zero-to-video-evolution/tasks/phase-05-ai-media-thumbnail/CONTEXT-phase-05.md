# CONTEXT: Phase 05 — AI Media, Upscale, Thumbnail & Metadata

## 1. Repomix
- `.\CONTEXT_BUNDLE.md`

## 2. Codebase Analysis
- `service_routing_config` đã có (sẵn từ admin plan).
- `assets` table từ Phase 02.
- `asset_provider_runs` table từ Phase 02.

## 3. Files
### Modify
- `apps/worker/services/asset_providers/`: thêm adapter mới (gemini, nanobanana, flux, sdxl).
- `apps/api/routers/assets.py`: thêm endpoints `generate-image`, `generate-video`, `upscale`, `thumbnail-gen`.

### Create
- `supabase/migrations/0027_ai_media.sql` (nếu cần thêm bảng)
- `apps/worker/services/media_pipeline.py`
- `apps/worker/services/watermark_cleanup.py`
- `apps/worker/tasks/thumbnail_generate.py`
- `apps/worker/tasks/metadata_package.py`
- `apps/api/routers/thumbnail.py`
- `apps/api/schemas/thumbnail.py`
- `apps/web/components/thumbnail-picker.tsx`
- `tests/worker/test_media_pipeline.py`
- `tests/worker/test_watermark_cleanup.py`

## 4. Dependencies
- google-generativeai (Gemini SDK)
- replicate (Nano Banana / Flux)
- stability-sdk (SDXL nếu cần)
- LaMa hoặc MI-GAN model weights (cho watermark cleanup)

## 5. Ràng buộc
- **KHÔNG sniff token, CAPTCHA bypass, private endpoint.**
- Watermark cleanup **CHỈ** chạy khi có `provenance_record` + user consent (gate).
- Source asset immutable — mọi output là `asset_variants` row mới.
- Preview bắt buộc trước khi commit cleanup.
- Capability probe trước khi dùng provider.
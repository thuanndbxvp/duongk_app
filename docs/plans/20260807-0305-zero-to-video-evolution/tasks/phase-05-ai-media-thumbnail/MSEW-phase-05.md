# MSEW: Phase 05 — AI Media, Thumbnail

## Prerequisites
- Branch: `feature/phase-05-ai-media`.
- Phase 02 + Phase 04 merged.
- Provider API keys trong `api_provider_keys` (Vault).

## Files KHÔNG được đụng
- `apps/worker/services/asset_providers/upload.py`, `pexels.py`, `local_placeholder.py` (Phase 02).
- `apps/worker/tasks/render_video.py` (Phase 04).

---

## Micro-Steps

### Step 1: Capability probe
**File:** `apps/worker/services/capability_probe.py`

```python
# Gọi mỗi provider 1 request rẻ (list model / get quota) để xác nhận capability.
# Lưu kết quả vào provider_health_snapshots (Phase 10 sẽ tận dụng).
```

---

### Step 2: Image/video provider adapters
**File:** `apps/worker/services/asset_providers/gemini.py`, `nanobanana.py`, `flux.py`, `sdxl.py`

Mỗi adapter implement `AssetProvider.search/generate/materialize`. Dùng SDK chính thức + API key từ Vault.

---

### Step 3: Media pipeline
**File:** `apps/worker/services/media_pipeline.py`

```python
async def run(asset_id: UUID, ops: list[Literal["normalize","upscale","cleanup","resize"]]) -> AssetVariant:
    # 1. Load source asset → local temp
    # 2. Apply ops theo thứ tự
    # 3. Nếu cleanup → check consent + provenance trước
    # 4. Validate output (dimensions, MIME)
    # 5. Upload R2 → tạo asset_variants row
    # 6. Atomic move: chỉ update asset.status='ready' sau khi upload OK
```

---

### Step 4: Watermark cleanup
**File:** `apps/worker/services/watermark_cleanup.py`

```python
async def cleanup(asset_id: UUID, user_consent_id: UUID) -> AssetVariant:
    # 1. Verify consent_record.user_id == owner
    # 2. Load source → detect watermark boxes (model AI)
    # 3. Tạo preview image với box overlay → upload preview R2
    # 4. Trả preview asset_id cho UI confirm
    # 5. User approve → inpaint vào temp output
    # 6. Validate → upload → atomic move
    # 7. Ghi audit log: ai approved, lúc nào, consent_id
```

Endpoint:
- `POST /api/assets/{id}/cleanup/preview` → tạo preview, KHÔNG inpaint.
- `POST /api/assets/{id}/cleanup/approve` → user confirm → inpaint.
- `POST /api/assets/{id}/cleanup/reject` → hủy.

---

### Step 5: Thumbnail generation
**File:** `apps/worker/tasks/thumbnail_generate.py`

```python
async def generate(project_id: UUID, brief: dict) -> list[AssetVariant]:
    # 1. 3–5 candidates qua provider (Gemini hoặc Nano Banana)
    # 2. 1280x720, text legibility check
    # 3. AI vision score contrast/composition
    # 4. Lưu candidates là asset_variants với role='thumbnail_candidate'
    # 5. User chọn 1 → attach vào project
```

---

### Step 6: Metadata package
**File:** `apps/worker/tasks/metadata_package.py`

```python
async def build(project_id: UUID) -> dict:
    # Title candidates, description, tags, chapters, hashtags, thumbnail path, srt path.
    # Output JSON lưu vào project_exports (sẽ tạo bảng nếu chưa có).
```

---

### Step 7: API endpoints

```python
# POST /api/projects/{id}/thumbnail/generate
# GET /api/projects/{id}/thumbnail/candidates
# POST /api/projects/{id}/thumbnail/select
# POST /api/projects/{id}/metadata/build
# GET /api/projects/{id}/metadata
```

---

### Step 8: UI thumbnail picker

`apps/web/components/thumbnail-picker.tsx` — gallery + score + select.

---

### Step 9: Tests

Test cases:
- Cleanup không có consent → 403.
- Cleanup preview KHÔNG tạo asset_variants thật.
- Approve preview → tạo variant mới, KHÔNG ghi đè source.
- Thumbnail generation tạo 3–5 candidates đúng size 1280x720.
- Metadata package có trường title, description, tags, thumbnail.
- Capability probe fail → provider không dùng được trong route.
- Credit hold/commit/refund khi provider fail một phần.

```powershell
pytest tests/worker/test_media_pipeline.py tests/worker/test_watermark_cleanup.py -v --cov=apps.worker.services.media_pipeline --cov=apps.worker.services.watermark_cleanup --cov-report=term-missing
```
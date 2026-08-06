# MSEW: Phase 02 — Scene Studio, Asset Management & Stock Search

## Prerequisites
- **Repomix bundle:** Tier 2 chạy `repomix --include "apps/web/components/scene-timeline.tsx,apps/worker/services/scene_breaker.py,apps/worker/tasks/scene_breakdown.py,supabase/migrations/**" --output CONTEXT_BUNDLE.md`.
- **Branch:** `git checkout -b feature/phase-02-scene-asset`.
- **Phase 01 phải merged:** Cần schema `projects` + `project_briefs` từ Phase 01.

## Skill Routing Summary
| Step | Tiêu đề | Primary | Reference | Fallback |
|------|---------|---------|-----------|----------|
| 1 | Migration SQL | `databases` | `backend-development` | `debugging` |
| 2 | Pydantic schemas | `backend-development` | `databases` | `debugging` |
| 3 | Provider contract + 3 adapter | `backend-development` | `planning` | `debugging` |
| 4 | FastAPI router assets | `backend-development` | `databases` | `debugging` |
| 5 | Materialize task | `backend-development` | `databases` | `debugging` |
| 6 | Scene Studio UI | `frontend-development` | `ui-styling` | `aesthetic` |
| 7 | Asset drawer UI | `frontend-development` | `ui-styling` | `aesthetic` |
| 8 | Tests | `testing-protocol` | `debugging-protocol` | `debugging` |

## Files KHÔNG được đụng
- `apps/web/app/(dashboard)/channels/**` — flow cũ.
- `apps/worker/tasks/script_generate.py` — Phase 01 đụng, Phase 02 KHÔNG đụng.
- `supabase/migrations/0001_to_0023_*.sql` — append only.
- `apps/web/components/scene-timeline.tsx` — KHÔNG xoá; có thể wrap hoặc giữ nguyên làm fallback.

---

## Micro-Steps

### Step 1: Migration `0024_project_scenes_assets.sql`
**File:** `supabase/migrations/0024_project_scenes_assets.sql`
**Skill:** `databases` + `backend-development`.

```sql
-- project_scenes
CREATE TABLE IF NOT EXISTS public.project_scenes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  scene_id text NOT NULL,
  scene_index int NOT NULL,
  schema_version smallint NOT NULL DEFAULT 1,
  narration text NOT NULL DEFAULT '',
  visual_description text NOT NULL DEFAULT '',
  image_prompt text NOT NULL DEFAULT '',
  video_prompt text NOT NULL DEFAULT '',
  asset_type text NOT NULL DEFAULT 'image' CHECK (asset_type IN ('image', 'video')),
  estimated_duration numeric(6,2) NOT NULL DEFAULT 0,
  characters jsonb NOT NULL DEFAULT '[]'::jsonb,
  background text NOT NULL DEFAULT '',
  continuity_references jsonb NOT NULL DEFAULT '[]'::jsonb,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'ready', 'rendered', 'failed')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id, scene_id)
);

CREATE INDEX idx_project_scenes_project ON public.project_scenes(project_id, scene_index);

-- assets
CREATE TABLE IF NOT EXISTS public.assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  source text NOT NULL CHECK (source IN ('upload', 'pexels', 'local_placeholder', 'ai_generated', 'gemini', 'nanobanana', 'flux', 'sdxl')),
  provider_id text NULL,
  storage_key text NOT NULL,
  mime_type text NOT NULL,
  size_bytes bigint NOT NULL CHECK (size_bytes > 0),
  width int NULL,
  height int NULL,
  duration_seconds numeric(10,3) NULL,
  checksum text NOT NULL,
  license jsonb NOT NULL DEFAULT '{}'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  status text NOT NULL DEFAULT 'ready' CHECK (status IN ('uploading', 'ready', 'processing', 'failed', 'deleted')),
  deleted_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (owner_id, source, provider_id),
  UNIQUE (owner_id, checksum)
);

CREATE INDEX idx_assets_owner_status ON public.assets(owner_id, status) WHERE deleted_at IS NULL;

-- asset_variants
CREATE TABLE IF NOT EXISTS public.asset_variants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id uuid NOT NULL REFERENCES public.assets(id) ON DELETE CASCADE,
  variant_kind text NOT NULL CHECK (variant_kind IN ('original', 'normalized', 'preview', 'processed', 'upscaled', 'cleaned')),
  storage_key text NOT NULL,
  mime_type text NOT NULL,
  width int NULL,
  height int NULL,
  duration_seconds numeric(10,3) NULL,
  checksum text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_asset_variants_asset ON public.asset_variants(asset_id, variant_kind);

-- scene_assets
CREATE TABLE IF NOT EXISTS public.scene_assets (
  scene_id uuid NOT NULL REFERENCES public.project_scenes(id) ON DELETE CASCADE,
  asset_id uuid NOT NULL REFERENCES public.assets(id) ON DELETE RESTRICT,
  variant_id uuid NULL REFERENCES public.asset_variants(id) ON DELETE SET NULL,
  role text NOT NULL DEFAULT 'primary' CHECK (role IN ('primary', 'broll', 'backup')),
  position int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (scene_id, asset_id, role)
);

CREATE INDEX idx_scene_assets_scene ON public.scene_assets(scene_id);

-- asset_provider_runs
CREATE TABLE IF NOT EXISTS public.asset_provider_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id uuid NULL REFERENCES public.assets(id) ON DELETE SET NULL,
  provider text NOT NULL,
  operation text NOT NULL,
  request_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  response_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  cost_cents int NULL,
  status text NOT NULL,
  error_code text NULL,
  error_message text NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz NULL
);

-- RLS
ALTER TABLE public.project_scenes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.asset_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scene_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.asset_provider_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "project_scenes_owner_all" ON public.project_scenes
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_scenes.project_id AND p.user_id = auth.uid()))
  WITH CHECK (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_scenes.project_id AND p.user_id = auth.uid()));

CREATE POLICY "assets_owner_all" ON public.assets FOR ALL
  USING (owner_id = auth.uid()) WITH CHECK (owner_id = auth.uid());

CREATE POLICY "asset_variants_owner_all" ON public.asset_variants FOR ALL
  USING (EXISTS (SELECT 1 FROM public.assets a WHERE a.id = asset_variants.asset_id AND a.owner_id = auth.uid()))
  WITH CHECK (EXISTS (SELECT 1 FROM public.assets a WHERE a.id = asset_variants.asset_id AND a.owner_id = auth.uid()));

CREATE POLICY "scene_assets_owner_all" ON public.scene_assets FOR ALL
  USING (EXISTS (
    SELECT 1 FROM public.project_scenes s
    JOIN public.projects p ON p.id = s.project_id
    WHERE s.id = scene_assets.scene_id AND p.user_id = auth.uid()
  ));

CREATE POLICY "asset_provider_runs_owner_select" ON public.asset_provider_runs FOR SELECT
  USING (asset_id IS NULL OR EXISTS (SELECT 1 FROM public.assets a WHERE a.id = asset_provider_runs.asset_id AND a.owner_id = auth.uid()));
```

**Verify:**
```powershell
supabase db reset
psql -h localhost -p 54322 -U postgres -d postgres -c "\d public.assets"
```

---

### Step 2: Pydantic schemas assets
**File:** `apps/api/schemas/assets.py`

```python
from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field

AssetSource = Literal["upload", "pexels", "local_placeholder", "ai_generated", "gemini", "nanobanana", "flux", "sdxl"]
AssetStatus = Literal["uploading", "ready", "processing", "failed", "deleted"]
AssetType = Literal["image", "video", "audio"]

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_VIDEO_BYTES = 200 * 1024 * 1024
MAX_AUDIO_BYTES = 50 * 1024 * 1024

class AssetUploadInitRequest(BaseModel):
    model_config = {"extra": "forbid"}
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(pattern=r"^(image|video|audio)/.+")
    size_bytes: int = Field(gt=0)
    checksum: str = Field(min_length=32, max_length=128)
    width: Optional[int] = Field(default=None, gt=0)
    height: Optional[int] = Field(default=None, gt=0)
    duration_seconds: Optional[float] = Field(default=None, gt=0)

    @property
    def max_bytes(self) -> int:
        if self.mime_type.startswith("image/"): return MAX_IMAGE_BYTES
        if self.mime_type.startswith("video/"): return MAX_VIDEO_BYTES
        if self.mime_type.startswith("audio/"): return MAX_AUDIO_BYTES
        return MAX_IMAGE_BYTES


class AssetUploadCompleteRequest(BaseModel):
    model_config = {"extra": "forbid"}
    asset_id: UUID
    final_checksum: str
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None


class AssetSearchRequest(BaseModel):
    model_config = {"extra": "forbid"}
    provider: Literal["pexels"]
    query: str = Field(min_length=1, max_length=200)
    media_type: AssetType = "image"
    orientation: Optional[Literal["landscape", "portrait", "square"]] = None
    page: int = Field(default=1, ge=1, le=50)


class AssetResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    source: AssetSource
    storage_key: str
    mime_type: str
    size_bytes: int
    width: Optional[int]
    height: Optional[int]
    duration_seconds: Optional[float]
    license: dict
    status: AssetStatus
    created_at: datetime


class SceneAssetBindingRequest(BaseModel):
    model_config = {"extra": "forbid"}
    scene_id: UUID
    asset_id: UUID
    variant_id: Optional[UUID] = None
    role: Literal["primary", "broll", "backup"] = "primary"
    position: int = Field(default=0, ge=0)
```

**Verify:**
```powershell
pytest tests/api/test_schemas_assets.py -v
```

---

### Step 3: Provider contract + 3 adapter
**File:** `apps/worker/services/asset_providers/base.py`

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class AssetMetadata:
    provider_id: str
    mime_type: str
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    license: dict = None
    raw_metadata: dict = None


@dataclass(frozen=True)
class SearchResult:
    provider_id: str
    preview_url: str
    download_url: str
    metadata: AssetMetadata


class AssetProvider(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, media_type: str, orientation: Optional[str], page: int) -> list[SearchResult]: ...

    @abstractmethod
    async def materialize(self, provider_id: str) -> AssetMetadata: ...
```

**File:** `apps/worker/services/asset_providers/upload.py`
```python
from .base import AssetProvider, AssetMetadata, SearchResult

class UploadProvider(AssetProvider):
    name = "upload"
    async def search(self, *a, **kw): return []
    async def materialize(self, provider_id): raise NotImplementedError("upload không cần materialize")
```

**File:** `apps/worker/services/asset_providers/pexels.py`
```python
import httpx
from .base import AssetProvider, AssetMetadata, SearchResult

class PexelsProvider(AssetProvider):
    name = "pexels"
    BASE = "https://api.pexels.com"
    def __init__(self, api_key: str):
        self.api_key = api_key
    async def search(self, query, media_type="image", orientation=None, page=1) -> list[SearchResult]:
        # ... gọi /v1/search qua API key từ api_provider_keys
        ...
    async def materialize(self, provider_id) -> AssetMetadata:
        # download qua httpx → upload lên R2
        ...
```

**File:** `apps/worker/services/asset_providers/local_placeholder.py`
- Dùng cho test/dev. Sinh ảnh SVG đơn giản.

---

### Step 4: FastAPI router `/api/assets`
**File:** `apps/api/routers/assets.py`

Endpoints:
- `POST /api/assets/upload-init` → trả `asset_id` + signed URL.
- `POST /api/assets/upload-complete` → verify checksum.
- `POST /api/assets/search` → gọi provider adapter.
- `POST /api/assets/materialize/{provider}/{provider_id}` → enqueue materialize task.
- `POST /api/scenes/{scene_id}/assets` → binding.
- `DELETE /api/scenes/{scene_id}/assets/{asset_id}` → unbind (KHÔNG xoá asset).

**KHÔNG đụng:**
- Router cũ.
- Endpoint `/api/projects/{id}/approve` từ Phase 01.

---

### Step 5: Materialize task
**File:** `apps/worker/tasks/materialize_asset.py`

Idempotency key: `(source, provider_id, checksum)`.

```python
import hashlib
@celery_app.task(name="materialize_asset", bind=True, max_retries=3)
def materialize_asset(self, asset_id: str, provider: str, provider_id: str):
    # 1. Check asset row đã ready chưa → idempotent skip
    # 2. Gọi provider.materialize(provider_id)
    # 3. Upload lên R2 với storage_key đã sinh
    # 4. Tạo asset_variants row (variant_kind='original')
    # 5. Update asset.status = 'ready'
```

---

### Step 6: Scene Studio UI
**File:** `apps/web/components/scene-studio.tsx` + sửa `apps/web/app/(dashboard)/projects/[id]/page.tsx`

- Scene card có: narration, prompt, duration, asset slot, status.
- Drag-drop reorder (giữ stable scene_id).
- Nút mở Asset Drawer.

---

### Step 7: Asset Drawer UI
**File:** `apps/web/components/asset-drawer.tsx`

- 3 tab: Upload / Search Pexels / My Library.
- Preview thumbnail.
- Nút "Assign to scene".

---

### Step 8: Tests
**File:** `tests/api/test_assets.py`, `tests/worker/test_asset_providers.py`

Test cases:
- Upload-init trả signed URL với TTL ≤ 15 phút.
- Upload-complete với checksum sai → 422.
- Search Pexels với query rỗng → 422.
- Materialize asset đã ready → idempotent skip.
- Soft-delete asset đang ở scene_assets → status='deleted' nhưng row còn.
- RLS: user B không select asset của user A.

**Verify:**
```powershell
pytest tests/api/test_assets.py tests/worker/test_asset_providers.py -v --cov=apps.api.routers.assets --cov=apps.worker.services.asset_providers --cov-report=term-missing
```

**Expected:** Coverage ≥80%.
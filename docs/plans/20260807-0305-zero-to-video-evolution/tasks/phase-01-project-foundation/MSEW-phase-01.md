# MSEW: Phase 01 — Project foundation & Blank Project

## Prerequisites (Điều kiện tiên quyết)
- **Repomix bundle:** Tier 2 chạy `repomix --include "apps/web/app/(dashboard)/projects/**,apps/api/**,apps/worker/tasks/script_generate.py,apps/worker/services/rag_service.py,supabase/migrations/**" --output CONTEXT_BUNDLE.md` trước khi code.
- **Branch:** Tạo nhánh mới từ main: `git checkout -b feature/phase-01-project-foundation`.
- **Python venv activated:** Bắt buộc Tier 2 gọi: `.\venv\Scripts\Activate.ps1`
- **Database local:** Supabase local phải đang chạy: `supabase status`.

## Skill Routing Summary
| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | Migration SQL + RLS | `databases` | `backend-development` | `debugging` |
| 2 | Pydantic schemas | `backend-development` | `databases` | `debugging` |
| 3 | FastAPI router projects | `backend-development` | `databases` | `debugging` |
| 4 | Service project_context | `backend-development` | `planning` | `debugging` |
| 5 | Sửa script_generate | `backend-development` | `planning` | `debugging` |
| 6 | Sửa scene_breakdown | `backend-development` | `planning` | `debugging` |
| 7 | Next.js project wizard | `frontend-development` | `ui-styling` | `aesthetic` |
| 8 | Project workspace page | `frontend-development` | `ui-styling` | `aesthetic` |
| 9 | Tests API/RLS/task | `testing-protocol` | `debugging-protocol` | `debugging` |

## Files KHÔNG được đụng (Do Not Touch)
- `apps/worker/tasks/scene_breaker.py` — Lý do: Logic chia paragraph/WPM đang chạy production; Phase 01 chưa refactor.
- `apps/web/app/(dashboard)/channels/**` — Lý do: Flow cũ phải giữ nguyên 100%.
- `supabase/migrations/0001_to_0022_*.sql` — Lý do: Migration cũ KHÔNG BAO GIỜ chỉnh sửa, chỉ append mới.
- `apps/api/main.py` (ngoài phần mount router) — Lý do: Chỉ thêm `app.include_router(projects.router)`, không đụng phần khác.

---

## Micro-Steps

### Step 1: Tạo migration `0023_projects_foundation.sql`
**File:** `supabase/migrations/0023_projects_foundation.sql` (TẠO MỚI)
**Vị trí:** Append sau migration 0022.
**Skill Invocation:**
  - **Primary:** `databases` — Migration SQL + RLS là phần việc của databases.
  - **Reference:** `backend-development` — Cross-check với Pydantic schema.
  - **Fallback:** `debugging` — Nếu migration fail.

**Pre-check (CodeGraph):**
- `codegraph_search`: `channel_assistants` ➔ verify existing schema.
- `codegraph_search`: `projects` ➔ confirm chưa tồn tại (tránh collision).

**Code cần viết:**
```sql
-- Bảng projects: root entity mới
CREATE TABLE IF NOT EXISTS public.projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  channel_assistant_id uuid NULL REFERENCES public.channel_assistants(id) ON DELETE SET NULL,
  mode text NOT NULL CHECK (mode IN ('blank', 'clone_channel')),
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'awaiting_approval', 'approved', 'rejected', 'archived')),
  approval_state text NOT NULL DEFAULT 'draft' CHECK (approval_state IN ('draft', 'awaiting_approval', 'approved', 'rejected')),
  brief_hash text NOT NULL,
  schema_version smallint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  approved_at timestamptz NULL,
  UNIQUE (user_id, brief_hash)
);

-- Bảng project_briefs: versioned creative brief
CREATE TABLE IF NOT EXISTS public.project_briefs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  version smallint NOT NULL,
  topic text NOT NULL,
  audience text NULL,
  language text NOT NULL DEFAULT 'vi',
  duration_target_seconds integer NOT NULL CHECK (duration_target_seconds > 0 AND duration_target_seconds <= 3600),
  aspect_ratio text NOT NULL DEFAULT '16:9' CHECK (aspect_ratio IN ('16:9', '9:16', '1:1')),
  tone text NULL,
  visual_style text NULL,
  voice_profile_id uuid NULL,
  music_mood text NULL,
  payload jsonb NOT NULL,
  schema_version smallint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id, version)
);

-- Bảng project_stage_events: log stage transitions
CREATE TABLE IF NOT EXISTS public.project_stage_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  stage text NOT NULL,
  status text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_projects_user_id ON public.projects(user_id);
CREATE INDEX idx_projects_channel_assistant_id ON public.projects(channel_assistant_id) WHERE channel_assistant_id IS NOT NULL;
CREATE INDEX idx_project_briefs_project_id ON public.project_briefs(project_id);
CREATE INDEX idx_project_stage_events_project_id_occurred_at ON public.project_stage_events(project_id, occurred_at DESC);

-- RLS
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_briefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_stage_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "projects_select_own" ON public.projects FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "projects_insert_own" ON public.projects FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "projects_update_own" ON public.projects FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "projects_delete_own" ON public.projects FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "project_briefs_select_own" ON public.project_briefs FOR SELECT
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_briefs.project_id AND p.user_id = auth.uid()));
CREATE POLICY "project_briefs_insert_own" ON public.project_briefs FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_briefs.project_id AND p.user_id = auth.uid()));
CREATE POLICY "project_briefs_update_own" ON public.project_briefs FOR UPDATE
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_briefs.project_id AND p.user_id = auth.uid()));

CREATE POLICY "project_stage_events_select_own" ON public.project_stage_events FOR SELECT
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_stage_events.project_id AND p.user_id = auth.uid()));
CREATE POLICY "project_stage_events_insert_own" ON public.project_stage_events FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_stage_events.project_id AND p.user_id = auth.uid()));

-- updated_at trigger
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_projects_updated_at BEFORE UPDATE ON public.projects
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
```

**KHÔNG được sửa:**
- File này append mới; KHÔNG đụng `0001_to_0022`.

**Verify command (PowerShell):**
```powershell
supabase db reset
supabase status
psql -h localhost -p 54322 -U postgres -d postgres -c "\d public.projects"
```

**Expected output:**
```text
 Table "public.projects"
 Column | Type | ...
 id | uuid | ...
 user_id | uuid | ...
 ...
```

**Nếu fail:**
- Invoke skill `debugging`.
- Ghi BLOCKERS.md.
- **CẤM TỰ SỬA migration cũ.**

---

### Step 2: Pydantic schemas
**File:** `apps/api/schemas/projects.py` (TẠO MỚI)
**Vị trí:** Module mới trong `apps/api/schemas/`.
**Skill Invocation:**
  - **Primary:** `backend-development` — Pydantic v2 là việc của backend.
  - **Reference:** `databases` — Cross-check enum values với SQL CHECK constraints.
  - **Fallback:** `debugging`.

**Pre-check (CodeGraph):**
- `codegraph_search`: `channel_assistant` ➔ tìm Pydantic hiện có để tái sử dụng pattern.

**Import cần thêm:**
```python
from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator
import hashlib
import json
```

**Code cần viết:**
```python
SCHEMA_VERSION: Literal[1] = 1

ProjectMode = Literal["blank", "clone_channel"]
ProjectStatus = Literal["draft", "awaiting_approval", "approved", "rejected", "archived"]
ApprovalState = Literal["draft", "awaiting_approval", "approved", "rejected"]
AspectRatio = Literal["16:9", "9:16", "1:1"]


class CreativeBriefPayload(BaseModel):
    model_config = {"extra": "forbid"}
    schema_version: Literal[1] = SCHEMA_VERSION
    topic: str = Field(min_length=3, max_length=500)
    audience: Optional[str] = Field(default=None, max_length=500)
    language: str = Field(default="vi", min_length=2, max_length=8)
    duration_target_seconds: int = Field(gt=0, le=3600)
    aspect_ratio: AspectRatio = "16:9"
    tone: Optional[str] = Field(default=None, max_length=200)
    visual_style: Optional[str] = Field(default=None, max_length=200)
    voice_profile_id: Optional[UUID] = None
    music_mood: Optional[str] = Field(default=None, max_length=200)

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(), sort_keys=True, separators=(",", ":"))

    def brief_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


class ProjectCreate(BaseModel):
    model_config = {"extra": "forbid"}
    mode: ProjectMode
    channel_assistant_id: Optional[UUID] = None
    brief: CreativeBriefPayload

    @model_validator(mode="after")
    def check_clone_requires_assistant(self):
        if self.mode == "clone_channel" and self.channel_assistant_id is None:
            raise ValueError("clone_channel mode requires channel_assistant_id")
        return self


class ProjectBriefResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    project_id: UUID
    version: int
    payload: dict
    schema_version: Literal[1]
    created_at: datetime


class ProjectResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    user_id: UUID
    channel_assistant_id: Optional[UUID]
    mode: ProjectMode
    status: ProjectStatus
    approval_state: ApprovalState
    brief_hash: str
    schema_version: Literal[1]
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime]


class ProjectApproveRequest(BaseModel):
    model_config = {"extra": "forbid"}
    decision: Literal["approved", "rejected"]
    notes: Optional[str] = Field(default=None, max_length=1000)


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    next_cursor: Optional[str] = None
```

**KHÔNG được sửa:**
- Các file Pydantic khác ngoài `projects.py`.
- KHÔNG expose internal helpers như `canonical_json` ra router.

**Verify command (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
pytest tests/api/test_schemas_projects.py -v
```

**Expected output:**
```text
tests/api/test_schemas_projects.py::test_brief_hash_stable PASSED
tests/api/test_schemas_projects.py::test_clone_requires_assistant PASSED
...
```

**Nếu fail:** Gọi `debugging-protocol` skill, KHÔNG tự đổi schema field.

---

### Step 3: FastAPI router `/api/projects`
**File:** `apps/api/routers/projects.py` (TẠO MỚI)
**Vị trí:** Module mới trong `apps/api/routers/`.
**Skill Invocation:** `backend-development` + `databases` (RLS check).

**Pre-check (CodeGraph):**
- `codegraph_search`: `channel_assistants` router ➔ xem pattern CRUD đang dùng.

**Import cần thêm:**
```python
from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.deps import get_db, get_current_user
from apps.api.schemas.projects import (
    ProjectCreate, ProjectResponse, ProjectBriefResponse, ProjectApproveRequest, ProjectListResponse
)
from apps.worker.services.project_context import build_project_context
```

**Code cần viết:**
```python
router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
):
    brief_hash = payload.brief.brief_hash()
    existing = await db.execute(
        select(Project).where(Project.user_id == user_id, Project.brief_hash == brief_hash)
    )
    project = existing.scalar_one_or_none()
    if project:
        return ProjectResponse.model_validate(project)

    project = Project(
        user_id=user_id,
        mode=payload.mode,
        channel_assistant_id=payload.channel_assistant_id,
        brief_hash=brief_hash,
        status="draft",
        approval_state="draft",
        schema_version=1,
    )
    db.add(project)
    await db.flush()
    brief = ProjectBrief(
        project_id=project.id,
        version=1,
        payload=payload.brief.model_dump(),
        schema_version=1,
    )
    db.add(brief)
    await db.commit()
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db), user_id: UUID = Depends(get_current_user)):
    project = await db.get(Project, project_id)
    if project is None or project.user_id != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.get("", response_model=ProjectListResponse)
async def list_projects(db: AsyncSession = Depends(get_db), user_id: UUID = Depends(get_current_user), limit: int = Query(20, ge=1, le=100), cursor: Optional[str] = None):
    q = select(Project).where(Project.user_id == user_id).order_by(Project.created_at.desc()).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return ProjectListResponse(items=[ProjectResponse.model_validate(r) for r in rows])


@router.post("/{project_id}/approve", response_model=ProjectResponse)
async def approve_project(project_id: UUID, payload: ProjectApproveRequest, db: AsyncSession = Depends(get_db), user_id: UUID = Depends(get_current_user)):
    project = await db.get(Project, project_id)
    if project is None or project.user_id != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    project.approval_state = payload.decision
    project.approved_at = datetime.utcnow() if payload.decision == "approved" else None
    db.add(ProjectStageEvent(project_id=project.id, stage="approval", status=payload.decision, payload={"notes": payload.notes}))
    await db.commit()
    return ProjectResponse.model_validate(project)
```

**Mount router trong `apps/api/main.py`** — chỉ thêm dòng:
```python
from apps.api.routers import projects  # noqa: E402
app.include_router(projects.router)
```

**KHÔNG được sửa:**
- Phần code khác của `apps/api/main.py`.
- KHÔNG tạo router mới ngoài `/api/projects`.

**Verify command:**
```powershell
.\venv\Scripts\Activate.ps1
uvicorn apps.api.main:app --reload
Invoke-RestMethod -Uri "http://localhost:8000/api/projects" -Method Get -Headers @{Authorization="Bearer $TOKEN"}
```

**Expected output:** JSON `{ items: [...], next_cursor: null }` hoặc `401` nếu chưa auth.

---

### Step 4: Service `project_context.py`
**File:** `apps/worker/services/project_context.py` (TẠO MỚI)
**Skill Invocation:** `backend-development` + `planning`.

**Code cần viết:**
```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.models import Project, ProjectBrief, ChannelAssistant
from apps.worker.services.rag_service import build_context


@dataclass(frozen=True)
class ProjectContext:
    project_id: UUID
    mode: str
    brief_payload: dict
    channel_dna: Optional[dict]
    rag_context: str


async def build_project_context(db: AsyncSession, project_id: UUID) -> ProjectContext:
    project = await db.get(Project, project_id)
    if project is None:
        raise ValueError(f"Project {project_id} not found")
    brief = (await db.execute(
        select(ProjectBrief).where(ProjectBrief.project_id == project_id).order_by(ProjectBrief.version.desc()).limit(1)
    )).scalar_one_or_none()
    if brief is None:
        raise ValueError(f"No brief for project {project_id}")

    channel_dna: Optional[dict] = None
    if project.channel_assistant_id is not None:
        assistant = await db.get(ChannelAssistant, project.channel_assistant_id)
        if assistant is not None:
            channel_dna = assistant.dna_payload

    rag_context = await build_context(
        brief=brief.payload,
        channel_dna=channel_dna,
        fallback_preset="blank_default" if project.mode == "blank" else None,
    )
    return ProjectContext(
        project_id=project_id,
        mode=project.mode,
        brief_payload=brief.payload,
        channel_dna=channel_dna,
        rag_context=rag_context,
    )
```

**Post-verify (CodeGraph):**
- `codegraph_callers`: `build_context` ➔ thêm 1 caller (build_project_context).

---

### Step 5: Sửa `script_generate.py`
**File:** `apps/worker/tasks/script_generate.py` (SỬA)
**Skill Invocation:** `backend-development` + `planning`.

**Pre-check (CodeGraph):**
- `codegraph_callers`: `script_generate` ➔ ghi lại số callers.
- `codegraph_callees`: `script_generate` ➔ xem chuỗi call.

**Code cần thêm/sửa:**
```python
# Thêm signature mới, giữ backward compat
async def run_script_generate(project_id: UUID, *, brief_version: int = 1, idempotency_key: Optional[str] = None) -> dict:
    async with session_scope() as db:
        ctx = await build_project_context(db, project_id)
        # ... dùng ctx.brief_payload, ctx.channel_dna, ctx.rag_context
        # ... map output sang schema versioned
```

**KHÔNG được sửa:**
- Hàm cũ `run_script_generate(assistant_id=...)` — vẫn giữ như wrapper, không xoá.

---

### Step 6: Sửa `scene_breakdown.py`
**File:** `apps/worker/tasks/scene_breakdown.py` (SỬA)
**Skill Invocation:** `backend-development`.

**Code cần thêm:**
```python
SCENE_CONTRACT_VERSION: Literal[1] = 1

def wrap_scene_contract(scene: dict, scene_index: int, scene_id: str) -> dict:
    return {
        "schema_version": SCENE_CONTRACT_VERSION,
        "scene_id": scene_id,
        "scene_index": scene_index,
        "narration": scene.get("narration", ""),
        "visual_description": scene.get("visual_description", ""),
        "image_prompt": scene.get("image_prompt", ""),
        "video_prompt": scene.get("video_prompt", ""),
        "asset_type": scene.get("asset_type", "image"),
        "estimated_duration": scene.get("estimated_duration", 0.0),
        "characters": scene.get("characters", []),
        "background": scene.get("background", ""),
        "continuity_references": scene.get("continuity_references", []),
        "status": "draft",
    }
```

---

### Step 7: Next.js project wizard UI
**File:** `apps/web/components/project-wizard.tsx` (TẠO MỚI) + sửa `apps/web/app/(dashboard)/projects/new/page.tsx`
**Skill Invocation:** `frontend-development` + `ui-styling`.

**Code cần viết (rút gọn — Tier 2 tự chi tiết hoá UI):**
```tsx
"use client";
import { useState } from "react";

export function ProjectWizard() {
  const [mode, setMode] = useState<"blank" | "clone_channel">("blank");
  // ... form fields topic, audience, language, duration, aspect_ratio, tone, visual_style, voice_profile_id, music_mood
  // ... submit gọi POST /api/projects
}
```

**KHÔNG được sửa:**
- File `apps/web/app/(dashboard)/channels/**` (flow cũ).

---

### Step 8: Project workspace page
**File:** `apps/web/app/(dashboard)/projects/[id]/page.tsx` (TẠO MỚI)
**Skill Invocation:** `frontend-development`.

Hiển thị: stage timeline, brief hiện tại, job progress, nút Approve/Reject.

---

### Step 9: Tests
**File:** `tests/api/test_projects.py` + `tests/worker/test_script_generate.py` (TẠO MỚI)
**Skill Invocation:** `testing-protocol` + `debugging-protocol`.

Test cases bắt buộc:
- Tạo project blank với brief hợp lệ → 201.
- Tạo 2 lần cùng brief → trả về cùng project_id (idempotent).
- `clone_channel` không có `channel_assistant_id` → 422.
- User A tạo project, user B GET → 404.
- RLS: user B không select được row của user A.
- Job retry với cùng idempotency key → không tạo duplicate scene.

**Verify command:**
```powershell
.\venv\Scripts\Activate.ps1
pytest tests/api/test_projects.py tests/worker/test_script_generate.py -v --cov=apps.api.routers.projects --cov=apps.worker.tasks.script_generate --cov-report=term-missing
```

**Expected:** Coverage ≥80% cho module mới.

---

## Quy trình bàn giao (Handover)

1. Tier 2 chạy toàn bộ verify command ở trên.
2. Nếu pass, tạo AUDIT-REPORT theo template `.ai-pipeline/templates/AUDIT-REPORT.template.md`.
3. Commit local (KHÔNG push): `git add . && git commit -m "feat(phase-01): project foundation + blank onboarding"`.
4. Giao AUDIT-REPORT cho Tier 1 (tôi) duyệt. Tier 1 sẽ có section "Quyết định của Planner".
5. Sau khi duyệt, sếp mới push lên remote.
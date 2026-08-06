# MSEW: phase1-preflight-blockers

## Prerequisites (Điều kiện tiên quyết)
- **Đọc CONTEXT:** `docs/plan/CONTEXT-phase1-preflight-blockers.md`
- **Đọc PLAN:** `docs/plan/PLAN-phase1-preflight-blockers.md`
- **Migration hiện tại cuối:** `supabase/migrations/0022_admin_panel_foundation.sql` (đã viết ở Phase 5)
- **Branch:** main
- **Working dir:** `d:\appDK`
- **Line ending:** CRLF
- **Quy tắc:** KHÔNG tự sửa code ngoài scope. Nếu fail → ghi vào `BLOCKERS.md`.

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | Migration 0023: DROP FUNCTION cũ + Fix RLS transcripts | `databases` | `better-auth` | `debugging` |
| 2 | Tạo `apps/api/routers/assistants.py` | `backend-development` | `databases` | `debugging` |
| 3 | Tạo `apps/api/routers/jobs.py` | `backend-development` | `databases` | `debugging` |
| 4 | Tạo `apps/api/routers/analysis.py` | `backend-development` | `databases` | `debugging` |
| 5 | Tạo `apps/api/routers/ideas.py` | `backend-development` | `databases` | `debugging` |
| 6 | Tạo `apps/api/routers/channels.py` | `backend-development` | `databases` | `debugging` |
| 7 | Thêm `GET /credits/pricing` vào `credits.py` | `backend-development` | `databases` | `debugging` |
| 8 | Tạo `apps/worker/tasks/collect_channel_task.py` | `backend-development` | `databases` | `debugging` |
| 9 | Refactor `apps/worker/tasks/analysis_task.py` | `backend-development` | `databases` | `debugging` |
| 10 | Tạo 4 web proxy routes | `frontend-development` | `web-frameworks` | `better-auth` |
| 11 | Mount 5 routers mới vào `apps/api/main.py` | `backend-development` | `debugging` | `code-review` |
| 12 | Self-verify toàn bộ | `debugging` | `code-review` | `backend-development` |

## Files KHÔNG được đụng (Do Not Touch)
- `apps/api/routers/projects.py` — production route đang chạy.
- `apps/api/modules/voice/*` — TTS production.
- `apps/worker/tasks/script_generate.py`, `idea_generate.py`, `scene_breakdown.py` — production worker tasks.
- `supabase/migrations/0001..0022` — không xóa/sửa, chỉ thêm 0023.
- Web proxy routes đã có (`apps/web/app/api/assistants/route.ts`, `assistants/[id]/route.ts`, `jobs/[id]/route.ts`, `analysis/[assistant_id]/route.ts`, `ideas/[assistant_id]/route.ts`).

---

## Micro-Steps

### Step 1: Migration `0023_preflight_cleanup.sql`
**File:** `supabase/migrations/0023_preflight_cleanup.sql` (NEW)
**Vị trí:** File mới, sau `0022_admin_panel_foundation.sql`.
**Skill Invocation:**
  - **Primary:** `databases` — SQL DDL.
  - **Reference:** `better-auth` — RLS pattern.
  - **Fallback:** `debugging`.

**Pre-check (CodeGraph):**
- `codegraph_node`: `hold_credits` ở `credit_manager.py:71` ➔ confirm RPC signature `(p_user_id, p_amount, p_job_id)`.
- `codegraph_node`: `partial_commit_credits` ở `credit_manager.py:89` ➔ confirm RPC signature `(p_job_id, p_final_amount)`.

**Import cần thêm:** (không — SQL migration)

**Code cần viết:**
```sql
-- 0023_preflight_cleanup.sql
-- ============================================================
-- Migration: 0023_preflight_cleanup.sql
-- Purpose: Drop duplicate credit functions from 0006 + Fix RLS transcripts leaky
-- ============================================================

-- 1) Cleanup: xóa signature CŨ của hold_credits (từ 0006) — đảo tham số so với 0020
DROP FUNCTION IF EXISTS hold_credits(UUID, UUID, INT);
DROP FUNCTION IF EXISTS hold_credits(UUID, INT, UUID);  -- defensive: nếu 0020 chưa apply
DROP FUNCTION IF EXISTS partial_commit_credits(UUID, UUID, INT);
DROP FUNCTION IF EXISTS partial_commit_credits(UUID, INT, UUID);  -- defensive
DROP FUNCTION IF EXISTS release_credits(UUID, UUID);  -- dead function (no caller)

-- 2) Fix RLS transcripts: scope theo assistant_id thay vì 'all authenticated'
DROP POLICY IF EXISTS "Authenticated users can view transcripts" ON transcripts;

-- Policy mới: cho phép user đọc transcripts thuộc các assistant của mình
-- (qua JOIN bảng dna_chunks → channel_assistants → user_id)
CREATE POLICY "Users can view own assistant transcripts" ON transcripts FOR SELECT
  USING (
    EXISTS (
      SELECT 1
      FROM dna_chunks dc
      JOIN channel_assistants ca ON ca.id = dc.assistant_id
      WHERE dc.source_video_id = transcripts.video_id
        AND ca.user_id = auth.uid()
    )
  );

-- Service role vẫn INSERT được (worker ghi transcripts sau khi collect_channel_task chạy)
CREATE POLICY "Service can insert transcripts" ON transcripts FOR INSERT
  WITH CHECK (true);
```

**Post-verify (CodeGraph):**
- (SQL only)

**KHÔNG được sửa:**
- Không xóa `pg_cron` job `transcript-cleanup`.

**Verify command (PowerShell):**
```powershell
Get-Content supabase\migrations\0023_preflight_cleanup.sql | Measure-Object -Line
Select-String -Path supabase\migrations\0023_preflight_cleanup.sql -Pattern "DROP FUNCTION|CREATE POLICY"
```

**Expected output:** Line count ≥ 25. Có 5 `DROP FUNCTION` + 2 `CREATE POLICY`.

---

### Step 2: Tạo `apps/api/routers/assistants.py`
**File:** `apps/api/routers/assistants.py` (NEW)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `databases`.
  - **Fallback:** `debugging`.

**Pre-check (CodeGraph):**
- `codegraph_node`: `channel_assistants` table ➔ columns: `id, user_id, youtube_url, channel_id, status, created_at, updated_at` (theo `0008_channel_assistants.sql`).
- `codegraph_node`: `get_supabase_user` ở `apps/api/dependencies/auth.py:14` ➔ signature `-> str`.

**Import cần thêm:** (đã có sẵn module)

**Code cần viết:**
```python
"""
Routers cho Channel Assistant CRUD.
Mounted dưới /api/assistants.
"""
from fastapi import APIRouter, Depends, HTTPException
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from typing import Optional


router = APIRouter(prefix="/api/assistants", tags=["Assistants"])


@router.get("")
async def list_assistants(
    user_id: str = Depends(get_supabase_user),
    limit: int = 50,
    offset: int = 0,
):
    """
    List assistants của user hiện tại.
    
    Query params:
        limit: số row tối đa (default 50, max 200).
        offset: pagination offset.
    
    Returns:
        List of channel_assistants rows.
    """
    admin = get_supabase_admin()
    result = (
        admin.table('channel_assistants')
        .select('*')
        .eq('user_id', user_id)
        .order('created_at', desc=True)
        .range(offset, offset + min(limit, 200) - 1)
        .execute()
    )
    return result.data or []


@router.get("/{assistant_id}")
async def get_assistant(
    assistant_id: str,
    user_id: str = Depends(get_supabase_user),
):
    """
    Lấy chi tiết 1 assistant. Verify ownership.
    
    Args:
        assistant_id: UUID.
    
    Raises:
        HTTPException 404 nếu không tồn tại hoặc không thuộc user.
    """
    admin = get_supabase_admin()
    result = (
        admin.table('channel_assistants')
        .select('*')
        .eq('id', assistant_id)
        .eq('user_id', user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(404, 'Assistant not found')
    return result.data


@router.delete("/{assistant_id}")
async def delete_assistant(
    assistant_id: str,
    user_id: str = Depends(get_supabase_user),
):
    """
    Soft delete assistant: set status='deleted'.
    
    Returns:
        204 No Content.
    """
    admin = get_supabase_admin()
    # Verify ownership trước
    existing = (
        admin.table('channel_assistants')
        .select('id')
        .eq('id', assistant_id)
        .eq('user_id', user_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(404, 'Assistant not found')
    
    admin.table('channel_assistants').update({
        'status': 'deleted',
        'updated_at': 'now()',
    }).eq('id', assistant_id).execute()
    
    return None  # 204
```

**KHÔNG được sửa:**
- Không import module khác ngoài auth + supabase.

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.routers.assistants import router; print('OK')"
```

**Expected output:** `OK`.

---

### Step 3: Tạo `apps/api/routers/jobs.py`
**File:** `apps/api/routers/jobs.py` (NEW)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `databases`.
  - **Fallback:** `debugging`.

**Pre-check (CodeGraph):**
- `codegraph_node`: `jobs` table ➔ columns: `id, user_id, task_type, status, credits_held, assistant_id, channel_id, created_at, updated_at`.
- `codegraph_node`: `CreditManager` ở `apps/api/services/credit_manager.py:43`.

**Code cần viết:**
```python
"""
Routers cho Jobs: trigger, get, recent.
Mounted dưới /api/jobs.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.credit_manager import CreditManager
from apps.worker.tasks.analysis_task import analyze_channel_task
from apps.worker.tasks.idea_generate import idea_generate_task
from apps.worker.tasks.script_generate import script_generate_task
import uuid


router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


VALID_TASK_TYPES = {
    'deep_analysis': 50,
    'idea_generation': 5,
    'script_generation': 30,
    'scene_breakdown': 10,
}


class TriggerJobRequest(BaseModel):
    assistant_id: str = Field(..., description="UUID")
    task_type: str = Field(..., description="deep_analysis | idea_generation | script_generation | scene_breakdown")


@router.post("/trigger")
async def trigger_job(
    request: TriggerJobRequest,
    user_id: str = Depends(get_supabase_user),
):
    """
    Trigger 1 task cho assistant.
    
    Args:
        request: {assistant_id, task_type}.
    
    Returns:
        {job_id, task_type, status: 'pending'}.
    
    Raises:
        HTTPException 400 nếu task_type không hợp lệ.
        HTTPException 402 nếu không đủ credits.
        HTTPException 404 nếu assistant không thuộc user.
    """
    if request.task_type not in VALID_TASK_TYPES:
        raise HTTPException(400, f"task_type phải là một trong: {list(VALID_TASK_TYPES.keys())}")

    admin = get_supabase_admin()

    # Verify ownership
    assistant = (
        admin.table('channel_assistants')
        .select('id, channel_id, status')
        .eq('id', request.assistant_id)
        .eq('user_id', user_id)
        .single()
        .execute()
    )
    if not assistant.data:
        raise HTTPException(404, 'Assistant not found')

    # Hold credits
    manager = CreditManager()
    job_id = str(uuid.uuid4())
    try:
        manager.hold(user_id, job_id, VALID_TASK_TYPES[request.task_type])
    except ValueError as e:
        raise HTTPException(402, f'Insufficient credits: {e}')

    # Insert jobs row
    admin.table('jobs').insert({
        'id': job_id,
        'user_id': user_id,
        'task_type': request.task_type,
        'status': 'pending',
        'credits_held': VALID_TASK_TYPES[request.task_type],
        'assistant_id': request.assistant_id,
        'channel_id': assistant.data.get('channel_id'),
    }).execute()

    # Dispatch Celery task
    if request.task_type == 'deep_analysis':
        analyze_channel_task.delay(job_id, request.assistant_id)
    elif request.task_type == 'idea_generation':
        idea_generate_task.delay(job_id, request.assistant_id)
    elif request.task_type == 'script_generation':
        script_generate_task.delay(job_id, request.assistant_id, topic=None)
    elif request.task_type == 'scene_breakdown':
        # scene_breakdown cần script_id, sẽ implement sau
        pass

    return {
        'job_id': job_id,
        'task_type': request.task_type,
        'status': 'pending',
    }


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    user_id: str = Depends(get_supabase_user),
):
    """Lấy chi tiết job. Verify ownership."""
    admin = get_supabase_admin()
    result = (
        admin.table('jobs')
        .select('*')
        .eq('id', job_id)
        .eq('user_id', user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(404, 'Job not found')
    return result.data


@router.get("/recent/list")
async def get_recent_jobs(
    user_id: str = Depends(get_supabase_user),
    limit: int = 10,
):
    """Lấy N jobs gần nhất của user (cho dashboard)."""
    admin = get_supabase_admin()
    result = (
        admin.table('jobs')
        .select('id, task_type, status, credits_held, created_at, assistant_id')
        .eq('user_id', user_id)
        .order('created_at', desc=True)
        .limit(min(limit, 50))
        .execute()
    )
    return result.data or []
```

**KHÔNG được sửa:**
- Không sửa 3 task import (chỉ dispatch).

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.routers.jobs import router; print('OK')"
```

**Expected output:** `OK`.

---

### Step 4: Tạo `apps/api/routers/analysis.py`
**File:** `apps/api/routers/analysis.py` (NEW)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `databases`.
  - **Fallback:** `debugging`.

**Pre-check (CodeGraph):**
- `codegraph_node`: `channel_deep_analysis` table ➔ FK `assistant_id` → `channel_assistants.id`.

**Code cần viết:**
```python
"""
Routers cho Deep Analysis: get + reanalyze.
Mounted dưới /api/analysis.
"""
from fastapi import APIRouter, Depends, HTTPException
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.credit_manager import CreditManager
from apps.worker.tasks.analysis_task import analyze_channel_task
import uuid


router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.get("/{assistant_id}")
async def get_analysis(
    assistant_id: str,
    user_id: str = Depends(get_supabase_user),
):
    """Lấy analysis mới nhất của assistant (verify ownership)."""
    admin = get_supabase_admin()
    
    # Verify ownership
    assistant = (
        admin.table('channel_assistants')
        .select('id')
        .eq('id', assistant_id)
        .eq('user_id', user_id)
        .single()
        .execute()
    )
    if not assistant.data:
        raise HTTPException(404, 'Assistant not found')

    result = (
        admin.table('channel_deep_analysis')
        .select('*')
        .eq('assistant_id', assistant_id)
        .order('created_at', desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else {}


@router.post("/{assistant_id}/reanalyze")
async def reanalyze(
    assistant_id: str,
    user_id: str = Depends(get_supabase_user),
):
    """Trigger lại analysis task (charge 50 credits)."""
    admin = get_supabase_admin()
    
    assistant = (
        admin.table('channel_assistants')
        .select('id')
        .eq('id', assistant_id)
        .eq('user_id', user_id)
        .single()
        .execute()
    )
    if not assistant.data:
        raise HTTPException(404, 'Assistant not found')

    manager = CreditManager()
    job_id = str(uuid.uuid4())
    try:
        manager.hold(user_id, job_id, 50)
    except ValueError as e:
        raise HTTPException(402, f'Insufficient credits: {e}')

    admin.table('jobs').insert({
        'id': job_id,
        'user_id': user_id,
        'task_type': 'deep_analysis',
        'status': 'pending',
        'credits_held': 50,
        'assistant_id': assistant_id,
    }).execute()

    analyze_channel_task.delay(job_id, assistant_id)
    
    return {'job_id': job_id, 'status': 'pending'}
```

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.routers.analysis import router; print('OK')"
```

**Expected output:** `OK`.

---

### Step 5: Tạo `apps/api/routers/ideas.py`
**File:** `apps/api/routers/ideas.py` (NEW)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `databases`.
  - **Fallback:** `debugging`.

**Code cần viết:**
```python
"""
Routers cho Ideas: get ideas của assistant.
Mounted dưới /api/ideas.
"""
from fastapi import APIRouter, Depends, HTTPException
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin


router = APIRouter(prefix="/api/ideas", tags=["Ideas"])


@router.get("/{assistant_id}")
async def get_ideas(
    assistant_id: str,
    user_id: str = Depends(get_supabase_user),
    limit: int = 50,
):
    """Lấy generated ideas của assistant (verify ownership)."""
    admin = get_supabase_admin()
    
    # Verify ownership
    assistant = (
        admin.table('channel_assistants')
        .select('id')
        .eq('id', assistant_id)
        .eq('user_id', user_id)
        .single()
        .execute()
    )
    if not assistant.data:
        raise HTTPException(404, 'Assistant not found')

    result = (
        admin.table('generated_ideas')
        .select('*')
        .eq('assistant_id', assistant_id)
        .order('gap_score', desc=True)
        .limit(min(limit, 200))
        .execute()
    )
    return result.data or []
```

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.routers.ideas import router; print('OK')"
```

**Expected output:** `OK`.

---

### Step 6: Tạo `apps/api/routers/channels.py`
**File:** `apps/api/routers/channels.py` (NEW)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `databases`.
  - **Fallback:** `debugging`.

**Pre-check (CodeGraph):**
- `codegraph_node`: `YouTubeCollector` class ở `apps/api/modules/module_2a/service.py`.
- `codegraph_node`: `collect_channel_task` (chưa tồn tại — Step 8 sẽ tạo).

**Code cần viết:**
```python
"""
Routers cho Channel Collection.
Mounted dưới /api/channels.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.worker.tasks.collect_channel_task import collect_channel_task
import uuid
import re


router = APIRouter(prefix="/api/channels", tags=["Channels"])


class CollectChannelRequest(BaseModel):
    youtube_url: str = Field(..., description="URL hoặc channel ID")


def parse_channel_id(url: str) -> str:
    """Parse channel ID từ URL hoặc trả raw nếu đã là ID."""
    # Match @handle, /channel/UC..., /c/handle
    patterns = [
        r'youtube\.com/channel/(UC[A-Za-z0-9_-]+)',
        r'youtube\.com/@([A-Za-z0-9_-]+)',
        r'youtube\.com/c/([A-Za-z0-9_-]+)',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return url  # assume already ID


@router.post("/collect")
async def collect_channel(
    request: CollectChannelRequest,
    user_id: str = Depends(get_supabase_user),
):
    """
    Trigger collect channel videos: insert assistant + enqueue collect_channel_task.
    
    Args:
        request: {youtube_url}.
    
    Returns:
        {assistant_id, status: 'collecting'}.
    """
    admin = get_supabase_admin()
    channel_id = parse_channel_id(request.youtube_url)
    assistant_id = str(uuid.uuid4())
    
    # Insert channel_assistants
    admin.table('channel_assistants').insert({
        'id': assistant_id,
        'user_id': user_id,
        'youtube_url': request.youtube_url,
        'channel_id': channel_id,
        'status': 'collecting',
    }).execute()
    
    # Enqueue Celery task
    collect_channel_task.delay(assistant_id, channel_id)
    
    return {
        'assistant_id': assistant_id,
        'status': 'collecting',
    }
```

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.routers.channels import router; print('OK')"
```

**Expected output:** `OK` (sau khi Step 8 đã tạo `collect_channel_task`).

---

### Step 7: Thêm `GET /credits/pricing` vào `apps/api/routers/credits.py`
**File:** `apps/api/routers/credits.py` (UPDATE — append)
**Vị trí:** Dòng cuối file (sau function `_get_user_tier`).
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `databases`.
  - **Fallback:** `debugging`.

**Pre-check (CodeGraph):**
- `codegraph_node`: `credit_pricing` table ➔ columns: `job_type, credits, enabled, description`.

**Code cần viết (sửa file):**
- Mở file `apps/api/routers/credits.py`.
- **SAU** dòng cuối (function `_get_user_tier`), **THÊM** endpoint mới:

```python
@router.get('/credits/pricing')
async def get_pricing():
    """Lấy bảng giá credit (public — không cần auth)."""
    admin = get_supabase_admin()
    result = (
        admin.table('credit_pricing')
        .select('job_type, credits, description, enabled')
        .eq('enabled', True)
        .order('credits')
        .execute()
    )
    return result.data or []
```

**KHÔNG được sửa:**
- 2 endpoint cũ (`/credits/balance`, `/credits/transactions`).
- Imports.

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.routers.credits import router, get_pricing; print('OK')"
```

**Expected output:** `OK`.

---

### Step 8: Tạo `apps/worker/tasks/collect_channel_task.py`
**File:** `apps/worker/tasks/collect_channel_task.py` (NEW)
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `databases`.
  - **Fallback:** `debugging`.

**Pre-check (CodeGraph):**
- `codegraph_node`: `apps/api/modules/module_2a/service.py:YouTubeCollector` ➔ method `collect_channel_videos`.
- `codegraph_node`: `TranscriptEngine.get_transcript` ➔ signature `(video_id, preferred_languages)`.

**Code cần viết:**
```python
"""
Celery task: collect YouTube channel videos + transcripts.
Gọi YouTubeCollector + TranscriptEngine, insert vào DB.
"""
import os
import asyncio
from celery import Celery
from apps.api.modules.module_2a.service import YouTubeCollector
from apps.api.modules.transcript.engine import TranscriptEngine
from apps.api.dependencies.supabase import get_supabase_admin


celery_app = Celery('tasks', broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))


@celery_app.task(bind=True)
def collect_channel_task(self, assistant_id: str, channel_id: str):
    """
    Collect videos của channel + fetch transcripts.
    
    Args:
        assistant_id: UUID channel_assistants.id.
        channel_id: YouTube channel ID (UC...).
    """
    async def run():
        admin = get_supabase_admin()
        collector = YouTubeCollector()
        engine = TranscriptEngine()
        
        try:
            # Update status
            admin.table('channel_assistants').update({
                'status': 'collecting_videos',
            }).eq('id', assistant_id).execute()
            
            # Collect videos
            result = await collector.collect_channel_videos(
                channel_id=channel_id,
                max_videos=50,
            )
            quality_videos = result.get('quality_videos', [])
            
            # Insert videos (bảng videos table — nếu có, hoặc dùng channel_deep_analysis.metadata)
            # Tạm thời lưu vào raw_data của channel_assistants
            admin.table('channel_assistants').update({
                'status': 'fetching_transcripts',
                'updated_at': 'now()',
            }).eq('id', assistant_id).execute()
            
            # Fetch transcripts cho từng video (best-effort, max 10 để không timeout)
            transcripts_inserted = 0
            for video in quality_videos[:10]:
                video_id = video['id']
                try:
                    tr = await engine.get_transcript(
                        video_id=video_id,
                        preferred_languages=['vi', 'en'],
                    )
                    if tr and tr.get('transcript'):
                        admin.table('transcripts').upsert({
                            'video_id': video_id,
                            'text_content': tr['transcript'][:5000],
                            'raw_data': tr,
                            'fetched_at': 'now()',
                        }, on_conflict='video_id').execute()
                        transcripts_inserted += 1
                except Exception:
                    pass  # skip video nếu fail transcript
            
            # Update final status
            admin.table('channel_assistants').update({
                'status': 'ready',
                'updated_at': 'now()',
            }).eq('id', assistant_id).execute()
            
            return {
                'videos_collected': len(quality_videos),
                'transcripts_inserted': transcripts_inserted,
            }
        except Exception as e:
            admin.table('channel_assistants').update({
                'status': 'failed',
                'updated_at': 'now()',
            }).eq('id', assistant_id).execute()
            raise e
    
    return asyncio.run(run())
```

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.worker.tasks.collect_channel_task import collect_channel_task; print('OK')"
```

**Expected output:** `OK`.

---

### Step 9: Refactor `apps/worker/tasks/analysis_task.py`
**File:** `apps/worker/tasks/analysis_task.py` (UPDATE)
**Vị trí:** Xóa hàm `fetch_mock_data()` (line 19-20) và sửa logic `run()` (line 31-89) để query DB.
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `databases`.
  - **Fallback:** `debugging`.

**Pre-check (CodeGraph):**
- `codegraph_node`: `analyze_channel_task` callers ➔ chỉ `start_project` (line cuối của `projects.py`). Phase 1 KHÔNG dùng từ `/api/jobs/trigger` để tránh conflict. Phase sau sẽ switch.

**Import cần thêm:**
```python
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.modules.transcript.engine import TranscriptEngine
```

**Code cần viết (sửa file):**

**XÓA** toàn bộ function `fetch_mock_data()` (line 19-20).

**TRONG** function `run()`, **THAY** block:
```python
            videos = fetch_mock_data()
            transcripts = ["Hello world"] * 5
```
**BẰNG**:
```python
            admin = get_supabase_admin()
            engine = TranscriptEngine()
            
            # Query assistants để lấy user_id
            asst = (
                admin.table('channel_assistants')
                .select('id, user_id, channel_id')
                .eq('id', channel_id)
                .single()
                .execute()
            )
            if not asst.data:
                await tracker.fail("system", "Assistant not found")
                return
            
            # Query videos từ channel_deep_analysis hoặc fallback (Phase 1: tạm lấy từ channel_assistants metadata)
            # Thực tế: videos cần được insert bởi collect_channel_task. Phase 1: query transcripts table
            tr_result = (
                admin.table('transcripts')
                .select('video_id, text_content')
                .limit(50)
                .execute()
            )
            
            if tr_result.data and len(tr_result.data) > 0:
                videos = [{'title': f'Video {t["video_id"][:8]}', 'duration_sec': 300, 'views': 1000, 'thumbnail_url': '', 'video_id': t['video_id']} for t in tr_result.data]
                transcripts = [t['text_content'] for t in tr_result.data]
            else:
                # Fallback nếu chưa có transcripts: dùng minimal placeholder
                videos = [{'title': 'Placeholder', 'duration_sec': 300, 'views': 1000, 'thumbnail_url': '', 'video_id': 'placeholder'}]
                transcripts = ['No transcripts yet. Run collect_channel_task first.']
            
            # Nếu video thiếu transcript: gọi engine (best-effort)
            for i, v in enumerate(videos):
                if not transcripts[i] or transcripts[i].startswith('No transcripts'):
                    try:
                        tr = await engine.get_transcript(video_id=v['video_id'], preferred_languages=['vi', 'en'])
                        if tr and tr.get('transcript'):
                            transcripts[i] = tr['transcript']
                    except Exception:
                        pass
```

**KHÔNG được sửa:**
- Phần còn lại của `run()` (8 outputs, RAG layer).
- Signature của `analyze_channel_task(self, job_id, channel_id)`.
- Imports khác.

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.worker.tasks.analysis_task import analyze_channel_task; print('OK')"
```

**Expected output:** `OK`.

---

### Step 10: Tạo 4 web proxy routes
**Files (4 files NEW):**
- `apps/web/app/api/jobs/trigger/route.ts`
- `apps/web/app/api/jobs/recent/route.ts`
- `apps/web/app/api/channels/collect/route.ts`
- `apps/web/app/api/credits/pricing/route.ts`

**Skill Invocation:**
  - **Primary:** `frontend-development`.
  - **Reference:** `web-frameworks`.
  - **Fallback:** `better-auth`.

**Code cho cả 4 file:**

**`apps/web/app/api/jobs/trigger/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function POST(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const body = await req.json();
  try {
    const response = await apiFetch('/api/jobs/trigger', {
      method: 'POST',
      body: JSON.stringify(body),
    }, token);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/jobs/recent/route.ts`:**
```typescript
import { NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET() {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  try {
    const response = await apiFetch('/api/jobs/recent/list', {}, token);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/channels/collect/route.ts`:**
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function POST(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const body = await req.json();
  try {
    const response = await apiFetch('/api/channels/collect', {
      method: 'POST',
      body: JSON.stringify(body),
    }, token);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**`apps/web/app/api/credits/pricing/route.ts`:**
```typescript
import { NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';

export async function GET() {
  try {
    // /credits/pricing là public — không cần token
    const response = await apiFetch('/api/credits/pricing', {}, null);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

**Verify command:**
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit app/api/jobs/trigger/route.ts app/api/jobs/recent/route.ts app/api/channels/collect/route.ts app/api/credits/pricing/route.ts 2>&1 | Select-String "error TS"
```

**Expected output:** Không có dòng nào chứa "error TS".

---

### Step 11: Mount 5 routers mới vào `apps/api/main.py`
**File:** `apps/api/main.py` (UPDATE)
**Vị trí:** Thêm 5 dòng import (sau line 25) + 5 dòng include_router (sau line 42).
**Skill Invocation:**
  - **Primary:** `backend-development`.
  - **Reference:** `debugging`.
  - **Fallback:** `code-review`.

**Code cần viết (sửa file):**

**SAU** dòng `from apps.api.modules.voice.routes import router as voice_router` (line 25), **THÊM** 5 dòng:
```python
from apps.api.routers.assistants import router as assistants_router
from apps.api.routers.jobs import router as jobs_router
from apps.api.routers.analysis import router as analysis_router
from apps.api.routers.ideas import router as ideas_router
from apps.api.routers.channels import router as channels_router
```

**SAU** dòng `app.include_router(voice_router)` (line 42), **THÊM** 5 dòng:
```python
app.include_router(assistants_router)
app.include_router(jobs_router)
app.include_router(analysis_router)
app.include_router(ideas_router)
app.include_router(channels_router)
```

**KHÔNG được sửa:**
- 13 dòng include_router cũ.

**Verify command:**
```powershell
cd d:\appDK
python -c "from apps.api.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path')]; print('\n'.join([r for r in routes if '/api/' in r]))"
```

**Expected output:** Danh sách chứa:
- `/api/assistants`, `/api/assistants/{assistant_id}`
- `/api/jobs/trigger`, `/api/jobs/{job_id}`, `/api/jobs/recent/list`
- `/api/analysis/{assistant_id}`, `/api/analysis/{assistant_id}/reanalyze`
- `/api/ideas/{assistant_id}`
- `/api/channels/collect`
- `/api/credits/pricing`

---

### Step 12: Self-verify toàn bộ
**Skill Invocation:**
  - **Primary:** `debugging`.
  - **Reference:** `code-review`.
  - **Fallback:** `backend-development`.

**Verify commands:**
```powershell
# 1) All imports compile
cd d:\appDK
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.routers.assistants import router; print('assistants OK')"
python -c "from apps.api.routers.jobs import router; print('jobs OK')"
python -c "from apps.api.routers.analysis import router; print('analysis OK')"
python -c "from apps.api.routers.ideas import router; print('ideas OK')"
python -c "from apps.api.routers.channels import router; print('channels OK')"
python -c "from apps.api.routers.credits import router; print('credits OK')"
python -c "from apps.worker.tasks.collect_channel_task import collect_channel_task; print('collect_channel_task OK')"
python -c "from apps.worker.tasks.analysis_task import analyze_channel_task; print('analysis_task OK')"

# 2) Existing test không regression
cd apps\api
python -m pytest test_credit_manager.py -v 2>&1 | Select-String "PASSED|FAILED"

# 3) Migration file syntax check
cd ..\..
Get-Content supabase\migrations\0023_preflight_cleanup.sql | Measure-Object -Line

# 4) Web proxy routes TS compile
cd apps\web
pnpm exec tsc --noEmit 2>&1 | Select-String "error TS"
```

**Expected output:**
- 9 dòng "OK"
- 2 test PASSED (test_hold_succeeds, test_hold_insufficient_raises)
- Line count ≥ 25
- 0 errors TS

**Nếu bất kỳ check nào fail:**
- Invoke skill `debugging`
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
- Migration `0023_preflight_cleanup.sql` tồn tại, ≥ 25 dòng, syntax OK.
- 5 routers mới (`assistants`, `jobs`, `analysis`, `ideas`, `channels`) tồn tại, import OK.
- Endpoint `GET /credits/pricing` đã thêm vào `credits.py`.
- File `apps/worker/tasks/collect_channel_task.py` tồn tại, import OK.
- File `apps/worker/tasks/analysis_task.py` đã sửa (bỏ `fetch_mock_data`, query DB).
- 4 web proxy routes mới tồn tại, TS compile 0 errors.
- `apps/api/main.py` mount 5 routers mới, FastAPI app khởi động OK.
- **KHÔNG** có file nào trong `apps/api/routers/projects.py`, `apps/api/modules/voice/*`, `apps/worker/tasks/{script_generate,idea_generate,scene_breakdown}.py` bị đụng.
- Unit test `test_credit_manager.py` vẫn PASSED.
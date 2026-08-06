# MSEW: Phase 11 — Character/Background Lab

## Micro-Steps

### Step 1: Migration `0029b_character_background_lab.sql`
Như `phase-11-character-background-lab.md` mục "Data model".

### Step 2: Pydantic schemas
- `CharacterLabStart`, `CharacterAnchorResponse`, `BackgroundAnchorResponse`, `LabApprovalRequest`.

### Step 3: Capability probe
- Probe ip_adapter / instantid / pulid / face embedding qua adapter.

### Step 4: character_lab service
```python
async def generate_candidates(project_id, style_bible_id, slot_spec) -> list[Candidate]
async def bind_scene(scene_id, anchors) -> Binding
async def coverage_check(project_id) -> CoverageReport
```

### Step 5: API + coverage gate
- `POST /api/projects/{id}/lab/start`
- `POST /api/projects/{id}/lab/approve`
- Batch scene endpoint: nếu `lab_run.status != 'approved'` → 422 với danh sách scene thiếu anchor.

### Step 6: UI
- Character Lab tab + Background Lab tab trong project workspace.
- 3 panel: Candidate gallery / Detail viewer / Scene coverage.
- Nút Approve chỉ enable khi coverage = 100%.

### Step 7: Tests
```powershell
pytest tests/worker/test_character_lab.py tests/api/test_character_lab.py -v
```
- Coverage gate đúng.
- Regenerate KHÔNG phá source (variant mới).
- anchor_strength mapping đúng.
- Style bible version đổi → lab_run marked superseded.
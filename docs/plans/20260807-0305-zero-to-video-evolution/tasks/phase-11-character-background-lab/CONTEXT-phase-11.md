# CONTEXT: Phase 11 — Character & Background Lab

## 1. Repomix: `.\CONTEXT_BUNDLE.md`

## 2. Phụ thuộc
- Phase 02 (scene.characters, scene.background).
- Phase 05 (provider adapter + capability probe).
- Phase 09 (style bible, anchor_strength).
- Phase 10 batch scene assets chỉ chạy khi lab approved.

## 3. Files
### Modify
- `apps/api/routers/batch.py` — gate `lab_run.status == approved`.

### Create
- `supabase/migrations/0029b_character_background_lab.sql`
- `apps/worker/services/character_lab.py`
- `apps/worker/tasks/character_lab_generate.py`
- `apps/api/routers/character_lab.py`
- `apps/api/schemas/character_lab.py`
- `apps/web/components/character-lab.tsx`
- `apps/web/components/background-lab.tsx`
- `apps/web/app/(dashboard)/projects/[id]/lab/page.tsx`
- `tests/worker/test_character_lab.py`

## 4. Ràng buộc
- Coverage gate chặn batch khi có scene thiếu anchor.
- Capability probe trước khi dùng provider.
- Face embedding model whitelist.
- Metadata whitelist (giới tính, độ tuổi đại diện, ethnicity enum).
- Max 5 regenerate/anchor.
- Lab_run snapshot style_bible_version; đổi version → mark superseded.
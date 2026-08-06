# CONTEXT: Phase 09 — Style Bible, Character Reference & Design System

## 1. Repomix: `.\CONTEXT_BUNDLE.md`

## 2. Codebase
- `voice_profiles`, `channel_deep_analysis.visual_style`, `dna_chunks` có sẵn nhưng rải rác.
- Cần entity Style Bible riêng, version được.

## 3. Files
### Modify
- `apps/worker/services/rag_service.py` — chèn bible block.
- `apps/worker/tasks/script_generate.py` — inject merged prompt từ bible.
- `apps/worker/tasks/scene_breakdown.py` — gắn scene_style_applications.

### Create
- `supabase/migrations/0029_style_bible.sql`
- `apps/api/routers/style_bible.py`
- `apps/api/schemas/style_bible.py`
- `apps/worker/services/style_bible.py`
- `apps/web/components/style-bible-editor.tsx`
- `apps/web/components/character-reference-picker.tsx`
- `apps/web/app/(dashboard)/style-bibles/page.tsx`
- `apps/web/app/(dashboard)/style-bibles/[id]/page.tsx`
- `tests/api/test_style_bible.py`

## 4. Dependencies
- Pydantic v2.
- supabase-py.

## 5. Ràng buộc
- Source asset immutable; bible version tăng dần (không nhảy cóc).
- Validate palette (hex), lens (mm), motion keyword theo whitelist.
- Character ref phải gắn asset_id; nếu asset xoá → ref invalid.
- Không lưu mô tả nhân vật không phù hợp policy.
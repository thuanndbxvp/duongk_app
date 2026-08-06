# MSEW: Phase 09 — Style Bible

## Micro-Steps

### Step 1: Migration `0029_style_bible.sql`
Như `phase-09-style-bible-and-design-system.md` mục "Data model".

### Step 2: Pydantic schemas
- `StyleBibleCreate`, `StyleBibleUpdate`, `StyleBibleResponse`, `StyleBibleVersion`, `CharacterRef`, `BackgroundRef`, `StyleBibleApply`.

### Step 3: API
- CRUD bible + rollback version.
- `POST /api/projects/{id}/style-bible/apply` → tạo scene_style_applications row.

### Step 4: `build_prompt()`
```python
def build_prompt(bible_id, scene_contract, channel_profile_id) -> tuple[str, str, str]:
    # merge bible + scene → final_prompt
    # prepend negative_prompt (resolve conflict với channel forbidden_claims)
    # resolve character_refs theo scene.characters
    # resolve background_refs theo scene.background
    # return (merged_prompt, merged_negative, fingerprint)
```

### Step 5: RAG inject
- `rag_service.build_context()` thêm bible block trước evidence block.

### Step 6: Script generate inject
- `script_generate` dùng `build_prompt()` thay vì tự viết prompt.

### Step 7: UI
- 4 tab editor (Visual / Characters / Backgrounds / Negative).
- Version diff side-by-side.
- "Apply style bible" dropdown trong scene editor.

### Step 8: Tests
```powershell
pytest tests/api/test_style_bible.py tests/worker/test_style_bible.py -v
```
- build_prompt idempotent (cùng input → cùng output).
- Version rollback không phá scene_style_applications cũ.
- Character ref resolution: nếu asset bị xoá → mark invalid.
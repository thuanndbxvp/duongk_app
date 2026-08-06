# Phase 09 — Style Bible, Character Reference và Design System

## Context

- §3.8 trong `PIPELINE-INSIGHTS-FOR-NEW-PROJECT.md` đề xuất tách Style Bible ra khỏi prompt từng scene để tránh trôi phong cách.
- appDK hiện có `voice_profiles`, `channel_deep_analysis.visual_style` và `dna_chunks` rải rác; chưa có entity Style Bible riêng.
- Phase 01 đã chuẩn hoá `creative brief`; Phase 02/05 sinh image/video prompt theo scene; Phase 08 inject RAG.

## Mục tiêu

Đưa phong cách hình ảnh và tính nhất quán nhân vật ra thành một lớp dữ liệu độc lập, được version, có thể áp dụng xuyên suốt cho mọi scene, brief và provider.

```text
Style Bible
  ├── Visual style (palette, lighting, lens, motion)
  ├── Character references (face/body/wardrobe anchors)
  ├── Background references
  ├── Negative prompt
  └── Variant presets (genre, channel, project)
```

## Data model

Tạo migration `0029_style_bible.sql` với:

- `style_bibles`:
  - `id`, `owner_id`, `name`, `kind` (`genre` | `channel` | `project` | `custom`).
  - `version` (INT, NOT NULL), `is_active` (BOOL).
  - `visual_style` (JSONB): palette, lighting rule, lens rule, camera motion, composition rule.
  - `negative_prompt` (TEXT).
  - `character_refs` (JSONB[]): face anchors, body anchors, wardrobe anchors.
  - `background_refs` (JSONB[]): anchor asset ids, location tags.
  - `forbidden_claims` (TEXT[]).
  - `metadata` (JSONB).
  - UNIQUE (`owner_id`, `name`, `version`).
- `style_bible_assets`:
  - `bible_id`, `asset_id`, `role` (`character` | `background` | `texture` | `logo`).
  - `anchor_strength` (FLOAT 0..1).
- `scene_style_applications`:
  - `project_id`, `scene_id`, `bible_id`, `bible_version`, `merged_prompt`, `merged_negative`.
- `style_bible_versions`:
  - `bible_id`, `version`, `snapshot_json`, `diff_summary`, `created_by`, `created_at`.

Source asset bất biến. Khi Style Bible đổi version, sinh snapshot JSON trước khi ghi đè.

## Style bible contract

```text
build_prompt(bible_id, scene_contract, channel_profile_id)
  - merge style bible + scene prompt → final prompt
  - prepend negative prompt
  - resolve character refs theo scene.characters
  - resolve background refs theo scene.background
  - return merged_prompt, merged_negative, fingerprint
```

## UI

- Style bible editor: 4 tab (Visual / Characters / Backgrounds / Negative).
- Character reference picker: chọn asset + đặt anchor role + anchor strength.
- Version history: diff side-by-side với preview áp dụng lên một scene mẫu.
- Scene editor dùng dropdown "Apply style bible" và hiển thị preview merged prompt.

## Implementation steps

1. Tạo migration cho 4 bảng trên.
2. CRUD API cho style bible + version rollback.
3. `build_prompt()` service đặt tại `apps/worker/services/style_bible.py`.
4. Tích hợp với `script_generate` và `scene_breakdown` để inject merged prompt.
5. Tích hợp với Phase 05 providers: image, video, thumbnail.
6. Tích hợp với Phase 08 RAG: chèn bible block vào `rag_service.build_context()`.
7. UI editor và version diff.
8. Tests: build_prompt idempotent, character ref resolution, version rollback.

## Acceptance criteria

- Cùng một scene, đổi bible version → prompt đầu ra khác có kiểm soát.
- Character refs được resolve theo scene.characters và tạo asset placeholder nếu thiếu.
- Negative prompt được áp dụng cho mọi provider sinh ảnh/video.
- Version rollback không phá các scene đã approved (giữ scene_style_applications cũ).
- Style bible có thể tái sử dụng giữa nhiều project.

## Guardrails

- Validate palette (hex), lens (số mm), motion keyword theo whitelist.
- Không lưu mô tả nhân vật không phù hợp policy.
- Character ref phải gắn asset id; không để ref trỏ vào asset đã xoá.
- Style bible version tăng dần; không nhảy cóc trừ khi admin reset.

## Risks

- RAG context tràn nếu bible quá lớn: cap số chunk + tóm tắt tự động.
- Character drift giữa các provider: kiểm tra anchor strength > 0.6 và provider hỗ trợ ip_adapter/reference image.
- Negative prompt xung đột giữa bible và channel profile: ưu tiên channel `forbidden_claims`.
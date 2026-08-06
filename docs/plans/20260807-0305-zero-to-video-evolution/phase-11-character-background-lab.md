# Phase 11 — Character và Background Lab (Presets trước khi batch scene)

## Context

- Ai86Studio có flow "tạo trước character + background, rồi mới batch scene" để tránh character drift và giảm retry tốn credits.
- `phase-09` đã có khung `style_bible` + `character_refs` + `background_refs` + `anchor_strength`, nhưng chỉ là schema; chưa có flow bắt buộc.
- `phase-10` batch production có approval gate và cost estimate, nhưng chưa gate theo "đã có character/background reference".
- PIPELINE-INSIGHTS §3.7 nhấn mạnh "Không nên gọi tất cả AI generation ngay sau khi tạo script"; Phase 11 mở rộng nguyên tắc này thành 1 bước bắt buộc giữa approval và batch.

## Mục tiêu

Chèn 1 stage bắt buộc giữa "Scene Plan approved" và "Batch generate scene assets":

```text
Scene Plan approved
  → Character/Background Lab
      → Generate / chọn character anchors
      → Generate / chọn background anchors
      → User approve anchors
      → Validate coverage (mỗi scene.characters và scene.background đều có anchor)
  → Style Bible merge với anchors
  → Batch scene assets
```

## Data model

Mở rộng migration `0029_style_bible.sql` thành `0029b_character_background_lab.sql` với:

- `character_lab_runs`:
  - `id`, `project_id`, `owner_id`, `status` (`draft` | `generating` | `awaiting_approval` | `approved` | `failed`).
  - `style_bible_id`, `style_bible_version`.
  - `prompt_seed`, `provider`, `model_version`, `capability_probe_id`.
  - `cost_estimate_cents`, `cost_actual_cents`.
  - `started_at`, `finished_at`, `approved_at`, `approved_by`.
- `character_anchors`:
  - `id`, `project_id`, `name`, `role` (`main` | `supporting` | `extra`).
  - `face_asset_id`, `body_asset_id`, `wardrobe_asset_id`.
  - `face_embedding` (VECTOR hoặc FLOAT[]), `face_embedding_model`.
  - `anchor_strength` (FLOAT 0..1).
  - `consistency_score_target` (FLOAT 0..1).
  - `provider_capabilities` (JSONB): hỗ trợ ip_adapter, instantid, pulid, ...
  - `metadata` (JSONB): tuổi, giới tính, ethnicity theo whitelist, không lưu PII nhạy cảm.
- `background_anchors`:
  - `id`, `project_id`, `name`, `location_tag`.
  - `asset_id`, `lighting_preset`, `lens_preset`, `palette_override`.
  - `consistency_score_target`.
- `scene_anchor_bindings`:
  - `scene_id`, `character_anchor_id` (nullable), `background_anchor_id` (nullable).
  - `binding_strength` (FLOAT 0..1).
  - UNIQUE (`scene_id`, `character_anchor_id`, `background_anchor_id`).
- `lab_approval_evidence`:
  - `lab_run_id`, `anchor_id`, `anchor_kind`, `decision` (`approved` | `rejected` | `regenerate`).
  - `user_id`, `decided_at`, `notes`.
  - Không lưu PII ngoài `user_id`.

Source asset của anchor bất biến. Khi user bấm regenerate anchor, sinh variant mới, không ghi đè.

## Workflow bắt buộc

```text
Scene Plan approved
  → POST /projects/{id}/lab/start  (body: style_bible_id, channel_profile_id)
      → backend validate: tất cả scene.characters + scene.background đã được trích xuất
      → estimate cost
      → return cost_estimate + draft lab_run
  → User confirm
  → Backend gọi provider cho từng character/background slot
      → Generate candidates (mỗi anchor 3–5 candidates)
      → Lưu candidates vào lab_run.candidates
  → User browse candidates, chọn 1 hoặc yêu cầu regenerate
  → User chọn xong toàn bộ anchor → bấm Approve
      → Backend kiểm tra coverage: mọi scene đều có character_anchor_id + background_anchor_id
      → Coverage fail → trả về danh sách scene thiếu anchor, không cho approve
      → Coverage ok → lab_run.status = approved
  → Phase 05/10 chỉ bắt đầu khi lab_run.status = approved
```

## Lab contract

```text
character_lab.generate_candidates(project_id, style_bible_id, slot_spec)
  → input: style bible, scene.characters, role filter
  → output: candidates with face_asset_id, anchor_strength, embedding model

character_lab.bind_scene(scene_id, anchors)
  → input: scene_id, character_anchor_id, background_anchor_id, binding_strength
  → output: binding record + coverage check

character_lab.coverage_check(project_id)
  → output: {
      total_scenes, scenes_with_full_anchors, scenes_missing: [{scene_id, missing: ["character"|"background"]}]
    }
```

## UI

- Tab **Character Lab** trong project workspace.
- 3 panel: Candidate gallery / Detail viewer / Scene coverage.
- Mỗi candidate có score: face embedding distance, anchor strength, style bible match.
- Nút **Regenerate** cho 1 anchor; nút **Approve all** chỉ enable khi coverage = 100%.
- Empty state nếu chưa có style bible → CTA "Tạo Style Bible trước".

## Implementation steps

1. Migration `0029b_character_background_lab.sql`.
2. Service `apps/worker/services/character_lab.py` với các hàm trên.
3. Capability probe cho provider: hỗ trợ ip_adapter / instantid / pulid / face embedding trả về vector.
4. Tích hợp với `phase-09` build_prompt: merge anchor metadata vào final prompt.
5. Coverage gate ở API: batch scene không thể bắt đầu nếu chưa có `lab_run.status = approved`.
6. UI Character Lab + Background Lab.
7. Audit log: ai approved anchor, khi nào, hash embedding.
8. Tests: coverage gate đúng, regenerate không phá source, anchor_strength mapping đúng.

## Acceptance criteria

- Không thể batch scene assets khi có scene thiếu character_anchor hoặc background_anchor.
- User có thể regenerate từng anchor mà không phá các anchor đã approve.
- Coverage check chạy real-time, highlight scene nào thiếu anchor.
- Khi style bible đổi version, lab run cũ đánh dấu `superseded`; user phải re-approve.
- Cost estimate cho lab tách riêng với cost estimate batch scene.
- Không có provider nào chạy qua pipeline nếu chưa capability probe pass.

## Guardrails

- Chỉ dùng provider adapter chính thức; không dùng session-token sniffing hay private endpoint.
- Face embedding model phải được whitelist (không tự ý dùng model tải từ nguồn không kiểm chứng).
- Metadata mô tả nhân vật không được chứa thông tin nhạy cảm ngoài whitelist (giới tính, độ tuổi đại diện, ethnicity theo enum chuẩn).
- Anchor asset gắn license metadata; cleanup watermark chỉ chạy theo consent của phase-05.
- Lưu `lab_approval_evidence` không bao gồm IP, device fingerprint; chỉ `user_id` + `decided_at` + `decision`.

## Risks

- Anchor regeneration hàng loạt tốn credits: cap `max_regenerate_per_anchor = 5`.
- Provider capability khác nhau giữa ip_adapter và instantid: chuẩn hoá `binding_strength` về 0..1 và cho provider tự map.
- Style bible đổi version giữa chừng phá lab_run: snapshot style bible version vào lab_run, không đọc live.
- User bấm Approve khi vẫn còn scene missing anchor: API trả 422 với danh sách scene thiếu; UI disable nút.

## Phụ thuộc

- Phase 01: project approval state.
- Phase 02: scene contract có `scene.characters` + `scene.background`.
- Phase 09: style bible, build_prompt, anchor_strength.
- Phase 05: provider adapter + capability probe.
- Phase 10: batch production chỉ chạy khi lab approved.
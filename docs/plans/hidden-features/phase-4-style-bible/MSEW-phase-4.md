# Phase 4 — MSEW

## Milestones

| Step | Action | Skills |
|---|---|---|
| 1 | Verify style bible endpoints | `debugging` |
| 2 | Build `<StyleBibleCard>` | `frontend-development`, `ui-styling` |
| 3 | Build list page | `frontend-development` |
| 4 | Build 4 section components | `frontend-development`, `ui-styling` |
| 5 | Build `<StyleBibleDetail>` | `frontend-development` |
| 6 | Build detail page | `frontend-development` |
| 7 | Build create form | `frontend-development` |
| 8 | Wire preview button | `frontend-development` |
| 9 | Tests | `testing-protocol` |
| 10 | Review | `code-review` |

## Skills routing

| Task | Primary | Secondary |
|---|---|---|
| Components | `frontend-development` | `ui-styling` |
| Forms | `frontend-development` | — |
| Tests | `testing-protocol` | — |

## Evidence

```bash
curl -X GET "http://localhost:8000/api/style-bibles" -H "Authorization: Bearer ${TOKEN}"
curl -X POST "http://localhost:8000/api/style-bibles" -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -d '{"name":"My Style","description":"...","tags":["anime"]}'
curl -X POST "http://localhost:8000/api/style-bibles/{id}/sections" -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -d '{"type":"color","data":{"hex":"#3b82f6","name":"Primary Blue"}}'
curl -X POST "http://localhost:8000/api/style-bibles/{id}/preview" -H "Authorization: Bearer ${TOKEN}"

pytest tests/web/components/test_style_bible.tsx -v
pytest tests/api/test_style_bible_endpoints.py -v
```

## Warnings

### 🟡 Gotcha 1: Section state = derived vs source-of-truth

Sections có 2 nguồn:
- Server fetch (initial)
- Local state (sau khi user add/edit)

Tier 2 cần sync giữa 2 nguồn. Nếu user add section → local state update. Nếu server có change khác (e.g., admin edit) → conflict.

**Fix**: Dùng React state + re-fetch on demand. Tránh optimistic updates trong P4.

### 🟡 Gotcha 2: Image upload trong sections

Character refs và background refs cần upload ảnh. Trong form, user pick file → POST multipart → backend save → return URL.

**Fix**: Tier 2 tạo helper `<ImageUploadField>` dùng FormData.

### 🟡 Gotcha 3: Color picker UX

`<input type="color">` không friendly. Một số browser show modal phức tạp.

**Fix**: Tier 2 có thể dùng library (e.g., react-color), hoặc tự build swatch grid (clickable hex codes).

### 🟡 Gotcha 4: Preview generation slow

POST /preview chạy image composition → 5-10s. UI cần loading state.

**Fix**: Button disabled + spinner + toast "Đang generate preview..."

### 🟡 Gotcha 5: Tags input complexity

Tags (array of strings) khó handle trong form. Options:
- Comma-separated input (đơn giản, dễ parse)
- Chip input (advanced, cần library)

**Fix**: Tier 2 dùng comma-separated cho MVP. Improve sau.

## Performance budget

- Step 1: 2 giờ
- Step 2-3: 4 giờ
- Step 4-5: 8 giờ
- Step 6-7: 4 giờ
- Step 8: 2 giờ
- Step 9-10: 6 giờ
- Total: ~26 giờ (= 5 ngày part-time)

## Exit gates

- [ ] All tests pass
- [ ] Coverage ≥80%
- [ ] LoC delta +600/-10
- [ ] Tier 1 sign-off
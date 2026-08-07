# Phase 2 — MSEW

## Milestones

| Step | Action | Skills |
|---|---|---|
| 1 | Verify 6 analysis sub-endpoints exist + return correct shape | `debugging`, `code-review` |
| 2 | Create `lib/analysis-client.ts` helper | `frontend-development` |
| 3 | Refactor AnalysisPage to use helper | `frontend-development` |
| 4 | Update AnalysisTabs với badges + per-tab loading | `frontend-development`, `ui-styling` |
| 5 | Build `<ScriptRegenerateDialog>` | `frontend-development` |
| 6 | Build `<ScriptVersionDropdown>` | `frontend-development` |
| 7 | Wire dialog + dropdown vào `<ScriptEditor>` | `frontend-development` |
| 8 | Tests: component + integration | `testing-protocol` |
| 9 | Self-review + Tier 1 review | `code-review` |

## Skills routing

| Task | Primary | Secondary |
|---|---|---|
| Helper builder | `frontend-development` | — |
| Tabs refactor | `frontend-development` | `ui-styling` |
| Dialog | `frontend-development` | `ui-styling` |
| Dropdown | `frontend-development` | `ui-styling` |
| Tests | `testing-protocol` | — |

## Evidence

```bash
# Verify endpoints
curl -X GET "http://localhost:8000/api/analysis/{id}/nlp" -H "Authorization: Bearer ${TOKEN}"
# Should return 200 with {entities: [...], sentiment: {...}}

# Component tests
pytest tests/web/components/test_analysis_tabs.tsx -v
pytest tests/web/components/test_script_regenerate.tsx -v

# Integration tests
pytest tests/api/test_analysis_subendpoints.py -v
pytest tests/api/test_script_regenerate.py -v

# E2E
bash scripts/run_e2e_local.sh
```

## Warnings

### 🟡 Gotcha 1: Parallel API calls = need error tolerance

`fetchAnalysisFull` dùng `Promise.all`. Nếu 1 endpoint fail → cả nhóm reject → user thấy full error.

**Fix**: dùng `Promise.allSettled` thay thế → mỗi tab độc lập, tab nào fail chỉ show error tab đó.

```typescript
const results = await Promise.allSettled([
  apiFetch(`/api/analysis/${id}/nlp`, ...),
  apiFetch(`/api/analysis/${id}/llm`, ...),
  // ...
]);
const [nlp, llm, ...] = results.map(r => r.status === 'fulfilled' ? r.value : null);
```

### 🟡 Gotcha 2: Script regenerate có thể mất 10s

Backend regenerate gọi LLM → timeout 10s default. UI nên show "Đang generate..." với spinner.

**Fix**: Button disabled + loading state + toast sau success.

### 🟡 Gotcha 3: Version diff = UX consideration

Diff giữa 2 versions có thể dài → show modal toàn màn hình, không show inline.

**Fix**: Component `<DiffModal>` với side-by-side view (left = selected, right = current).

### 🟡 Gotcha 4: Tab badges phải reactive

Khi data thay đổi (e.g., user regenerate insights), tab badges phải update. Server component sẽ re-render toàn page, nhưng client component chỉ re-render khi props thay đổi.

**Fix**: Trong tabs, dùng client component với `useEffect` theo dõi props change, hoặc gọi `router.refresh()` sau regenerate.

### 🟡 Gotcha 5: Versions endpoint pagination

Script có thể có 20+ versions. Endpoint `GET /api/scripts/{id}/versions` returns tất cả → response lớn.

**Fix**: Tier 2 implement pagination (limit 50). Nếu user muốn xem older → "Load more" button.

## Performance budget

- Step 1: 2 giờ
- Step 2-4: 4 giờ
- Step 5-6: 4 giờ
- Step 7: 2 giờ
- Step 8: 4 giờ
- Step 9: 2 giờ
- Total: ~18 giờ (= 3 ngày part-time)

## Exit gates

- [ ] Tests pass
- [ ] Coverage ≥80%
- [ ] LoC delta within budget
- [ ] Tier 1 sign-off
- [ ] Merge to main
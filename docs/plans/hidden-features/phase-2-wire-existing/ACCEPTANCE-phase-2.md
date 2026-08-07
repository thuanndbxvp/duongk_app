# Phase 2 — Acceptance Criteria

## A. Analysis sub-endpoints

### A.1 — Refactor AnalysisPage

- [ ] `fetchAnalysisFull` helper in `lib/analysis-client.ts`
- [ ] 6 parallel API calls (nlp, llm, deterministic, insights, thumbnail, output)
- [ ] Server component passes typed data to `<AnalysisTabs>`
- [ ] No breaking change cho existing consumers

### A.2 — `<AnalysisTabs>` updates

- [ ] 5 tabs render: NLP, LLM, Deterministic, Insights, Thumbnail
- [ ] Tab badges show count từ data
- [ ] Loading state per tab
- [ ] Error state per tab
- [ ] Click tab → content switches without flicker

### A.3 — Tests

- [ ] `<AnalysisTabs>` renders with mock data
- [ ] `<AnalysisTabs>` handles empty/null data
- [ ] `<AnalysisTabs>` shows error state on API failure

## B. Script regeneration

### B.1 — Dialog component

- [ ] `<ScriptRegenerateDialog>` exists
- [ ] Textarea for feedback (required)
- [ ] Submit button → API call
- [ ] Loading state với disable button
- [ ] Error handling (alert + close)
- [ ] Success → refresh + close

### B.2 — Wire to `<ScriptEditor>`

- [ ] "Regenerate" button hiển thị ở editor header
- [ ] Click → mở dialog
- [ ] Submit → call POST `/api/scripts/{id}/regenerate`
- [ ] Page refresh sau success
- [ ] Backend tạo version mới, persist DB

### B.3 — Tests

- [ ] Unit test for dialog
- [ ] Mocks POST and validates payload
- [ ] Test error path

## C. Script versions

### C.1 — Dropdown component

- [ ] `<ScriptVersionDropdown>` exists
- [ ] Fetches `/api/scripts/{id}/versions` on mount
- [ ] Renders v1, v2, ... sorted desc
- [ ] Select → onVersionChange callback
- [ ] Empty state nếu chỉ có 1 version

### C.2 — Wire to `<ScriptEditor>`

- [ ] Dropdown hiển thị ở editor header
- [ ] Current version pre-selected
- [ ] Select version → load version content
- [ ] "Compare" button: show diff giữa current và selected
- [ ] Diff visualization (simple text diff OK)

### C.3 — Tests

- [ ] Dropdown fetches and renders
- [ ] Select version changes editor content
- [ ] Diff calculation correct

## D. Final verification

- [ ] All tests pass
- [ ] Coverage ≥80%
- [ ] LoC delta: +250 / -20
- [ ] No new dependencies
- [ ] No console.log / debug
- [ ] Tier 1 review pass

## Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _Tier 2_ | ____ | ☐ |
| Reviewer | _Tier 1_ | ____ | ☐ |

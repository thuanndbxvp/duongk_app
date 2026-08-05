# Sprint 4+ Task Group 7: Deep Analysis Results (14 Outputs)

## 1. Context & Mục đích

### Bối cảnh

PRD mô tả **14 outputs** từ Sprint 2 Deep Analysis Engine, là GIÁ TRỊ LỚN NHẤT của app:
1. Metadata Analysis
2. Tags Analysis
3. Performance Reports
4. Optimal Duration (A4)
5. Consistency Score (A5)
6. Pacing Profile (WPM)
7. Sentiment Distribution
8. Hook Analysis (LLM)
9. Structural Formula (LLM)
10. Emotion Distribution
11. Mimic Rules (LLM)
12. Hidden Insights (A12 + LLM narrate)
13. Idea Opportunities (A14 Gap Score)
14. Thumbnail Analysis (Vision)

UI hiện tại **KHÔNG CÓ** trang nào để user xem 14 outputs này.

### Mục đích task group này

- Trang **`/analysis/[assistant_id]`** hiển thị đầy đủ 14 outputs
- Chia thành **sections/tabs** để dễ đọc
- Visualization đẹp mắt (charts, badges, JSON viewer)
- Caching: nếu đã analyze rồi thì show cache (không charge lại)

### Phụ thuộc

- ✅ Task 6: Channel Assistants (để có assistant_id)
- ✅ Backend: `channel_deep_analysis` table (migration 0009)
- ✅ Backend: `analysis_task` (Sprint 2 worker)

---

## 2. 14 Outputs Detail

### Deterministic Layer (Outputs 1-4)

| # | Name | Formula | Data Source |
|---|------|---------|-------------|
| 1 | Metadata | Avg duration, median views | numpy |
| 2 | Tags | Co-occurrence, top tags | pure Python |
| 3 | Performance | Best/worst videos | sorted |
| 4 | Optimal Duration | A4 formula | statistical |

### NLP Layer (Outputs 5-7)

| # | Name | Tool | Data Source |
|---|------|------|-------------|
| 5 | Consistency Score | A5 formula | MAD algorithm |
| 6 | Pacing Profile | textstat | WPM, sentence length |
| 7 | Sentiment | VADER / PhoBERT | transcript chunks |

### LLM Layer (Outputs 8-11)

| # | Name | Prompt | Cost |
|---|------|--------|------|
| 8 | Hook Analysis | HOOK_ANALYSIS_PROMPT | $0.02 |
| 9 | Structural Formula | EXTRACT_STRUCTURE_PROMPT | $0.02 |
| 10 | Emotion Distribution | j-hartmann / PhoBERT | $0 |
| 11 | Mimic Rules | GENERATE_MIMIC_RULES_PROMPT | $0.02 |

### Insights Layer (Outputs 12-14)

| # | Name | Formula | Notes |
|---|------|---------|-------|
| 12 | Hidden Insights | Chi-square + LLM narrate | $0.05 |
| 13 | Idea Opportunities | A14 Gap Score | HDBSCAN |
| 14 | Thumbnail Analysis | GPT-4o Vision | $0.10 |

---

## 3. UI Layout

### `/analysis/[assistant_id]`

```
┌─────────────────────────────────────────────────────────────────────┐
│  ← Back to Assistant                                                │
│  Deep Analysis: Chú Béo Channel                    [🔄 Re-analyze] │
├─────────────────────────────────────────────────────────────────────┤
│  TABS:                                                              │
│  [Overview] [Deterministic] [NLP] [LLM] [Insights] [Thumbnail]      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  OVERVIEW TAB (default):                                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐        │
│  │ 14 Outputs     │ │ Last Analysis   │ │ Total Cost     │        │
│  │  ✓ All Done   │ │  2 hours ago    │ │  $0.23         │        │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘        │
│                                                                      │
│  DETERMINISTIC TAB:                                                  │
│  ┌─ Output 1: Metadata ─────────────────────────────────────┐      │
│  │  Total videos: 200                                       │      │
│  │  Avg duration: 8m 32s                                    │      │
│  │  Median views: 45,231                                    │      │
│  │  Engagement rate: 4.2%                                   │      │
│  └──────────────────────────────────────────────────────────┘      │
│  ┌─ Output 2: Tags ────────────────────────────────────────┐      │
│  │  Top co-occurring tags: [chart]                          │      │
│  └──────────────────────────────────────────────────────────┘      │
│  ...                                                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Files to Create

| File | Purpose |
|------|---------|
| `apps/web/app/analysis/[assistant_id]/page.tsx` | Main page with tabs |
| `apps/web/app/api/analysis/[assistant_id]/route.ts` | API proxy |
| `apps/web/components/analysis/overview-tab.tsx` | Tab 1 |
| `apps/web/components/analysis/deterministic-tab.tsx` | Tab 2 |
| `apps/web/components/analysis/nlp-tab.tsx` | Tab 3 |
| `apps/web/components/analysis/llm-tab.tsx` | Tab 4 |
| `apps/web/components/analysis/insights-tab.tsx` | Tab 5 |
| `apps/web/components/analysis/thumbnail-tab.tsx` | Tab 6 |
| `apps/web/components/analysis/output-card.tsx` | Reusable card |
| `apps/web/components/analysis/json-viewer.tsx` | JSON display |

---

## 5. Acceptance Summary

| # | Criteria |
|---|----------|
| AC1 | Page renders 14 outputs |
| AC2 | 6 tabs navigation works |
| AC3 | Loading + error states |
| AC4 | JSON viewer cho complex data |
| AC5 | "Re-analyze" button charges credits |
| AC6 | Cache behavior (no double charge) |
| AC7 | RLS isolation |
| AC8 | Responsive mobile |
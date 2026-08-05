# Sprint 4+ Task Group 7: Deep Analysis - Plan

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  DEEP ANALYSIS VIEW                                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User → /analysis/[assistant_id]                                 │
│     │                                                            │
│     ▼                                                            │
│  BFF GET /api/analysis/[assistant_id]                           │
│     │                                                            │
│     ▼                                                            │
│  Backend: Aggregate 14 outputs from channel_deep_analysis       │
│     │                                                            │
│     ▼                                                            │
│  UI: 6 tabs x N outputs                                          │
│                                                                   │
│  "Re-analyze" button:                                            │
│     │                                                            │
│     ▼                                                            │
│  Trigger Celery analysis_task (charges 50 credits)               │
│     │                                                            │
│     ▼                                                            │
│  Redirect to /jobs/[job_id] (realtime progress)                  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Data Structure

### Backend returns

```typescript
interface AnalysisData {
  assistant_id: string;
  channel_name: string;
  version: number;
  computed_at: string;
  total_cost_usd: number;
  
  // 14 outputs
  output_1_metadata: { total_videos, avg_duration_seconds, median_views, ... };
  output_2_tags: { top_tags: [{ tag, count }], co_occurrence: [...] };
  output_3_performance: { best_videos, worst_videos, consistency_score };
  output_4_optimal_duration: { recommended_seconds, formula_a4 };
  output_5_consistency: number;
  output_6_pacing: { avg_wpm, sentence_lengths };
  output_7_sentiment: { positive, neutral, negative };
  output_8_hook: { patterns: [...], framework: string };
  output_9_structure: { typical_structure: {...} };
  output_10_emotion: { joy, anger, surprise, ... };
  output_11_mimic_rules: { vocabulary, common_phrases, tone };
  output_12_insights: { findings: [{ title, evidence, narration }] };
  output_13_ideas: { opportunities: [{ topic, gap_score, untapped: bool }] };
  output_14_thumbnail: { brand_score, recurring_elements: [...] };
}
```

## Pages Detail

### /analysis/[assistant_id]

**Type:** Server Component (initial render) + Client Component (tabs)

**States:**
1. **Not analyzed:** Empty state với button "Run Analysis (50 credits)"
2. **Analyzing:** Loading state với progress link
3. **Analyzed:** Show 6 tabs với data

**Tabs:**
1. **Overview** - Summary cards (14 outputs count, cost, last run)
2. **Deterministic** - Outputs 1-4 (Metadata, Tags, Performance, Duration)
3. **NLP** - Outputs 5-7 (Consistency, Pacing, Sentiment)
4. **LLM** - Outputs 8-11 (Hook, Structure, Emotion, Mimic)
5. **Insights** - Outputs 12-13 (Hidden Insights, Ideas)
6. **Thumbnail** - Output 14 (Vision analysis)

## API Routes

### GET /api/analysis/[assistant_id]

Returns analysis data or 404 if not analyzed yet.

### POST /api/analysis/[assistant_id]

Triggers new analysis job (charges 50 credits).

## Backend Reference

### Existing endpoints (Sprint 2)

```python
POST /api/analysis/channel  # Run analysis (need assistant_id)
GET  /api/analysis/{assistant_id}  # Get latest (TODO)
```

⚠️ Backend GET endpoint cần bổ sung. Task này giả định backend đã có hoặc sẽ thêm qua Task 11.

---

## Files to Create

### 1. Page

- `apps/web/app/analysis/[assistant_id]/page.tsx`

### 2. API Proxy

- `apps/web/app/api/analysis/[assistant_id]/route.ts`

### 3. Components (10 files)

- `apps/web/components/analysis/analysis-tabs.tsx` - Tab container
- `apps/web/components/analysis/overview-tab.tsx`
- `apps/web/components/analysis/deterministic-tab.tsx`
- `apps/web/components/analysis/nlp-tab.tsx`
- `apps/web/components/analysis/llm-tab.tsx`
- `apps/web/components/analysis/insights-tab.tsx`
- `apps/web/components/analysis/thumbnail-tab.tsx`
- `apps/web/components/analysis/output-card.tsx`
- `apps/web/components/analysis/json-viewer.tsx`
- `apps/web/components/analysis/reanalyze-button.tsx`

---

## Constraints

1. **Initial server fetch** - page loads với data (no flicker)
2. **Client-side tabs** - no page reload
3. **JSON formatting** - readable cho LLM outputs
4. **Credit deduction** - chỉ khi user click "Re-analyze"
5. **Cache check** - nếu đã analyze trong 24h, không charge lại
6. **RLS isolation** - user chỉ xem analysis của assistants mình
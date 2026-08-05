# Sprint 4+ Task Group 8: Idea Generation & Selection

## 1. Context & Mục đích

### Bối cảnh

Sau Deep Analysis, bước tiếp theo là **Idea Generation** (Sprint 3.2):
- HDBSCAN cluster các topics của kênh
- Tính **Gap Score** (A14) = cơ hội "Untapped"
- Lưu vào `generated_ideas` table

UI hiện tại KHÔNG có trang để:
- Xem danh sách ideas
- Chọn 1 idea để generate script
- Xem opportunity description

### Mục đích task group này

- Trang **`/ideas/[assistant_id]`** hiển thị ideas
- **Filter/sort** theo Gap Score
- **Select idea** → trigger Generate Script
- **Re-generate** nếu muốn cluster lại

### Phụ thuộc

- ✅ Task 6: Channel Assistants
- ✅ Task 7: Deep Analysis (cần analysis để có topics)
- ✅ Backend: `generated_ideas` table (migration 0017)
- ✅ Backend: `idea_generate.py` worker

---

## 2. Data Model

### generated_ideas (Sprint 3)

```sql
CREATE TABLE generated_ideas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(id),
  assistant_id UUID REFERENCES channel_assistants(id),
  idea_topic TEXT,
  gap_score FLOAT,  -- 0-100
  cluster_id INT,
  related_topics TEXT[],
  opportunity_description TEXT,
  confidence TEXT,  -- 'high' / 'medium' / 'low'
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 3. UI Layout

### `/ideas/[assistant_id]`

```
┌─────────────────────────────────────────────────────────────────────┐
│  ← Back to Assistant                                                │
│  Ideas: Chú Béo Channel                       [🔄 Regenerate 5c]    │
├─────────────────────────────────────────────────────────────────────┤
│  Stats: 12 ideas | Top gap_score: 87 | Avg: 64                       │
│                                                                      │
│  Filter: [All ▼] [Confidence: All ▼] [Sort: Gap Score ▼]           │
│                                                                      │
│  ┌─ IDEA #1 ─────────────────────────────────────────────────┐    │
│  │ 📌 "Mẹo nấu ăn tiết kiệm"                    gap: 87 ⭐  │    │
│  │ Confidence: HIGH • Cluster 3                                │    │
│  │ Related: tiết kiệm, nấu ăn, mẹo vặt, ngân sách gia đình │    │
│  │ ──────────────────────────────────────────────────────     │    │
│  │ Opportunity: Kênh này chưa có video nào về tiết kiệm...    │    │
│  │                                  [✍️ Tạo Script 30c]       │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─ IDEA #2 ─────────────────────────────────────────────────┐    │
│  │ ...                                                        │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Card Detail

- **Topic:** Idea name
- **Gap Score:** Visual badge 0-100
- **Confidence:** HIGH (green) / MEDIUM (yellow) / LOW (gray)
- **Related topics:** Tags cluster
- **Opportunity:** Description text
- **Action button:** "Tạo Script" → trigger script generation

---

## 4. Files to Create

| File | Purpose |
|------|---------|
| `apps/web/app/ideas/[assistant_id]/page.tsx` | Main ideas page |
| `apps/web/app/api/ideas/[assistant_id]/route.ts` | API proxy |
| `apps/web/components/ideas/idea-card.tsx` | Card component |
| `apps/web/components/ideas/idea-filters.tsx` | Filter UI |
| `apps/web/components/ideas/regenerate-button.tsx` | Trigger |

---

## 5. Acceptance Summary

| # | Criteria |
|---|----------|
| AC1 | List ideas of assistant |
| AC2 | Empty state if no ideas |
| AC3 | Filter by confidence |
| AC4 | Sort by gap score |
| AC5 | "Tạo Script" triggers job |
| AC6 | "Regenerate" charges 5 credits |
| AC7 | RLS isolation |
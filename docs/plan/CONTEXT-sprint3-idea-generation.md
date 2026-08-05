# Sprint 3 Task Group 2: Idea Generation

## 1. Context & Mục đích

### Bối cảnh dự án

**AppDK** là nền tảng SaaS AI tạo kịch bản YouTube chuẩn phong cách kênh mẫu. Sprint 3 xây dựng module **Idea Generation** để gợi ý chủ đề video tiềm năng dựa trên phân tích kênh và trends.

### Sprint 3 trong roadmap

```
Sprint 1: Foundation ✅
Sprint 2: Deep Analysis ✅ (14 outputs)
Sprint 3: AI Script Generation
├── Task Group 1: RAG Retrieval ✅ (done)
├── Task Group 2: Idea Generation ← ĐÂY
├── Task Group 3: Script Generation
├── Task Group 4: Scene Breakdown
└── Task Group 5: Integration
```

### Mục đích task group này

- **HDBSCAN Clustering:** Nhóm các chủ đề từ kênh mẫu thành clusters
- **Gap Score (Formula A14):** Tính điểm "cơ hội" = (Niche Trending - Channel Avg) / Channel Avg
- **Output:** Danh sách "Untapped Opportunities" xếp theo gap score

### Dependencies

- ✅ Sprint 2: Tables `channel_deep_analysis`, `channel_assistants` đã tồn tại
- ✅ Task Group 1: RAG retrieval đã có (dùng cho reference)
- ⏳ Task Group 3: Script Gen (depends on this)

---

## 2. Database Schema

### Tables cần check (Sprint 2)

```sql
-- channel_deep_analysis.metadata_report chứa:
-- {
--   "top_tags": ["tag1", "tag2", ...],
--   "avg_views": 50000,
--   "total_views": 1000000,
--   "top_videos": [...]
-- }
```

### New Table: generated_ideas

```sql
-- Migration: 0015_ideas.sql
CREATE TABLE generated_ideas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
  idea_topic TEXT NOT NULL,
  gap_score FLOAT,
  cluster_id INT,
  related_videos JSONB,
  opportunity_description TEXT,
  confidence TEXT CHECK (confidence IN ('high', 'medium', 'low')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ideas_assistant ON generated_ideas(assistant_id, gap_score DESC);
```

---

## 3. Algorithms

### HDBSCAN Algorithm

```python
# Dùng sklearn.feature_extraction.text.TfidfVectorizer + hdbscan
from sklearn.feature_extraction.text import TfidfVectorizer
from hdbscan import HDBSCAN

# 1. Vectorize topics
vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
vectors = vectorizer.fit_transform(topics)

# 2. Cluster với HDBSCAN
clusterer = HDBSCAN(
    min_cluster_size=3,
    metric='cosine',
    cluster_selection_method='eom',
)
cluster_labels = clusterer.fit_predict(vectors.toarray())

# 3. Assign cluster names (top terms)
```

### Gap Score Formula A14

```
Gap_Score = (Niche_Trending - Channel_Avg) / Channel_Avg

Trong đó:
- Niche_Trending = trending_views dựa trên Google Trends score
- Channel_Avg = avg_views từ kênh mẫu

Ví dụ:
- Channel_Avg = 50,000 views
- Niche_Trending = 75,000 views (Google Trends score 75/100)
- Gap_Score = (75,000 - 50,000) / 50,000 = 0.5 (50% opportunity)
```

### Confidence Levels

| Gap Score | Confidence |
|-----------|------------|
| > 0.3 | HIGH |
| 0.0 - 0.3 | MEDIUM |
| < 0.0 | LOW |

---

## 4. Files to Create

| File | Purpose |
|------|---------|
| `supabase/migrations/0015_ideas.sql` | Create generated_ideas table |
| `apps/worker/services/idea_generator.py` | IdeaGenerator class |
| `apps/worker/tasks/idea_generate.py` | Celery task |
| `apps/worker/services/test_idea_generator.py` | Unit tests |

---

## 5. Acceptance Criteria Summary

| # | Criteria |
|---|----------|
| AC1 | SQL migration tạo bảng `generated_ideas` đúng schema |
| AC2 | HDBSCAN cluster topics thành groups |
| AC3 | Gap Score calculated đúng formula |
| AC4 | Ideas sorted by gap_score DESC |
| AC5 | Confidence assigned correctly |
| AC6 | Unit tests pass |

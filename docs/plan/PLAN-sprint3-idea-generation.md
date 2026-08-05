# Sprint 3 Task Group 2: Idea Generation - Plan

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│  IDEA GENERATION PIPELINE                                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Input: Tags from channel analysis                                │
│  ["cách làm bánh", "mẹo nấu ăn", "review nhà hàng", ...]        │
│                     │                                             │
│                     ▼                                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ STEP 1: TF-IDF Vectorization                              │  │
│  │ • Convert text to vectors                                 │  │
│  │ • max_features=100, ngram_range=(1,2)                     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                     │                                             │
│                     ▼                                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ STEP 2: HDBSCAN Clustering                                 │  │
│  │ • min_cluster_size=3                                      │  │
│  │ • metric='cosine'                                          │  │
│  │ • Output: cluster_id per topic                             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                     │                                             │
│                     ▼                                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ STEP 3: Cluster Naming                                    │  │
│  │ • Extract top terms from centroid                         │  │
│  │ • Use as cluster label                                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                     │                                             │
│                     ▼                                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ STEP 4: Gap Score Calculation (Formula A14)                │  │
│  │ Gap = (Niche_Trending - Channel_Avg) / Channel_Avg         │  │
│  │ Niche_Trending = (trending_score/100) * total_views        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                     │                                             │
│                     ▼                                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ STEP 5: Confidence & Sorting                               │  │
│  │ • HIGH: gap > 0.3                                         │  │
│  │ • MEDIUM: 0 <= gap <= 0.3                                 │  │
│  │ • LOW: gap < 0                                             │  │
│  │ • Sort by gap_score DESC                                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                     │                                             │
│                     ▼                                             │
│  Output: List of Ideas [{topic, gap_score, confidence}, ...]    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Fetch Channel Data

```python
# apps/worker/tasks/idea_generate.py
assistant = supabase.table('channel_assistants').select('*').eq('id', assistant_id).single().execute()
analysis = supabase.table('channel_deep_analysis').select('*').eq('assistant_id', assistant_id).eq('is_latest', True).single().execute()

# Get top tags from metadata
tags = analysis.data['metadata_report']['top_tags'][:20]
channel_avg_views = analysis.data['metadata_report']['avg_views']
```

### 2. HDBSCAN Clustering

```python
class IdeaGenerator:
    def cluster_topics(self, topics: list[str], min_cluster_size: int = 3) -> list[dict]:
        if len(topics) < min_cluster_size:
            return [{'topic': t, 'cluster_id': 0, 'cluster_label': 'misc'} for t in topics]

        # TF-IDF
        vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
        vectors = vectorizer.fit_transform(topics)

        # HDBSCAN
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            metric='cosine',
            cluster_selection_method='eom',
        )
        cluster_labels = clusterer.fit_predict(vectors.toarray())

        # Get cluster names
        cluster_names = {}
        for label in set(cluster_labels):
            if label == -1:
                cluster_names[label] = 'outlier'
            else:
                centroid = vectors[cluster_labels == label].mean(axis=0).A1
                top_indices = centroid.argsort()[-2:][::-1]
                features = vectorizer.get_feature_names_out()
                cluster_names[label] = ', '.join(features[i] for i in top_indices)

        return [
            {'topic': t, 'cluster_id': int(cid), 'cluster_label': cluster_names.get(cid, 'unknown')}
            for t, cid in zip(topics, cluster_labels)
        ]
```

### 3. Gap Score Calculation

```python
def calculate_gap_score(
    topic: str,
    channel_views: int,
    channel_avg_views: float,
    niche_trending: float,  # 0-100 from Google Trends
) -> float:
    if channel_avg_views == 0:
        return 0.0

    # Niche views = (trending_score/100) * total_views
    niche_avg_views = (niche_trending / 100) * channel_views

    # Gap Score
    gap_score = (niche_avg_views - channel_avg_views) / channel_avg_views
    return round(gap_score, 3)
```

### 4. Confidence Assignment

```python
def assign_confidence(gap_score: float) -> str:
    if gap_score > 0.3:
        return 'high'
    elif gap_score >= 0:
        return 'medium'
    else:
        return 'low'
```

## Files to Create

### 1. SQL Migration

**File:** `supabase/migrations/0015_ideas.sql`

```sql
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
CREATE INDEX idx_ideas_cluster ON generated_ideas(assistant_id, cluster_id);
```

### 2. Python Service

**File:** `apps/worker/services/idea_generator.py`

### 3. Celery Task

**File:** `apps/worker/tasks/idea_generate.py`

### 4. Unit Tests

**File:** `apps/worker/services/test_idea_generator.py`

# Sprint 3 Task Group 2: Idea Generation - Micro-Step Execution Workflow

## MSEW Checklist

- [ ] **Bước 1:** Tạo SQL migration `0015_ideas.sql`
- [ ] **Bước 2:** Implement `IdeaGenerator` class
- [ ] **Bước 3:** Implement Celery task
- [ ] **Bước 4:** Viết unit tests
- [ ] **Bước 5:** Verify với acceptance criteria

---

## Bước 1: SQL Migration

**File:** `supabase/migrations/0015_ideas.sql`

```sql
-- ============================================================
-- Migration: 0015_ideas.sql
-- Purpose: Table for generated ideas/opportunities
-- ============================================================

CREATE TABLE IF NOT EXISTS generated_ideas (
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

CREATE INDEX IF NOT EXISTS idx_ideas_assistant ON generated_ideas(assistant_id, gap_score DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_cluster ON generated_ideas(assistant_id, cluster_id);

-- RLS
ALTER TABLE generated_ideas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_can_read_own_ideas" ON generated_ideas FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = generated_ideas.assistant_id
        AND ca.user_id = auth.uid()
    )
  );

CREATE POLICY "service_can_insert_ideas" ON generated_ideas FOR INSERT
  WITH CHECK (true);  -- Worker uses service_role
```

---

## Bước 2: Python IdeaGenerator Service

**File:** `apps/worker/services/idea_generator.py`

```python
"""
Idea Generation Service - HDBSCAN clustering & Gap Score calculation.
"""
from typing import Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from hdbscan import HDBSCAN


class IdeaGenerator:
    """Service for generating video topic ideas with gap analysis."""

    def cluster_topics(
        self,
        topics: list[str],
        min_cluster_size: int = 3,
    ) -> list[dict]:
        """
        Cluster topics using HDBSCAN.
        
        Args:
            topics: List of topic strings
            min_cluster_size: Minimum points per cluster
            
        Returns:
            List of dicts with topic, cluster_id, cluster_label
        """
        if not topics:
            return []

        # Edge case: not enough topics
        if len(topics) < min_cluster_size:
            return [
                {'topic': t, 'cluster_id': 0, 'cluster_label': 'misc'}
                for t in topics
            ]

        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(
            max_features=100,
            ngram_range=(1, 2),
        )
        vectors = vectorizer.fit_transform(topics)

        # HDBSCAN clustering
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            metric='cosine',
            cluster_selection_method='eom',
        )
        cluster_labels = clusterer.fit_predict(vectors.toarray())

        # Assign cluster names (top terms from centroid)
        cluster_names = self._get_cluster_names(
            vectors, cluster_labels, vectorizer, topics
        )

        return [
            {
                'topic': topic,
                'cluster_id': int(cluster_id),
                'cluster_label': cluster_names.get(cluster_id, 'unknown'),
            }
            for topic, cluster_id in zip(topics, cluster_labels)
        ]

    def _get_cluster_names(
        self,
        vectors,
        labels: np.ndarray,
        vectorizer: TfidfVectorizer,
        topics: list[str],
    ) -> dict:
        """Extract cluster names from top terms."""
        names = {}
        feature_names = vectorizer.get_feature_names_out()

        for label in set(labels):
            if label == -1:  # Noise
                names[label] = 'outlier'
                continue

            # Get indices for this cluster
            mask = labels == label
            if not mask.any():
                continue

            # Calculate centroid
            centroid = vectors[mask].mean(axis=0).A1

            # Get top 2 terms
            top_indices = centroid.argsort()[-2:][::-1]
            names[label] = ', '.join(feature_names[i] for i in top_indices)

        return names

    def calculate_gap_score(
        self,
        topic: str,
        channel_views: int,
        channel_avg_views: float,
        niche_trending: float,
    ) -> float:
        """
        Calculate gap score using Formula A14.
        
        Gap_Score = (Niche_Trending - Channel_Avg) / Channel_Avg
        
        Args:
            topic: Topic name (for reference)
            channel_views: Total channel views
            channel_avg_views: Average views per video
            niche_trending: Trending score 0-100 (Google Trends)
            
        Returns:
            Gap score (e.g., 0.25 = 25% opportunity)
        """
        if channel_avg_views <= 0:
            return 0.0

        # Estimate niche views from trending score
        niche_avg_views = (niche_trending / 100) * channel_views

        # Gap Score
        gap_score = (niche_avg_views - channel_avg_views) / channel_avg_views
        return round(gap_score, 3)

    def assign_confidence(self, gap_score: float) -> str:
        """Assign confidence level based on gap score."""
        if gap_score > 0.3:
            return 'high'
        elif gap_score >= 0:
            return 'medium'
        else:
            return 'low'

    def generate_opportunity_description(
        self,
        topic: str,
        gap_score: float,
    ) -> str:
        """Generate human-readable opportunity description."""
        if gap_score > 0.5:
            return f"Rất tiềm năng: {topic} đang trending cao hơn 50% so với mức trung bình của kênh"
        elif gap_score > 0.2:
            return f"Cơ hội tốt: {topic} trending cao hơn 20% so với mức trung bình của kênh"
        elif gap_score > 0:
            return f"Có tiềm năng: {topic} đang trending cao hơn mức trung bình của kênh"
        else:
            return f"Cạnh tranh cao: {topic} đang trending thấp hơn mức trung bình của kênh"
```

---

## Bước 3: Celery Task

**File:** `apps/worker/tasks/idea_generate.py`

```python
"""
Celery task for idea generation.
"""
from celery import Task
from apps.worker.celery_app import celery_app
from apps.worker.services.progress_tracker import ProgressTracker
from apps.worker.services.supabase_admin import get_supabase_admin
from apps.worker.services.idea_generator import IdeaGenerator


@celery_app.task(
    name='apps.worker.tasks.idea_generate.run',
    bind=True,
    max_retries=2,
    acks_late=True,
)
def run(self: Task, job_id: str, assistant_id: str) -> dict:
    """
    Generate video topic ideas with gap analysis.
    
    Args:
        job_id: Job UUID
        assistant_id: Channel assistant UUID
        
    Returns:
        dict with ideas list
    """
    supabase = get_supabase_admin()
    tracker = ProgressTracker(supabase, job_id)

    try:
        # === FETCH DATA ===
        tracker.start('fetch_data')

        assistant = supabase.table('channel_assistants').select('*').eq('id', assistant_id).single().execute()
        if not assistant.data:
            raise ValueError(f"Assistant {assistant_id} not found")

        analysis = supabase.table('channel_deep_analysis').select('*').eq('assistant_id', assistant_id).eq('is_latest', True).single().execute()
        if not analysis.data:
            raise ValueError(f"No analysis found for assistant {assistant_id}")

        metadata = analysis.data.get('metadata_report', {})
        tags = metadata.get('top_tags', [])[:20]
        channel_avg_views = metadata.get('avg_views', 50000)
        channel_total_views = metadata.get('total_views', 1000000)

        tracker.done('fetch_data')

        # === CLUSTER TOPICS ===
        tracker.start('cluster_topics')

        generator = IdeaGenerator()
        clustered = generator.cluster_topics(tags, min_cluster_size=3)

        tracker.done('cluster_topics')

        # === CALCULATE GAP SCORES ===
        tracker.start('gap_analysis')

        ideas = []
        for cluster_id in set(c['cluster_id'] for c in clustered):
            if cluster_id == -1:  # Skip noise
                continue

            cluster_topics = [c['topic'] for c in clustered if c['cluster_id'] == cluster_id]
            cluster_label = clustered[0]['cluster_label']

            # Mock trending score (would come from Google Trends API)
            trending_score = 50.0

            gap_score = generator.calculate_gap_score(
                topic=cluster_label,
                channel_views=channel_total_views,
                channel_avg_views=channel_avg_views,
                niche_trending=trending_score,
            )

            ideas.append({
                'idea_topic': cluster_label,
                'gap_score': gap_score,
                'cluster_id': cluster_id,
                'related_topics': cluster_topics[:5],
                'opportunity_description': generator.generate_opportunity_description(cluster_label, gap_score),
                'confidence': generator.assign_confidence(gap_score),
            })

        # Sort by gap score
        ideas.sort(key=lambda x: x['gap_score'], reverse=True)

        tracker.done('gap_analysis')

        # === SAVE RESULTS ===
        result = {
            'ideas': ideas,
            'total_ideas': len(ideas),
            'top_opportunities': ideas[:5],
        }

        supabase.table('jobs').update({
            'status': 'succeeded',
            'progress': 100,
            'result_payload': result,
            'sub_progress': tracker.get_sub_progress(),
        }).eq('id', job_id).execute()

        # Save ideas to database
        for idea in ideas:
            supabase.table('generated_ideas').insert({
                'job_id': job_id,
                'assistant_id': assistant_id,
                'idea_topic': idea['idea_topic'],
                'gap_score': idea['gap_score'],
                'cluster_id': idea['cluster_id'],
                'opportunity_description': idea['opportunity_description'],
                'confidence': idea['confidence'],
            }).execute()

        return result

    except Exception as e:
        tracker.fail('idea_generate', str(e))
        supabase.table('jobs').update({
            'status': 'failed',
            'error_message': str(e),
        }).eq('id', job_id).execute()
        raise
```

---

## Bước 4: Unit Tests

**File:** `apps/worker/services/test_idea_generator.py`

```python
"""
Unit tests for IdeaGenerator service.
"""
import pytest
import numpy as np
from apps.worker.services.idea_generator import IdeaGenerator


class TestIdeaGenerator:
    """Test suite for IdeaGenerator."""

    @pytest.fixture
    def generator(self):
        return IdeaGenerator()

    def test_cluster_topics_few_topics(self, generator):
        """Test clustering with fewer topics than min_cluster_size."""
        topics = ['topic1', 'topic2']
        result = generator.cluster_topics(topics, min_cluster_size=3)

        assert len(result) == 2
        assert all(r['cluster_id'] == 0 for r in result)
        assert all(r['cluster_label'] == 'misc' for r in result)

    def test_cluster_topics_multiple_clusters(self, generator):
        """Test clustering with multiple distinct topics."""
        topics = [
            'cách làm bánh chocolate',
            'cách làm bánh gato',
            'cách làm bánh quy',
            'review nhà hàng hàn quốc',
            'review nhà hàng ý',
            'review nhà hàng việt nam',
        ]
        result = generator.cluster_topics(topics, min_cluster_size=2)

        assert len(result) == 6
        assert all('cluster_id' in r for r in result)

    def test_calculate_gap_score_positive(self, generator):
        """Test gap score when niche is trending higher."""
        score = generator.calculate_gap_score(
            topic='test',
            channel_views=100000,
            channel_avg_views=50000,
            niche_trending=75.0,  # 75% trending
        )
        # Niche views = 75% of 100000 = 75000
        # Gap = (75000 - 50000) / 50000 = 0.5
        assert score == 0.5

    def test_calculate_gap_score_negative(self, generator):
        """Test gap score when niche is trending lower."""
        score = generator.calculate_gap_score(
            topic='test',
            channel_views=100000,
            channel_avg_views=50000,
            niche_trending=25.0,  # 25% trending
        )
        # Niche views = 25% of 100000 = 25000
        # Gap = (25000 - 50000) / 50000 = -0.5
        assert score == -0.5

    def test_calculate_gap_score_zero_avg(self, generator):
        """Test gap score when avg views is zero."""
        score = generator.calculate_gap_score(
            topic='test',
            channel_views=0,
            channel_avg_views=0,
            niche_trending=50.0,
        )
        assert score == 0.0

    def test_assign_confidence_high(self, generator):
        """Test HIGH confidence for gap > 0.3."""
        assert generator.assign_confidence(0.4) == 'high'
        assert generator.assign_confidence(1.0) == 'high'

    def test_assign_confidence_medium(self, generator):
        """Test MEDIUM confidence for 0 <= gap <= 0.3."""
        assert generator.assign_confidence(0.0) == 'medium'
        assert generator.assign_confidence(0.3) == 'medium'
        assert generator.assign_confidence(0.15) == 'medium'

    def test_assign_confidence_low(self, generator):
        """Test LOW confidence for gap < 0."""
        assert generator.assign_confidence(-0.1) == 'low'
        assert generator.assign_confidence(-0.5) == 'low'

    def test_generate_opportunity_description_high(self, generator):
        """Test description for high opportunity."""
        desc = generator.generate_opportunity_description('test topic', 0.6)
        assert 'Rất tiềm năng' in desc
        assert '50%' in desc

    def test_generate_opportunity_description_medium(self, generator):
        """Test description for medium opportunity."""
        desc = generator.generate_opportunity_description('test topic', 0.25)
        assert 'Cơ hội tốt' in desc or 'Có tiềm năng' in desc

    def test_generate_opportunity_description_low(self, generator):
        """Test description for low opportunity."""
        desc = generator.generate_opportunity_description('test topic', -0.2)
        assert 'Cạnh tranh cao' in desc
```

---

## Bước 5: Verify

```bash
# Apply migration
supabase db push

# Run tests
cd apps/worker && pytest services/test_idea_generator.py -v

# Check coverage
pytest --cov=apps.worker.services.idea_generator --cov-report=term-missing
```

---

## Commands for Tier 2

```bash
# ============================================================
# TASK: Sprint 3 - Idea Generation
# ============================================================

cat docs/plan/CONTEXT-sprint3-idea-generation.md
cat docs/plan/SKILL-ROUTING-sprint3-idea-generation.md
cat docs/plan/PLAN-sprint3-idea-generation.md
cat docs/plan/MSEW-sprint3-idea-generation.md
cat docs/plan/ACCEPTANCE-sprint3-idea-generation.md
```

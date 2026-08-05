# Sprint 3 Task Group 2: Idea Generation - Acceptance Criteria

## Definition of Done

### Để task này được coi là **HOÀN THÀNH**, Tầng 2 phải:

---

## AC1: SQL Migration

- [ ] **AC1.1:** Migration file `0015_ideas.sql` tồn tại
- [ ] **AC1.2:** Table `generated_ideas` có đúng columns
- [ ] **AC1.3:** Foreign key đến `channel_assistants`
- [ ] **AC1.4:** Indexes on `assistant_id, gap_score` và `assistant_id, cluster_id`
- [ ] **AC1.5:** CHECK constraint cho `confidence` column

### Test AC1:

```sql
-- Verify table exists
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'generated_ideas';
```

---

## AC2: HDBSCAN Clustering

- [ ] **AC2.1:** Topics được cluster thành groups
- [ ] **AC2.2:** Noise points (cluster_id = -1) được handle
- [ ] **AC2.3:** Cluster labels = top terms từ centroid
- [ ] **AC2.4:** Edge case: < min_cluster_size topics → all 'misc'

### Test AC2:

```python
generator = IdeaGenerator()
topics = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'a', 'b', 'c']
result = generator.cluster_topics(topics, min_cluster_size=3)
assert len(result) == len(topics)
assert all('cluster_id' in r for r in result)
```

---

## AC3: Gap Score Calculation

- [ ] **AC3.1:** Formula đúng: `(Niche - Avg) / Avg`
- [ ] **AC3.2:** Niche views = `(trending/100) * total_views`
- [ ] **AC3.3:** Gap > 0 khi niche trending > channel avg
- [ ] **AC3.4:** Gap < 0 khi niche trending < channel avg
- [ ] **AC3.5:** Round to 3 decimal places

### Test AC3:

```python
# Test positive gap
score = generator.calculate_gap_score(
    topic='test',
    channel_views=100000,  # total views
    channel_avg_views=50000,  # avg views
    niche_trending=75.0,  # trending 75%
)
# Niche = 75% * 100000 = 75000
# Gap = (75000 - 50000) / 50000 = 0.5
assert score == 0.5

# Test negative gap
score = generator.calculate_gap_score(
    topic='test',
    channel_views=100000,
    channel_avg_views=50000,
    niche_trending=25.0,  # trending 25%
)
# Niche = 25% * 100000 = 25000
# Gap = (25000 - 50000) / 50000 = -0.5
assert score == -0.5
```

---

## AC4: Ideas Sorting & Confidence

- [ ] **AC4.1:** Ideas sorted by `gap_score` DESC
- [ ] **AC4.2:** Confidence HIGH for gap > 0.3
- [ ] **AC4.3:** Confidence MEDIUM for 0 <= gap <= 0.3
- [ ] **AC4.4:** Confidence LOW for gap < 0
- [ ] **AC4.5:** Opportunity description generated correctly

### Test AC4:

```python
assert generator.assign_confidence(0.5) == 'high'
assert generator.assign_confidence(0.2) == 'medium'
assert generator.assign_confidence(-0.1) == 'low'
```

---

## AC5: Celery Task

- [ ] **AC5.1:** Task `apps.worker.tasks.idea_generate.run` registered
- [ ] **AC5.2:** Task uses `ProgressTracker`
- [ ] **AC5.3:** Fetches data from `channel_deep_analysis`
- [ ] **AC5.4:** Saves ideas to `generated_ideas` table
- [ ] **AC5.5:** Updates job status on success/failure

---

## AC6: Unit Tests

- [ ] **AC6.1:** Test file exists: `test_idea_generator.py`
- [ ] **AC6.2:** Test `cluster_topics` with edge cases
- [ ] **AC6.3:** Test `calculate_gap_score` with positive/negative
- [ ] **AC6.4:** Test `assign_confidence` boundary values
- [ ] **AC6.5:** All tests pass: `pytest -v`

---

## AC7: Code Quality

- [ ] **AC7.1:** Type hints for all methods
- [ ] **AC7.2:** Docstrings for class and public methods
- [ ] **AC7.3:** No linter errors
- [ ] **AC7.4:** Follows existing patterns (`get_supabase_admin()`)

---

## Self-Check Checklist

1. [ ] All AC1-AC7 ✅
2. [ ] `pytest services/test_idea_generator.py -v` → PASSED
3. [ ] `ReadLints` → No errors

---

## Sign-off

```
✓ Task: Sprint 3 - Idea Generation
✓ Status: COMPLETED
✓ Files Created:
  - supabase/migrations/0015_ideas.sql
  - apps/worker/services/idea_generator.py
  - apps/worker/tasks/idea_generate.py
  - apps/worker/services/test_idea_generator.py
✓ All Acceptance Criteria: PASSED
✓ Ready for next task group: Script Generation
```

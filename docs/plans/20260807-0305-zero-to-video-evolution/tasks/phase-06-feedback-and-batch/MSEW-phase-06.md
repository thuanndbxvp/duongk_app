# MSEW: Phase 06 — Feedback Loop (subset: Channel Intelligence only)

> Lưu ý: Batch production đã được tách sang Phase 10 để tránh phụ thuộc Phase 04 cancel/idempotency. Phase 06 tập trung Channel Intelligence.

## Prerequisites
- Phase 01 + Phase 08 dependencies merged.

## Files KHÔNG được đụng
- `apps/worker/tasks/script_generate.py` core flow (chỉ thêm evidence injection).
- `apps/web/app/(dashboard)/channels/**` flow cũ.

---

## Micro-Steps

### Step 1: Migration `0027_channel_intel.sql`
Như Phase 08 đã mô tả. Cần: `channel_profile_versions`, `comment_clusters`, `insight_items`, `insight_outcomes`, `comment_ingest_batches`. RLS qua `channel_assistants.user_id`.

### Step 2: CommentProvider abstraction

```python
# apps/worker/services/comments_provider.py
class CommentsProvider(ABC):
    @abstractmethod
    async def fetch(self, video_ids: list[str], page_token: str = None) -> list[CommentRow]: ...

class YouTubeDataAPIProvider(CommentsProvider):
    def __init__(self, api_key: str): ...
```

### Step 3: ingest_comments task

```python
@shared_task(bind=True, max_retries=3)
def ingest_comments(self, batch_id: UUID):
    # Idempotency: skip nếu batch đã success
    # Pagination loop với rate-limit 1000 units/min
    # Ghi vào comment_ingest_batches
```

### Step 4: build_insights task

```python
@shared_task
def build_insights(assistant_id: UUID):
    # 1. cluster_comments(comments) → HDBSCAN → topic_label, size, sentiment
    # 2. build_insight_from_cluster(cluster) → LLM response REQUIRE evidence_comment_ids
    # 3. Lưu insight_items với status='pending'
    # 4. calculate_opportunity_score()
```

### Step 5: RAG upgrade

```python
# apps/worker/services/rag_service.py
async def build_context(brief, channel_dna=None, source_insight_ids=None):
    # ... existing logic
    if source_insight_ids:
        snippets = load_evidence_snippets(source_insight_ids)
        prompt += "\n[evidence]\n" + snippets + "\n[evidence_end]\n"
    return prompt
```

### Step 6: API endpoints

```python
# POST /api/assistants/{id}/references
# POST /api/assistants/{id}/ingest
# GET /api/assistants/{id}/insights
# POST /api/insights/{id}/approve
# POST /api/insights/{id}/reject
# POST /api/insights/{id}/to-project → trả project_id mới (Phase 01)
```

### Step 7: UI

`insight-card.tsx` — render insight + evidence chip + actions.

### Step 8: Tests

```powershell
pytest tests/worker/test_insights_service.py tests/api/test_channel_intel.py -v --cov=apps.worker.services.insights_service --cov=apps.worker.services.comments_provider --cov-report=term-missing
```

Test cases:
- Insight không có evidence_ids → LLM response bị reject.
- Approve insight → tạo project với brief seed từ insight.
- RLS: user A không đọc insight của user B.
- Rate-limit guard test với quota mock.
- RAG context có evidence tag khi source_insight_ids cung cấp.
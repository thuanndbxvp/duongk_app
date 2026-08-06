# MSEW: Phase 08 — Channel Intelligence

## Micro-Steps

### Step 1: Routing extension
- `service_routing_config` thêm `comment_intel=youtube_data_api`, `topic_cluster=hdbscan`, `trend_provider=google_trends_serpapi` (feature flag).

### Step 2: Migration `0027_channel_intel.sql`
Như đã spec trong `phase-08-channel-intelligence.md` mục 5.

### Step 3: CommentsProvider + YouTubeDataAPIProvider
- Pagination, retry 5xx, rate-limit 1000 units/min.

### Step 4: ingest_comments
- Idempotency: `(assistant_id, batch_id)`.
- Ghi `comment_ingest_batches`.

### Step 5: build_insights
- HDBSCAN trên embedding (đã có Cohere).
- LLM yêu cầu `evidence_comment_ids`; reject nếu thiếu.
- `calculate_opportunity_score = 0.4*gap + 0.3*evidence + 0.2*freshness + 0.1*confidence`.

### Step 6: RAG upgrade
- `rag_service.build_context()` chèn `[evidence] ... [evidence_end]` block.

### Step 7: API
```python
# POST /api/assistants/{id}/references
# POST /api/assistants/{id}/ingest
# GET /api/assistants/{id}/insights
# POST /api/insights/{id}/approve
# POST /api/insights/{id}/to-project
```

### Step 8: UI
- InsightCard với evidence chip click mở drawer.
- Page insights filter theo kind/status/freshness.

### Step 9: Tests
```powershell
pytest tests/worker/test_insights_service.py tests/api/test_channel_intel.py -v
```
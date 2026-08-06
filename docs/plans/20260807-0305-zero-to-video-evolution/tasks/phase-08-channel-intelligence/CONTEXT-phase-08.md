# CONTEXT: Phase 08 — Channel Intelligence Feedback Loop

## 1. Repomix: `.\CONTEXT_BUNDLE.md`

## 2. Files (chi tiết Phase 08)
### Modify
- `apps/worker/services/idea_generator.py` — thêm `cluster_comments()`, `opportunity_score()`.
- `apps/worker/services/rag_service.py` — `build_context()` đọc channel profile version + inject evidence.
- `apps/api/routers/analysis.py` — endpoints lấy/approve insight.
- `apps/api/routers/ideas.py` — trả `source_insight_id`, `opportunity_score`.

### Create
- `apps/api/routers/channel_intel.py`
- `apps/api/schemas/channel_intel.py`
- `apps/worker/services/comments_provider.py`
- `apps/worker/services/insights_service.py`
- `apps/worker/tasks/ingest_comments.py`
- `apps/worker/tasks/build_insights.py`
- `apps/web/components/insight-card.tsx`
- `apps/web/app/(dashboard)/assistants/[id]/insights/page.tsx`
- `apps/web/app/(dashboard)/assistants/[id]/references/page.tsx`

## 3. Dependencies
- YouTube Data API (chính thức).
- HDBSCAN, scikit-learn.
- Existing `dna_chunks`, `transcripts`, `channel_deep_analysis`.

## 4. Ràng buộc
- Insight phải có evidence_ids[] (bắt buộc).
- Mỗi insight có `freshness_at`; giảm weight khi stale.
- Quota guard: max 5000 comments/channel/ngày.
- KHÔNG scrape qua session; chỉ API chính thức.
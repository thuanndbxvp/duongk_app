# CONTEXT: Phase 06 — Feedback Loop, Channel Intelligence & Batch Production

## 1. Repomix: `.\CONTEXT_BUNDLE.md`

## 2. Codebase
- `channel_assistants`, `channel_deep_analysis`, `dna_chunks`, `transcripts` đã có.
- `credit_transactions` có sẵn.
- Phase 01–05 cung cấp project foundation + scene + asset + voice + render.

## 3. Files
### Modify
- `apps/worker/services/idea_generator.py`
- `apps/worker/services/rag_service.py`
- `apps/api/routers/analysis.py`
- `apps/api/routers/ideas.py`
- `apps/web/app/(dashboard)/dashboard/page.tsx`
- `apps/web/app/(dashboard)/assistants/[id]/page.tsx`

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

## 4. Dependencies
- YouTube Data API client, google-generativeai, scikit-learn, hdbscan.

## 5. Ràng buộc
- Chỉ dùng YouTube Data API chính thức — KHÔNG scrape.
- Evidence-backed: insight phải có evidence_ids[] trước khi persist.
- Batch chỉ chạy sau khi Phase 04 cancel/idempotency ổn định.
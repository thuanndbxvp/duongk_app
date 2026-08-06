# ACCEPTANCE: Phase 06 — Channel Intelligence (subset)

## 1. Functional
- [ ] Channel profile versioned (audience, editorial_rules, voice_profile_id, visual_style, thumbnail_rules, forbidden_claims).
- [ ] User import video ID/URL → ingest comments qua YouTube Data API.
- [ ] Cluster comments với HDBSCAN; có `topic_label`, `size`, `sentiment_score`.
- [ ] Insight có `evidence_ids[]` bắt buộc.
- [ ] Approve insight → tạo project với brief seed từ insight.
- [ ] RAG build_context inject evidence snippet khi có source_insight_ids.

## 2. Non-functional
- [ ] Quota guard: max 5000 comments/channel/ngày.
- [ ] Prompt injection escape.
- [ ] Stale insight giảm weight sau 30 ngày.

## 3. Coverage
- ≥80% cho `insights_service`, `comments_provider`, `rag_service` (chỉ phần mới).

## 4. Done
- All pass + AUDIT-REPORT nộp.
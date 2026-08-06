# PLAN: Phase 08 — Channel Intelligence

## 1. Mục tiêu
- Biến DNA + RAG thành **đề xuất có bằng chứng**.
- User duyệt insight/idea trước khi đưa vào brief.
- Channel profile versioned; rollback được.

## 2. Kiến trúc
```text
YouTube Data API → ingest_comments → comment_normalized
  → build_insights (HDBSCAN + LLM yêu cầu evidence_comment_ids)
  → insight_items (status='pending')
  → User approve → idea v2 + opportunity_score
  → Project brief seed từ insight (Phase 01)
```

## 3. Rủi ro
| Rủi ro | Giảm thiểu |
|---|---|
| Insight không có evidence | Schema bắt buộc, LLM response reject |
| Prompt injection từ comment | Escape + tag rõ |
| Quota cạn | Rate-limit guard |
| Stale insight | freshness_at giảm weight |
# PLAN: Phase 06 — Feedback Loop

## 1. Mục tiêu
- Channel profile versioned, comment intelligence qua API chính thức, evidence-backed insights, RAG inject evidence.

## 2. Kiến trúc
```text
YouTube Data API → CommentProvider.fetch()
  → ingest_comments task → comment_normalized
  → build_insights task → HDBSCAN cluster → LLM insight (require evidence_ids)
  → User approve → idea v2 với source_insight_id
  → Project brief seed từ insight
```

## 3. Lựa chọn
- **Phương án A — Browser session scrape (ĐÃ LOẠI):** Rủi ro pháp lý.
- **Phương án B — YouTube Data API chính thức (CHỌN):** An toàn, có quota.
- **Phương án C — Scrape + API fallback (CÂN NHẮC):** Rủi ro khi scrape fail.

## 4. Rủi ro
| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Insight không có evidence | Cao | Schema require evidence_ids, LLM response reject nếu thiếu. |
| Quota YouTube cạn | Trung bình | Rate-limit guard, retry sau. |
| Prompt injection từ comment | Trung bình | Escape, tag rõ ràng `[evidence]` block. |
| Stale insight | Thấp | Freshness factor giảm weight. |

## 5. Nỗ lực
- ~1000 LOC, 8 micro-steps, 5 ngày Tier 2.
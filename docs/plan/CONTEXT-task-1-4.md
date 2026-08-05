# Bối cảnh Hệ thống (CONTEXT): Task 1.4 - Module 1 Niche Validate

## 1. Tri thức Tổng hợp
- **Task:** Sprint 1 - Module 1: Niche Validation (Discovery)
- **Mục tiêu:** Xây dựng pipeline 10 bước để validate niche khả thi cho YouTube
- **Tài liệu tham khảo:**
  - `docs/plan/PLAN-task-1-4.md` - Kiến trúc chi tiết
  - `docs/implementation_plan_v1_fixes.md` §1.4

## 2. Module đã có (Sprint 1)

### Đã hoàn thành trước đó:
- `/apps/api/` - FastAPI app structure
- `/apps/worker/` - Celery worker structure
- `/packages/shared-types/` - Pydantic models

### Dependencies đã cài:
- `redis[hiredis]` - Async Redis client
- `tenacity` - Retry policy

## 3. Các File liên quan và Vai trò

| File | Vai trò | Priority |
|------|---------|----------|
| `apps/api/core/bulkhead.py` | TokenBucket utility (NEW) | HIGH |
| `apps/api/core/cache.py` | Redis Cache với Lock (NEW) | HIGH |
| `apps/api/modules/module_1/__init__.py` | Module 1 package init | MEDIUM |
| `apps/api/modules/module_1/formulas.py` | Formula A0, A2 (NEW) | HIGH |
| `apps/api/modules/module_1/service.py` | NicheValidator service (NEW) | HIGH |
| `apps/api/modules/module_1/routes.py` | API routes (NEW) | HIGH |
| `apps/api/modules/module_1/schemas.py` | Pydantic schemas (NEW) | HIGH |
| `tests/test_module_1/` | Test suite (NEW) | HIGH |

## 4. Dependencies mới cần cài

```bash
pip install pytrends serpapi numpy
```

## 5. Kiến trúc Module 1

```
┌─────────────────────────────────────────────────────────────────┐
│                    MODULE 1: NICHE VALIDATE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HTTP Request ──► TokenBucket (rate limit)                      │
│                       │                                         │
│                       ▼                                         │
│                  Redis Cache ──► [HIT] ──► Return cached          │
│                       │                                         │
│                       │ [MISS]                                   │
│                       ▼                                         │
│              Pytrends API ──► [SUCCESS] ──► Save cache          │
│                  │          │                                  │
│                  │ [FAIL]    │                                  │
│                  ▼           ▼                                  │
│            SerpAPI ──► [SUCCESS] ──► Save cache                 │
│              │         │                                        │
│              │ [FAIL]   │                                        │
│              ▼          ▼                                        │
│        Formula A0 ──► Filter Quality Videos                     │
│              │                                                    │
│              ▼                                                    │
│        Formula A2 ──► Detect Viral (MAD)                        │
│              │                                                    │
│              ▼                                                    │
│         Response ──► { is_viable, suggested_titles, ... }       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 6. Ràng buộc (Constraints)

| Ràng buộc | Mô tả |
|-----------|--------|
| **Môi trường** | Windows 10/11 (PowerShell) |
| **Line Ending** | CRLF |
| **Python** | 3.10+ |
| **Redis** | localhost:6379 |
| **API Key** | Cần SUPABASE_URL, PYTRENDS, SERPAPI_KEY |
| **Rate Limit** | Pytrends: 1 req/10s (TokenBucket) |

## 7. Sample Response (Expected)

```json
{
  "keyword": "làm đẹp",
  "total_monthly_views": 15000000,
  "total_channels": 45,
  "avg_views_per_video": 45000,
  "google_trends_interest": 72,
  "is_viable": true,
  "suggested_titles": [
    "5 công thức làm đẹp từ thiên nhiên",
    "Cách chăm sóc da mùa đông"
  ]
}
```

## 8. Repomix Bundle

- **Bundle file:** `CONTEXT_BUNDLE.md` (sẽ được tạo bởi Tier 1)

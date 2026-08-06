# Kế hoạch Triển khai (PLAN): phase7-admin-api-keys

## 1. Mục tiêu (Objective)
- **Mô tả ngắn gọn:** Sprint A3 — API Key Management cho Admin Panel. 3 migration + 3 service + 9 endpoint + 7 file frontend.
- **Giá trị cốt lõi:**
  1. Admin thêm/xoay key provider (OpenAI, Cohere, R2, Modal, Supadata, SerpAPI, ...) qua UI — không cần SSH vào server.
  2. Encryption AES-GCM cho raw value (không ai đọc được từ DB).
  3. Cost tracking infrastructure (chưa cron reset, chỉ tracking) cho budget alerts.

## 2. Kiến trúc lựa chọn (Architecture)

### Pattern: Encrypted key vault + provider-scoped resolver
```
[Admin UI] 
  → fetch /api/admin/api-keys/[id]/test (Next.js proxy)
    → FastAPI POST /api/admin/api-keys/{id}/test
      → Depends(require_admin)
      → vault.decrypt(api_provider_keys.encrypted_value)
      → ping provider (OpenAI: models.list(), Cohere: embed, R2: head_bucket, Modal: function lookup)
      → return {ok: bool, latency_ms, error}
      → log_admin_action('api_key.test', before={last_test_status: 'ok'}, after={last_test_status: 'ok', latency_ms: 234})
```

### Cấu trúc file

**Migrations (3 NEW):**
```
supabase/migrations/
  0023_api_provider_keys.sql       — table + indexes
  0024_api_usage_logs.sql           — table + trigger
  0025_admin_alerts.sql             — table + RPC create_alert
```

**Backend services (3 NEW):**
```
apps/api/services/
  vault.py                  — Fernet encrypt/decrypt
  key_resolver.py           — cache 60s + fallback chain
  usage_tracker.py          — decorator @track_usage(provider)
```

**Backend routers (2 NEW):**
```
apps/api/routers/
  admin_api_keys.py         — 7 endpoints (list, create, update, rotate, delete, test, usage)
  admin_alerts.py           — 2 endpoints (list unresolved, resolve)
```

**Frontend (8 NEW + 1 UPDATE):**
```
apps/web/app/api/admin/api-keys/
  route.ts                              (NEW) - GET list + POST create
  [id]/route.ts                         (NEW) - PATCH update + DELETE archive
  [id]/test/route.ts                    (NEW) - POST test
  [id]/rotate/route.ts                  (NEW) - POST rotate
apps/web/app/api/admin/alerts/
  route.ts                              (NEW) - GET list
  [id]/resolve/route.ts                 (NEW) - POST resolve

apps/web/app/(admin)/admin/
  api-keys/page.tsx                     (NEW) - Provider table + form
  alerts/page.tsx                       (NEW) - Alerts list + resolve

apps/web/app/(admin)/layout.tsx         (UPDATE) - Enable API Keys + Alerts
```

## 3. Lý do chọn & Các phương án đã loại trừ (Alternatives)

### Phương án A — Supabase Vault (ĐÃ LOẠI)
- **Lý do loại:** Vault extension cần enable riêng trên Supabase instance + thêm complexity. Fernet đơn giản hơn, đủ bảo mật (key trong env).

### Phương án B — Không encrypt, lưu raw value (ĐÃ LOẠI)
- **Lý do loại:** DB có thể leak (backup, migration, log). Fernet chỉ thêm ~5 LOC.

### Phương án C — Refactor worker Phase 7 để dùng `key_resolver` (ĐÃ LOẠI một phần)
- **Lý do loại:** Worker refactor là Phase 8+ (Sprint A4 Service Routing). Phase 7 chỉ tạo infrastructure, không break existing flow.

### Phương án D — Implement full cron reset cost đầu tháng Phase 7 (ĐÃ LOẢI)
- **Lý do loại:** Cron job là Sprint A5 (Polish). Phase 7 chỉ cần tracking infrastructure + manual check.

### Lý do chọn phương án hiện tại
- **Minimal change:** Worker vẫn dùng `os.environ` (Phase 8+ mới refactor).
- **Encryption:** Fernet AES-GCM, đủ mạnh cho MVP.
- **Phase 7 scope:** CRUD + test + rotate, KHÔNG touch routing.

## 4. Đánh giá rủi ro (Risk Assessment)

| # | Rủi ro | Mức | Giảm thiểu |
|---|--------|-----|------------|
| 1 | Encryption key trong `.env` leak → tất cả provider keys compromise | **Cao** | Generate key riêng, KHÔNG commit. Add `.env` to `.gitignore` (đã có). Doc warning trong ENV-VARS.md. |
| 2 | `key_resolver` cache stale key 60s sau khi admin rotate | Trung bình | Cache TTL = 60s. Phase 8+ sẽ add Redis pub/sub để invalidate ngay khi rotate. |
| 3 | Test endpoint trigger provider call → cost | Trung bình | Test endpoint mỗi key max 1 call. Tier 2 doc khuyến cáo "test sparingly". |
| 4 | Migration fail vì trigger ghi đè cost | Thấp | Step 2 trigger viết idempotent (`ON CONFLICT DO UPDATE`). |
| 5 | Worker KHÔNG dùng `key_resolver` Phase 7 → admin rotate key nhưng worker vẫn dùng env cũ | Trung bình | Phase 7 doc warning rõ ràng. Phase 8+ sẽ refactor worker. |
| 6 | Audit log leak raw key qua `before` snapshot | Trung bình | `audit._SENSITIVE_KEYS` regex đã có `key|token|secret|password|api_key` — mask tự động. |
| 7 | `cryptography` library chưa cài | Thấp | Step 11 verify command check `pip show cryptography`. Nếu thiếu → `pip install cryptography`. |

## 5. Dự kiến nỗi lực (Estimation)

| Metric | Value |
|--------|-------|
| **Estimated LOC** | ~1100 lines (300 SQL + 300 Python + 400 TypeScript + 100 markdown) |
| **Timeline** | 14 steps MSEW, ước tính 6-8 giờ Tier 2 thực thi + verify |
| **Files touched** | 18 NEW + 2 UPDATE (main.py + layout.tsx) |

## 6. Phụ thuộc giữa các Step
- Step 1-3 (3 migrations) độc lập nhau.
- Step 4 (vault) trước Step 5 (key_resolver) — key_resolver dùng vault.
- Step 5 (key_resolver) trước Step 7 (admin_api_keys) — router dùng resolver.
- Step 6 (usage_tracker) trước Step 7 (admin_api_keys) — usage endpoint dùng tracker.
- Step 7-8 (2 routers) trước Step 9 (mount).
- Step 10 (web proxy) trước Step 11-12 (UI pages).
- Step 13 (sidebar) sau Step 11-12.
- Step 14 (verify) cuối cùng.
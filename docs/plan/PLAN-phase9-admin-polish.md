# Kế hoạch Triển khai (PLAN): phase9-admin-polish

## 1. Mục tiêu (Objective)
- **Mô tả ngắn gọn:** Sprint A5 — Polish cho Admin Panel. Phase cuối cùng của admin panel MVP, focus vào 3 trọng tâm: audit log viewer + IP whitelist + documentation + wire Phase 8 stub.
- **Giá trị cốt lõi:**
  1. Admin có thể audit lại mọi mutation (filter + JSON diff + export).
  2. IP whitelist chặn brute force từ IP không tin cậy.
  3. Admin mới onboard có handbook tiếng Việt + English.
  4. 2 consumer thật sự dùng routing config (Phase 8 stub → fully wired).

## 2. Kiến trúc lựa chọn (Architecture)

### Pattern: Defense-in-depth + audit-readonly + doc-driven
```
[Admin UI] 
  → GET /api/admin/audit-logs?action=user.update&from_date=...
    → FastAPI query admin_audit_logs (read-only)
    → IP whitelist middleware check IP trước
    → Return table + pagination

[External request từ IP không whitelist]
  → FastAPI middleware reject 403 (defense layer #1)
  → Caddy IP whitelist (defense layer #2, Phase 9 doc)
  → Supabase RLS (defense layer #3, Phase 5 đã có)
```

### Cấu trúc file
```
apps/api/services/
  ip_whitelist.py               (NEW) - CIDR matching + middleware
  backup.py                     (NEW) - dump/restore config JSON

apps/api/routers/
  admin_audit.py                (NEW) - 3 endpoints (list, detail, export)

apps/api/modules/rag/
  embedder.py                   (UPDATE) - wire Phase 8 stub

apps/worker/tasks/
  script_generate.py            (UPDATE) - wire Phase 8 stub

apps/api/main.py                (UPDATE) - register IP whitelist middleware

apps/web/app/api/admin/audit-logs/
  route.ts                      (NEW) - GET list + export
  [id]/route.ts                 (NEW) - GET detail

apps/web/app/(admin)/admin/audit-logs/
  page.tsx                      (NEW) - table + filter + JSON diff modal

apps/web/app/(admin)/layout.tsx (UPDATE) - enable Audit Logs

docs/admin_handbook.md          (NEW) - song ngữ VI/EN
```

## 3. Lý do chọn & Các phương án đã loại trừ (Alternatives)

### Phương án A — Full Sprint A5 (audit + MFA + analytics + backup + handbook + IP) (ĐÃ LOẢI)
- **Lý do loại:** Phase 9 scope quá lớn (~2500 LOC). Tập trung 3 trọng tâm để Phase 10+ loại bỏ MFA + analytics.

### Phương án B — Supabase MFA TOTP setup Phase 9 (ĐÃ LOẢI)
- **Lý do loại:** Cần enable MFA trên Supabase project + customize JWT template. Phase 9 chỉ document setup steps, Phase 10+ implement.

### Phương án C — Dashboard analytics (cohort retention, revenue) Phase 9 (ĐÃ LOẢI)
- **Lý do loại:** Cần nhiều data warehouse setup. Phase 9 chỉ giữ dashboard Phase 5 stub.

### Phương án D — Backup/restore script chạy qua cron job (ĐÃ LOẢI một phần)
- **Lý do loại:** Phase 9 chỉ viết helper dump config → JSON file. Manual trigger. Cron job Phase 10+.

### Lý do chọn phương án hiện tại
- **Minimum viable polish:** 3 features admin MVP cần nhất.
- **Wire Phase 8 stub:** 2 consumer chưa fully wired.
- **Documentation:** Tiếng Việt ưu tiên (team VN).

## 4. Đánh giá rủi ro (Risk Assessment)

| # | Rủi ro | Mức | Giảm thiểu |
|---|--------|-----|------------|
| 1 | IP whitelist chặn nhầm admin IP (lockout) | **Cao** | Default = allow all (khi `ADMIN_ALLOWED_IPS` empty). Doc warning "test trước ở staging". |
| 2 | Middleware check IP qua `X-Forwarded-For` bị spoof | Trung bình | Phase 9 chỉ check `request.client.host` (FastAPI default — không trust proxy). Phase 10+ mới add Caddy proxy trust. |
| 3 | Audit log export CSV dump hàng triệu rows → OOM | Thấp | Cap 10k rows + date range filter required. |
| 4 | JSON diff viewer render diff 1MB JSON → UI freeze | Thấp | Modal max-height + scroll. Lazy render JSON tree. |
| 5 | Consumer wire `embedder` Phase 8 stub break Cohere client | Trung bình | Phase 9 chỉ wire khi provider != fallback. Test cả 2 case. |
| 6 | Doc handbook commit secret thật | Trung bình | Dùng placeholder `<your-key-here>` + template. |
| 7 | Backup script dump `encrypted_value` → leak | Thấp | Backup chỉ dump metadata (label, is_active, cost), KHÔNG dump value. |

## 5. Dự kiến nỗi lực (Estimation)

| Metric | Value |
|--------|-------|
| **Estimated LOC** | ~850 lines (200 Python services + 200 Python router + 100 Python wire + 200 TypeScript + 150 docs markdown) |
| **Timeline** | 11 steps MSEW, ước tính 4-6 giờ Tier 2 thực thi + verify |
| **Files touched** | 8 NEW + 4 UPDATE (2 consumer + main.py + layout.tsx) |

## 6. Phụ thuộc giữa các Step
- Step 1 (ip_whitelist) → Step 6 (main.py register middleware).
- Step 2 (backup) standalone → không phụ thuộc.
- Step 3 (audit router) standalone.
- Step 4-5 (wire 2 consumer) standalone.
- Step 6 (main.py) sau Step 1.
- Step 7 (web proxy) → Step 8 (UI page).
- Step 9 (sidebar) sau Step 8.
- Step 10 (docs) standalone.
- Step 11 (verify) cuối cùng.
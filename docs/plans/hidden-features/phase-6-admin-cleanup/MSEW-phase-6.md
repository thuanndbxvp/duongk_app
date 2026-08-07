# Phase 6 — MSEW

## Milestones

| Step | Action | Skills |
|---|---|---|
| 1 | Verify admin endpoints | `debugging` |
| 2 | Build admin layout với auth gate | `frontend-development`, `ui-styling` |
| 3 | Build `/admin/backup` + `<BackupManager>` | `frontend-development`, `ui-styling` |
| 4 | Build `/admin/traffic` + chart | `frontend-development`, `ui-styling` |
| 5 | Build `/admin/users` + table | `frontend-development`, `ui-styling` |
| 6 | Build `/admin/mfa` + setup | `frontend-development`, `ui-styling` |
| 7 | Identify 12 columns to cleanup | `code-review`, `debugging` |
| 8 | Write migration SQL | `database-admin` |
| 9 | Update ORM models | `backend-development` |
| 10 | Tests: admin + migration | `testing-protocol` |
| 11 | Review | `code-review` |

## Skills routing

| Task | Primary | Secondary |
|---|---|---|
| Auth gate | `frontend-development` | — |
| Components | `frontend-development` | `ui-styling` |
| Charts | `frontend-development` | `ui-styling` |
| DB migration | `database-admin` | `backend-development` |
| Tests | `testing-protocol` | — |

## Evidence

```bash
# Admin endpoints
curl -X GET "http://localhost:8000/api/admin/backup" -H "Authorization: Bearer ${ADMIN_TOKEN}"
curl -X GET "http://localhost:8000/api/admin/traffic" -H "Authorization: Bearer ${ADMIN_TOKEN}"
curl -X GET "http://localhost:8000/api/admin/users" -H "Authorization: Bearer ${ADMIN_TOKEN}"
curl -X POST "http://localhost:8000/api/admin/mfa" -H "Authorization: Bearer ${TOKEN}"

# Auth gate
curl -X GET "http://localhost:8000/api/admin/users" -H "Authorization: Bearer ${USER_TOKEN}"
# Expected: 403 Forbidden

# Migration
psql -d appdk -f supabase/migrations/20260808-drop-unused-columns.sql
# Verify: columns dropped

pytest tests/web/components/admin/ -v
pytest tests/api/test_admin_endpoints.py -v
```

## Warnings

### 🟡 Gotcha 1: Auth gate phải server-side

Nếu chỉ client-side check → user có thể bypass bằng cách tắt JS. Auth gate phải ở server component hoặc middleware.

**Fix**: Tier 2 dùng `layout.tsx` server component check `user.role === 'admin'`. Redirect non-admin.

### 🟡 Gotcha 2: Backup file size

Backup JSON có thể lớn (10MB+). Download không dùng blob stream → memory issue.

**Fix**: Tier 2 dùng `Content-Disposition: attachment` + streaming response.

### 🟡 Gotcha 3: Chart library

Frontend chưa có chart library. Tier 2 cần chọn:
- Chart.js (lightweight, ~30KB)
- Recharts (React-friendly, ~100KB)
- D3 (powerful but heavy)

**Fix**: Tier 2 chọn Chart.js. Add to deps nếu approved.

### 🟡 Gotcha 4: Drop column = data loss

Một khi drop column, data mất vĩnh viễn. Phải backup trước.

**Fix**: Migration chạy local → verify → backup DB → run trên staging → verify → production.

### 🟡 Gotcha 5: MFA QR code generation

Enroll MFA trả về QR code (data URL). Hiển thị bằng `<img src={dataUrl}>`.

**Fix**: Verify backend returns data URL (không phải external URL).

## Performance budget

- Step 1: 1 giờ
- Step 2: 2 giờ
- Step 3-6: 8 giờ (4 pages × 2 giờ)
- Step 7-9: 4 giờ (DB cleanup)
- Step 10-11: 4 giờ
- Total: ~19 giờ (= 3 ngày part-time)

## Exit gates

- [ ] All tests pass
- [ ] Coverage ≥80%
- [ ] LoC delta +400/-50
- [ ] DB migration applied + verified
- [ ] Tier 1 sign-off
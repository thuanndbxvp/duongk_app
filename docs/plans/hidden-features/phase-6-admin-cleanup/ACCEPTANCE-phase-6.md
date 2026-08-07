# Phase 6 — Acceptance Criteria

## A. Admin Pages

### A.1 — Layout + auth

- [ ] `/admin/*` route group với layout
- [ ] Auth gate: non-admin → redirect /dashboard
- [ ] Sidebar navigation
- [ ] User info in header

### A.2 — Backup

- [ ] `/admin/backup` exists
- [ ] Download backup button → GET /api/admin/backup
- [ ] Restore from file → POST /api/admin/backup
- [ ] Last backup timestamp shown
- [ ] Loading states
- [ ] Error handling

### A.3 — Traffic

- [ ] `/admin/traffic` exists
- [ ] Chart requests/day
- [ ] Top endpoints list
- [ ] Error rate gauge
- [ ] Active users count
- [ ] Date range selector (optional)

### A.4 — Users

- [ ] `/admin/users` exists
- [ ] User table với pagination
- [ ] Filter by status
- [ ] Click user → /admin/users/[id]
- [ ] User detail với stats

### A.5 — MFA

- [ ] `/admin/mfa` exists (user-facing, ngoài `/admin` group nếu cần)
- [ ] Show MFA status
- [ ] Enroll button → POST /api/admin/mfa → QR + backup codes
- [ ] Disable button với confirm

## B. Database cleanup

### B.1 — Decision matrix

| Column | Decision | Reason |
|---|---|---|
| `voice_profiles.pitch` | DROP | No UI, no business |
| `voice_profiles.tone` | DROP | No UI |
| `voice_profiles.speed` | KEEP+UI | UI will add in P3+ |
| `scripts.last_token_count` | DROP | Debug only |
| `projects.archived_at` | KEEP | UI planned |
| `projects.deleted_at` | DROP | Use soft-delete flag |
| ... 6 more | ☐ | ☐ |

### B.2 — Migration

- [ ] SQL file với DROP statements
- [ ] ORM models updated (remove columns)
- [ ] Tests updated (nếu reference)
- [ ] Migration applied locally + CI

## C. Tests

- [ ] Admin component tests
- [ ] Auth gate tests (non-admin denied)
- [ ] Admin endpoint integration tests
- [ ] Migration test (apply + rollback)

## D. Final

- [ ] Tests pass ≥80%
- [ ] Coverage ≥80%
- [ ] LoC delta: +400 / -50 (drops reduce)
- [ ] DB schema clean
- [ ] Tier 1 review

## Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _Tier 2_ | ____ | ☐ |
| Reviewer | _Tier 1_ | ____ | ☐ |
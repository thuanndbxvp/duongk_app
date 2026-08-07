# Phase 6 — Context & Background

## 1. Why this phase exists

Admin tools are **operational** — backup, traffic monitoring, user management. Without UI, admin phải dùng:
- Database GUI trực tiếp (Postico, pgAdmin) → risky
- curl commands → tedious
- Manual metrics via Prometheus → not actionable

DB cleanup = remove technical debt. ~12 columns không có UI = bloat ORM models, confuse developers.

## 2. Background: Admin role

`users.role` enum: `user | admin`. Hiện không có UI để phân quyền (tier-1 manual via DB).

## 3. Background: Backup format

`/api/admin/backup` returns JSON:
```json
{
  "version": "2026-08-07",
  "routing_config": {...},
  "provider_configs": {...},
  "feature_flags": {...},
  "templates": [...]
}
```

Restore ghi đè lên config hiện tại → confirm dialog required.

## 4. Background: Traffic data

`/api/admin/traffic` returns Prometheus-derived metrics:
```json
{
  "requests_per_day": [
    { "date": "2026-08-01", "count": 1234 },
    ...
  ],
  "top_endpoints": [
    { "path": "/api/projects", "count": 5000, "p95_ms": 120 },
    ...
  ],
  "error_rate": 0.02,
  "active_users": 234
}
```

## 5. Background: DB columns to clean

Tier 1 audit (sampling) found these unused columns:
- `voice_profiles.pitch` — never written
- `voice_profiles.tone` — never written
- `voice_profiles.speed` — written but no UI display
- `scripts.last_token_count` — debug only
- `projects.archived_at` — written but no UI
- `projects.deleted_at` — soft-delete not implemented
- 6 more (Tier 2 to identify during execution)

## 6. What is NOT in this phase

- WebSocket-based real-time traffic
- Audit log viewer
- Feature flag UI
- Email/SMS notification settings

## 7. References

- `apps/api/routers/admin.py` (existing endpoints)
- `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` §3.1.F, §4.B
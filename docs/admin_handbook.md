# Admin Panel Handbook — AppDK
> Cập nhật: 2026-08-06 · Phiên bản: 1.0 · Tác giả: Admin Team

## Giới thiệu / Introduction

Admin Panel là công cụ quản trị hệ thống AppDK, cho phép admin:
- Quản lý users (CRUD, ban, soft-delete, impersonate).
- Điều chỉnh credits (adjust + ledger + export).
- Quản lý API keys providers (OpenAI, Cohere, R2, Modal, ...) với encryption.
- Cấu hình routing 8 nghiệp vụ (transcript, TTS, embedding, ...) với hot-reload.
- Xem audit log + IP whitelist.

The Admin Panel manages AppDK system, allowing admins to manage users, credits, API keys, service routing, and audit logs.

## Truy cập / Access

1. **URL:** `https://app.example.com/admin`
2. **Yêu cầu / Requirements:**
   - User có `role = admin` hoặc `super_admin` trong bảng `users`.
   - IP phải thuộc `ADMIN_ALLOWED_IPS` (CIDR list, comma-separated).
   - 2FA (Phase 10+, hiện tại chỉ cần password).

## Cấu trúc Sidebar / Sidebar Structure

| Menu | Mục đích | Phase |
|------|----------|-------|
| Dashboard | Tổng quan hệ thống (4 stat cards) | 5 |
| Users | List, search, filter, detail, adjust credit, ban, impersonate | 6 |
| Credits | Ledger toàn hệ thống + stats + export CSV | 6 |
| Pricing | CRUD credit_pricing (per job_type) | 6 |
| API Keys | CRUD providers + encrypt + rotate + test | 7 |
| Routing | 8 features × primary + fallback + cost | 8 |
| Alerts | List unresolved budget/error alerts | 7 |
| Audit Logs | Full-text search + JSON diff + export | 9 |

## Tasks thường gặp / Common Tasks

### 1. Adjust credit cho user / Adjust User Credit
```
1. Vào /admin/users → search email user → click row
2. Tab "Profile" → thấy credit balance hiện tại
3. Form "Adjust Credit" → nhập delta (+/-) + lý do (≥ 10 ký tự)
4. Click "Adjust Credit" → balance update + audit log ghi
```

### 2. Rotate API key / Rotate API Key
```
1. Vào /admin/api-keys → tìm provider → click "Rotate"
2. Nhập new value → confirm
3. Key cũ archive (giữ 7 ngày), key mới active
4. Worker tự động reload cache trong < 60s
```

### 3. Đổi primary provider cho TTS / Change TTS Provider
```
1. Vào /admin/routing → tìm card "Text-to-Speech"
2. Dropdown "Primary" → chọn provider mới
3. Click "Save + Hot Reload"
4. Job TTS mới dùng provider mới trong < 60s (worker pick up qua Redis pub/sub)
```

### 4. Xem audit log / View Audit Logs
```
1. Vào /admin/audit-logs → filter theo admin_email / action / target
2. Click row → modal hiển thị JSON diff (before vs after)
3. Click "Export CSV" → download file (date range max 30 ngày)
```

## Security / Bảo mật

- **Audit log:** Mọi mutation đều ghi vào `admin_audit_logs`. Field sensitive (`*key*`, `*secret*`, `*token*`, `*password*`) tự động mask thành `***`.
- **IP Whitelist:** Set env `ADMIN_ALLOWED_IPS=192.168.1.0/24,10.0.0.0/8`. Empty = allow all (DEV ONLY).
- **Encryption:** API key values lưu encrypted bằng Fernet (AES-128-CBC + HMAC). Key từ env `ENCRYPTION_KEY`.
- **Rate limit:** Áp dụng ở Caddy (recommended) hoặc Cloudflare.

## Troubleshooting

### Lỗi 403 khi truy cập /admin
- Check role user trong DB: `SELECT email, role FROM users WHERE email = '<your-email>';`
- Nếu `role = user` → update thành `admin` hoặc `super_admin`.

### API key test fail / API Key Test Failed
- Check key còn valid không (provider dashboard).
- Check budget có bị exhausted không (`/admin/api-keys` → cột `Cost (mo)`).
- Check rate limit (provider dashboard).

### Routing config thay đổi không có hiệu lực
- Click "Reload" trên card `/admin/routing`.
- Hoặc đợi 60s (worker polling fallback).
- Check worker logs: `[config_watcher] Routing config updated for feature: <feature>`.

### Audit log ghi sai before/after
- Phase 5 audit mask đã sẵn. Kiểm tra `_SENSITIVE_KEYS` regex ở `apps/api/services/audit.py`.

## Phase Roadmap (đã xong + sắp tới)

| Phase | Tính năng | Status |
|-------|-----------|--------|
| 5 | Foundation (RBAC, audit log, RPCs) | ✅ Done |
| 6 | User & Credit Management | ✅ Plan |
| 7 | API Keys (encryption + rotate) | ✅ Plan |
| 8 | Service Routing (hot-reload) | ✅ Plan |
| 9 | Polish (audit log viewer, IP whitelist, docs) | ✅ Plan |
| 10+ | 2FA TOTP, analytics, backup cron, ffmpeg dispatcher | 📋 Future |

## Liên hệ / Contact

- Slack: #admin-panel channel
- Email: admin@appdk.example.com
- On-call: PagerDuty rotation

---

> **Lưu ý quan trọng / Important:**
> - KHÔNG commit secret thật vào repo. Dùng env vars.
> - KHÔNG share admin JWT. Mỗi admin có session riêng.
> - KHÔNG disable audit log. Mọi mutation PHẢI được log.
> - DO NOT commit real secrets. Use env vars.
> - DO NOT share admin JWT. Each admin has own session.
> - DO NOT disable audit log. All mutations MUST be logged.
# Tiêu chí Nghiệm thu (ACCEPTANCE): phase9-admin-polish

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### File 1: `apps/api/services/ip_whitelist.py` (NEW)
- [ ] Có class `IPWhitelistMiddleware(BaseHTTPMiddleware)`.
- [ ] Middleware chỉ check paths bắt đầu `/api/admin/`.
- [ ] Parse env `ADMIN_ALLOWED_IPS` (comma-separated CIDR).
- [ ] Empty env = allow all (dev mode).
- [ ] Non-matching IP → 403 JSON response.
- [ ] Có helper `is_ip_allowed(client_ip) → bool`.

### File 2: `apps/api/services/backup.py` (NEW)
- [ ] Có hàm `dump_config() → dict` (3 tables: `service_routing_config`, `credit_pricing`, `api_provider_keys.metadata`).
- [ ] **KHÔNG dump `encrypted_value`** (security).
- [ ] Có hàm `restore_config(config_data, dry_run=True) → dict`.
- [ ] Default `dry_run=True` (chỉ report, không apply).
- [ ] Có hàm `export_to_file(filepath) → str`.

### File 3: `apps/api/routers/admin_audit.py` (NEW)
- [ ] Có 3 endpoints:
  - `GET /api/admin/audit-logs` (filter: admin_email, action, target_type, target_id, from_date, to_date, page, limit)
  - `GET /api/admin/audit-logs/{log_id}` (chi tiết 1 log + before/after JSON)
  - `GET /api/admin/audit-logs/export/csv` (date range required, max 30 days, cap 10k rows)
- [ ] Mọi endpoint có `Depends(require_admin)`.
- [ ] Export trả CSV với `Content-Disposition: attachment`.

### File 4: `apps/api/modules/rag/embedder.py` (UPDATE — wire Phase 8)
- [ ] Method `embed_texts` chọn provider từ `_select_embedding_provider()` (Phase 8 đã có helper).
- [ ] Fallback về `cohere` (vi/zh) hoặc `openai` (en) nếu routing fail.

### File 5: `apps/worker/tasks/script_generate.py` (UPDATE — wire Phase 8)
- [ ] Function `generate_script` chọn provider từ `select_llm_provider()` (Phase 8 đã có helper).
- [ ] Fallback về `openai` nếu routing fail.

### File 6: `apps/api/main.py` (UPDATE)
- [ ] Import `IPWhitelistMiddleware` + `admin_audit_router`.
- [ ] `app.add_middleware(IPWhitelistMiddleware)` (sau khi tạo app).
- [ ] `app.include_router(admin_audit_router)`.
- [ ] Admin audit route count ≥ 3.

### File 7-9: Web proxy routes (3 NEW)
- [ ] `apps/web/app/api/admin/audit-logs/route.ts` (GET).
- [ ] `apps/web/app/api/admin/audit-logs/[id]/route.ts` (GET).
- [ ] `apps/web/app/api/admin/audit-logs/export/csv/route.ts` (GET, return blob).
- [ ] TS compile 0 errors.

### File 10: `apps/web/app/(admin)/admin/audit-logs/page.tsx` (NEW)
- [ ] File tồn tại, TS compile 0 errors.
- [ ] Filter bar (admin_email, action, target_type).
- [ ] Export CSV button (date range).
- [ ] Table với 5 columns (Admin, Action, Target, Reason, Date).
- [ ] Click row → modal JSON diff (Before vs After).
- [ ] Modal có max-height + scroll.
- [ ] Pagination (Previous/Next).

### File 11: `apps/web/app/(admin)/layout.tsx` (UPDATE)
- [ ] `Audit Logs.enabled = true` (line 15).
- [ ] 7 mục còn lại KHÔNG đổi.

### File 12: `docs/admin_handbook.md` (NEW)
- [ ] File tồn tại.
- [ ] Song ngữ VI/EN.
- [ ] Có 5 sections: Giới thiệu, Truy cập, Sidebar structure, Common tasks, Security, Troubleshooting, Phase Roadmap.
- [ ] KHÔNG commit secret thật (placeholder `<your-key-here>`).

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

- **Security:**
  - IP whitelist mặc định allow all (dev), CIDR ở prod.
  - Audit log read-only (no delete endpoint).
  - Backup dump KHÔNG bao gồm `encrypted_value`.
  - Handbook KHÔNG có secret thật.
- **Backward compatibility:**
  - 0 regression trên Phase 5/6/7/8 endpoints.
  - 0 regression trên user-facing routes.
  - 2 consumer wire (`embedder`, `script_generate`) vẫn fallback env var.
- **No new dependency:**
  - `ipaddress` (stdlib).
- **Performance:**
  - Audit log export CSV cap 10k rows + 30 days max.
  - IP whitelist check O(N) networks per request (N thường ≤ 5 — OK).

## 3. Mục tiêu Test Coverage
- **Backend:** Phase 9 KHÔNG thêm unit test mới. Verify qua smoke test (10 file import) + IP whitelist manual test.
- **Frontend:** TS compile 0 errors.

## 4. Các bước Manual Verification (Windows PowerShell)

### Bước 1: Verify Python imports (6 file)
```powershell
cd d:\appDK
python -c "from apps.api.main import app; print('main OK')"
python -c "from apps.api.services.ip_whitelist import IPWhitelistMiddleware, is_ip_allowed; print('ip_whitelist OK')"
python -c "from apps.api.services.backup import dump_config, restore_config; print('backup OK')"
python -c "from apps.api.routers.admin_audit import router; print('admin_audit OK')"
python -c "from apps.api.modules.rag.embedder import Embedder; print('embedder wired OK')"
python -c "from apps.worker.tasks.script_generate import generate_script; print('script_generate wired OK')"
```
**Expected:** 6 dòng "OK".

### Bước 2: Verify admin audit routes
```powershell
python -c "from apps.api.main import app; routes = sorted([r.path for r in app.routes if hasattr(r, 'path') and '/admin' in r.path and 'audit' in r.path]); print(len(routes), 'audit routes'); [print(r) for r in routes]"
```
**Expected:** ≥ 3 routes.

### Bước 3: Run existing test (no regression)
```powershell
cd d:\appDK\apps\api
python -m pytest test_credit_manager.py -v
```
**Expected:** 2 tests PASSED.

### Bước 4: TS compile
```powershell
cd d:\appDK\apps\web
pnpm exec tsc --noEmit
```
**Expected:** 0 errors.

### Bước 5: Verify UI page + handbook exists
```powershell
Test-Path "app\(admin)\admin\audit-logs\page.tsx"
Test-Path "..\docs\admin_handbook.md"
```
**Expected:** 2 True.

### Bước 6: Verify sidebar update
```powershell
Get-Content "apps\web\app\(admin)\layout.tsx" | Select-String "Audit Logs.*enabled.*true"
```
**Expected:** 1 match.

### Bước 7: IP whitelist test (dev mode = allow all)
```powershell
$env:ADMIN_ALLOWED_IPS = ""
python -c "from apps.api.services.ip_whitelist import is_ip_allowed; assert is_ip_allowed('1.2.3.4') == True; assert is_ip_allowed('192.168.99.99') == True; print('dev mode OK')"
```
**Expected:** `dev mode OK`.

### Bước 8: IP whitelist test (with CIDR)
```powershell
$env:ADMIN_ALLOWED_IPS = "192.168.1.0/24,10.0.0.0/8"
python -c "from apps.api.services.ip_whitelist import is_ip_allowed; assert is_ip_allowed('192.168.1.5') == True; assert is_ip_allowed('10.0.0.1') == True; assert is_ip_allowed('172.16.0.1') == False; print('CIDR test OK')"
```
**Expected:** `CIDR test OK`.

### Bước 9: Visual smoke test (optional, cần admin role)
```powershell
pnpm dev
```
Mở browser với admin user:
- `/admin/audit-logs` → table với filter bar.
- Click row → modal JSON diff.
- Click "Export CSV" → date range prompt → download file.
- Sidebar: "Audit Logs" không còn badge "Soon".

### Bước 10: Verify handbook
```powershell
Get-Content "..\docs\admin_handbook.md" | Measure-Object -Line
```
**Expected:** ≥ 50 lines.

## 5. Định nghĩa "Hoàn thành Phase"
Tất cả 11 MSEW step phải PASS verify command của riêng nó, VÀ 10 manual verification ở trên pass.

Khi pass → Tier 2 ghi báo cáo vào file `docs/audit/AUDIT-REPORT-phase9-admin-polish.md` và thông báo cho Planner.

## 6. Lưu ý cho Phase sau (Phase 10+)
Sprint A5 đã hoàn thành scope tối thiểu. Còn lại để Phase 10+:
- **MFA TOTP** — enable trên Supabase project + customize JWT template + middleware check.
- **Advanced dashboard analytics** — cohort retention, revenue chart (cần data warehouse).
- **Backup cron** — schedule job dump config hàng tuần → S3.
- **ffmpeg_render dispatcher** (`apps/worker/services/render_dispatcher.py`) — gọi Modal.render_video.
- **thumbnail_vision consumer** — wire Phase 8 routing.
- **Caddy IP whitelist** — config rule giới hạn path `/admin/*` theo IP (defense in depth).
- **2FA enforcement cho super_admin** — middleware check `auth.mfa_verified`.
- **Audit log retention** — archive logs > 1 năm sang cold storage.

## 7. Admin Panel MVP — Hoàn thành

Sau Phase 9, Admin Panel MVP hoàn thành 100% theo `docs/plans/admin_panel_plan.md` (Phase 2):

| Sprint | Status | Tính năng chính |
|--------|--------|-----------------|
| A1 | ✅ Done | Foundation (audit, RBAC, schema, layout shell, dashboard) |
| A2 | ✅ Plan → thực thi | User & Credit Management (13 endpoint + 3 UI page) |
| A3 | ✅ Plan → thực thi | API Keys (encrypted + rotate + test + alerts) |
| A4 | ✅ Plan → thực thi | Service Routing (hot-reload 8 features qua Redis) |
| A5 | ✅ Plan → thực thi | Polish (audit log viewer + IP whitelist + docs) |

**Total admin endpoints: 32** (9 users + 4 credit + 2 pricing + 7 api-keys + 2 alerts + 5 routing + 3 audit log).

**Total admin UI pages: 7** (Dashboard + Users + Credits + API Keys + Alerts + Routing + Audit Logs).

**Total admin services: 5** (audit + key_resolver + routing + cache + ip_whitelist).

Đây là kết thúc **Admin Panel MVP** theo plan. Sau này cần mở rộng: MFA, analytics, backup cron, ffmpeg dispatcher — nhưng đó là Phase 10+ (ngoài scope plan).
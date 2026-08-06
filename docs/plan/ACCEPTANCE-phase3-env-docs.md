# Tiêu chí Nghiệm thu (ACCEPTANCE): phase3-env-docs

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### File 1: `.env.example` (UPDATE)
- [ ] File có **30** dòng match pattern `^[A-Z_]+=` (19 cũ + 11 mới).
- [ ] Có 11 biến mới được thêm:
  - 7 biến R2 (`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT`, `R2_BUCKET_UPLOADS`, `R2_BUCKET_RENDERS`, `R2_BUCKET_CACHE`, `R2_PUBLIC_CDN`)
  - 2 biến Modal (`MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`)
  - 1 biến Supadata (`SUPADATA_API_KEY`)
  - 1 biến SerpAPI (`SERPAPI_KEY`)
  - 1 biến Stali (`STALI_API_KEY`, `STALI_BASE_URL`)
  - 1 biến Python (`PYTHONUNBUFFERED`)
- [ ] **KHÔNG** có pattern secret thật (`sk-...`, `eyJ...`, R2 key dài > 20 char thật).
- [ ] File có comment nhóm (`# === Supabase ===`, etc.).

### File 2: `docs/SETUP.md` (NEW)
- [ ] File tồn tại, ≥ 60 dòng.
- [ ] Có 5 section chính:
  1. Clone & Install
  2. Tạo `.env` từ template
  3. Verify env (link tới `scripts/check-env.py`)
  4. Apply DB migrations
  5. Start services
- [ ] Có section Troubleshooting ở cuối (≥ 3 lỗi thường gặp).

### File 3: `docs/ENV-VARS.md` (NEW)
- [ ] File tồn tại, ≥ 80 dòng.
- [ ] Có bảng cho 6 nhóm biến: Supabase, Redis, R2, Modal, LLM, External APIs.
- [ ] Có section "Optional / unused" ghi rõ `STALI_*` unused.
- [ ] Có section "Admin panel" ghi `ADMIN_ALLOWED_IPS`.

### File 4: `scripts/check-env.py` (NEW)
- [ ] File tồn tại, chạy được bằng `python scripts/check-env.py`.
- [ ] In bảng ≥ 30 dòng (header + separator + 30 biến + footer).
- [ ] Mask secret values (hiện `sk-***` thay vì full key).
- [ ] Phân biệt `[OK]` / `[MISSING]` / `[OPTIONAL]`.
- [ ] Return exit code 0 nếu đủ required, 1 nếu thiếu.

### File 5: `apps/web/README.md` (UPDATE)
- [ ] Phần Next.js default KHÔNG bị mất.
- [ ] Có section "Environment Variables" (≥ 1 mention).
- [ ] Có link tới `docs/ENV-VARS.md` và `docs/SETUP.md`.

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

- **Security:**
  - `.env.example` không chứa secret thật.
  - `.env` local KHÔNG bị đụng.
  - `check-env.py` mask secret khi in ra.
- **Consistency:** Dùng cùng format markdown heading (# ## ###) và table cho cả 3 file docs.
- **Single source of truth:** `ENV-VARS.md` là reference duy nhất cho biến.
- **CI-friendly:** `check-env.py` return exit code chuẩn (0/1) để CI check.

## 3. Mục tiêu Test Coverage
- **N/A** — Phase 3 là devops/docs, không có unit test.

## 4. Các bước Manual Verification (Windows PowerShell)

### Bước 1: Verify `.env.example`
```powershell
cd d:\appDK
$count = (Get-Content .env.example | Select-String "^[A-Z_]+=" | Measure-Object -Line).Lines
Write-Host "Variables: $count (expected 30)"

# Check không có secret leak
$leak = Select-String -Path .env.example -Pattern "sk-[a-zA-Z]|eyJ[a-zA-Z0-9_-]{30,}|PLACEHOLDER_R2_(?!.*PLACEHOLDER)"
Write-Host "Potential leaks: $($leak.Count)"
```
**Expected:** Variables = 30, leaks = 0.

### Bước 2: Verify 3 file mới tồn tại
```powershell
Test-Path docs\SETUP.md
Test-Path docs\ENV-VARS.md
Test-Path scripts\check-env.py
```
**Expected:** 3 lần True.

### Bước 3: Chạy check-env.py
```powershell
cd d:\appDK
python scripts\check-env.py
```
**Expected:**
- Bảng ≥ 30 dòng.
- Mỗi dòng có format: `TÊN_BIẾN    [OK|MISSING|OPTIONAL]   Mô tả`.
- Secret keys hiện `sk-***` hoặc `eyJ***`.

### Bước 4: Verify web README
```powershell
Get-Content apps\web\README.md | Select-String "Environment Variables|ENV-VARS"
```
**Expected:** ≥ 2 matches.

### Bước 5: Verify `.env` không bị đụng
```powershell
git status .env
```
**Expected:** `.env` KHÔNG có trong `modified`/`untracked` (Tier 2 không commit nó).

## 5. Định nghĩa "Hoàn thành Phase"
Tất cả 6 MSEW step phải PASS verify command của riêng nó, VÀ 5 manual verification ở trên pass.

Khi pass → Tier 2 ghi báo cáo vào file `docs/audit/AUDIT-REPORT-phase3-env-docs.md` (theo template `AUDIT-REPORT.template.md`) và thông báo cho Planner.
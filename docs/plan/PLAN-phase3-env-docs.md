# Kế hoạch Triển khai (PLAN): phase3-env-docs

## 1. Mục tiêu (Objective)
- **Mô tả ngắn gọn:** Hoàn thiện tài liệu + script dev ops giúp dev mới setup dự án trong 5 phút.
- **Giá trị cốt lõi:**
  1. Dev mới clone repo → chạy `python scripts/check-env.py` → biết ngay thiếu gì.
  2. `.env.example` đầy đủ 30 biến (19 cũ + 11 mới), tier 2 Phase sau không bị "missing key" surprise.
  3. `docs/ENV-VARS.md` là reference duy nhất — không phải đọc code để biết biến nào bắt buộc.

## 2. Kiến trúc lựa chọn (Architecture)

### Pattern: Template-driven documentation
```
.env.example (1 file UPDATED)
  └─ 30 biến, có comment nhóm (Supabase / Redis / R2 / Modal / LLM / etc.)

docs/SETUP.md (1 file NEW)
  └─ Hướng dẫn 5 bước: clone → install → copy env → start Docker → verify

docs/ENV-VARS.md (1 file NEW)
  └─ Bảng từng biến: Tên | Mô tả | Bắt buộc? | Nguồn lấy

scripts/check-env.py (1 file NEW)
  └─ Load .env, check từng biến, in bảng kết quả

apps/web/README.md (1 file UPDATED, append only)
  └─ Section "Environment Variables" — pointer tới docs/ENV-VARS.md
```

### Không có code change
- Phase 3 là devops/docs. Không thêm logic, không đổi file Python/TypeScript ngoài script check-env.py.

## 3. Lý do chọn & Các phương án đã loại trừ (Alternatives)

### Phương án A — Tạo root `README.md` thay vì append vào `apps/web/README.md` (ĐÃ LOẠI)
- **Lý do loại:** Repo không có convention root README. Tier 2 chỉ đang làm devops, không phải marketing. Append vào `apps/web/README.md` (Next.js default) là đủ.

### Phương án B — Dùng `direnv` / `dotenv-cli` thay vì `python-dotenv` (ĐÃ LOẠI)
- **Lý do loại:** Repo đã có `python-dotenv` (xem `apps/api/main.py:8`). Thêm tool mới → friction.

### Phương án C — `check-env.py` dùng `pydantic-settings` validation (ĐÃ LOẠI)
- **Lý do loại:** Pydantic chỉ dùng ở FastAPI. Script check-env nên độc lập với framework → dùng `os.getenv` đơn giản.

### Phương án D — Merge `SETUP.md` và `ENV-VARS.md` thành 1 file (ĐÃ LOẢI)
- **Lý do loại:** SETUP = hướng dẫn tổng quát (5 bước). ENV-VARS = reference tra cứu (bảng). Audience khác nhau.

### Lý do chọn phương án hiện tại
- **Single responsibility:** Mỗi file 1 mục đích rõ ràng.
- **Zero dependency:** Không thêm package, dùng `os.getenv`.
- **CI-friendly:** `check-env.py` có thể gọi từ CI script sau (Phase 4 sẽ dùng).

## 4. Đánh giá rủi ro (Risk Assessment)

| # | Rủi ro | Mức | Giảm thiểu |
|---|--------|-----|------------|
| 1 | Lỡ commit secret thật vào `.env.example` | **Cao** | Step 1 chỉ dùng `...` hoặc `PLACEHOLDER_*`. Step 6 verify bằng `git diff .env.example` không có pattern JWT/SK- prefix. |
| 2 | `check-env.py` import dotenv sai → fail | Thấp | Dùng `os.getenv` thuần (không cần dotenv). Env đã được load bởi `load_dotenv()` ở FastAPI startup — nhưng check-env chạy standalone nên dùng `os.environ`. |
| 3 | `.env.example` syntax lỗi (thiếu newline cuối) | Thấp | PowerShell `Get-Content` + visual check. |
| 4 | `STALI_API_KEY` có trong `.env` nhưng không có consumer trong code → tier 2 nhầm tưởng bắt buộc | Trung bình | Step 3 (ENV-VARS.md) mark `STALI_*` là "Optional — unused". |
| 5 | `apps/web/README.md` Next.js default có thể bị Next.js CLI overwrite nếu regenerate | Thấp | Phase 3 chỉ append 1 section, không chạy `create-next-app` lại. |

## 5. Dự kiến nỗi lực (Estimation)

| Metric | Value |
|--------|-------|
| **Estimated LOC** | ~250 lines (50 markdown + 30 .env.example + 80 script Python + 30 web README) |
| **Timeline** | 6 steps MSEW, ước tính 1-2 giờ Tier 2 thực thi |
| **Files touched** | 5 files (1 UPDATE .env.example + 1 UPDATE web README + 3 NEW: SETUP.md, ENV-VARS.md, check-env.py) |

## 6. Phụ thuộc giữa các Step
- Step 1 (.env.example) phải xong trước Step 4 (check-env.py dùng cùng danh sách biến).
- Step 2 (SETUP.md) và Step 3 (ENV-VARS.md) độc lập nhau.
- Step 5 (web README) độc lập.
- Step 6 (verify) cuối cùng.
# PHÂN TÍCH PIPELINE & UI - AppDK

**Ngày:** 2026-08-05
**Trạng thái UI:** Cơ bản - Thiếu nhiều màn hình nghiệp vụ quan trọng
**Trạng thái Backend:** 9 modules đã implement

---

## 1. TỔNG QUAN PIPELINE NGHIỆP VỤ

### A. User Journey (Người dùng cuối)

```
┌─────────────────────────────────────────────────────────────────────┐
│  END-TO-END PIPELINE                                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ① LOGIN/REGISTER ────▶ ② DASHBOARD ────▶ ③ NEW PROJECT            │
│      ❌ Thừng                                 ⚠️ Sơ sài              │
│  /login /register                    /projects/new                  │
│                                                                     │
│                              ▼                                      │
│  ④ NHẬP URL ──────────▶ ⑤ BACKEND XỬ LÝ (Celery + LLM)              │
│      YouTube                       module_1 → module_2a            │
│      Channel                       → analysis (14 outputs)         │
│                                     → RAG (embeddings)             │
│                                                                     │
│                              ▼                                      │
│  ⑥ WATCH PROGRESS ─────▶ ⑦ XEM KẾT QUẢ (Channel DNA/14 outputs)   │
│      /jobs/[id]   ❌ THIẾU             ❌ THIẾU                       │
│                                                                     │
│                              ▼                                      │
│  ⑧ CHỌN CHỦ ĐỀ ──────▶ ⑨ SINH SCRIPT                              │
│      /ideas      ❌ THIẾU       ⚠️ Chỉ có script editor            │
│                              /scripts/[id]                         │
│                                                                     │
│                              ▼                                      │
│  ⑩ SCENE BREAKDOWN ─────▶ ⑪ CHỈNH SỬA + EXPORT                    │
│      ❌ THIẾU               ❌ THIẾU                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. BACKEND ĐÃ CÓ (9 Modules)

| # | Module | API Routes | Tasks | Notes |
|---|--------|-----------|-------|-------|
| 1 | `module_1` | `/api/research/*` | Niche validate | ✅ |
| 2 | `module_2a` | `/api/channels/*` | Channel collection | ✅ |
| 3 | `transcript` | `/api/transcripts/*` | 3-tier transcript | ✅ |
| 4 | `analysis` | `/api/analysis/*` | 14 outputs | ✅ |
| 5 | `nlp` | `/api/nlp/*` | NLP analysis | ✅ |
| 6 | `llm` | `/api/llm/*` | LLM operations | ✅ |
| 7 | `rag` | `/api/rag/*` | RAG retrieval | ✅ |
| 8 | `script` | `/api/scripts/*` | Script generation | ✅ |
| 9 | `vision` | (internal) | Thumbnail | ✅ (Sprint 2) |

**Backend API endpoints rất phong phú. UI chỉ dùng ~10%.**

---

## 3. UI HIỆN TẠI - KIỂM KÊ

### ✅ CÓ

| Page | Route | Mục đích | Hoàn chỉnh? |
|------|-------|----------|-------------|
| Landing | `/` | Giới thiệu | ⚠️ Sơ sài |
| Login | `/login` | Đăng nhập | ✅ |
| Register | `/register` | Đăng ký | ✅ |
| Dashboard | `/dashboard` | Danh sách jobs | ⚠️ Thiếu credits badge |
| New Project | `/projects/new` | Nhập URL | ⚠️ Thiếu chọn job type |
| Job Progress | `/jobs/[id]` | Realtime progress | ✅ |
| Script Editor | `/scripts/[id]` | Xem/sửa script | ⚠️ readOnly, không lưu |

### ❌ THIẾU QUAN TRỌNG

| # | Thiếu gì | Tại sao quan trọng |
|---|----------|-------------------|
| 1 | **Niche Research Page** | Module 1 đã có - user chưa dùng được |
| 2 | **Channel Analysis Results** | 14 outputs đã tính - user không xem được |
| 3 | **Idea Selection Page** | HDBSCAN + Gap Score - user không thấy |
| 4 | **Channel Assistant List** | Sau khi collect phải chọn assistant |
| 5 | **Credit Purchase Page** | User hết credit không mua được |
| 6 | **Account Settings** | Đổi password, tier management |
| 7 | **Script Editor với Save** | Hiện tại textarea readOnly |
| 8 | **B-roll Picker** | Scene có suggestions - chưa có UI chọn |
| 9 | **Analytics Dashboard** | Credits usage chart, jobs stats |
| 10 | **Pricing Page** | User chọn tier (free/pro/enterprise) |

---

## 4. THIẾU KẾT NỐI NGHIỆP VỤ

### A. Job Types Đa Dạng (Backend có 8 loại)

UI hiện tại chỉ cho phép **1 loại**: `script_generate`. User không thể:
- 🔍 **Validate Niche** (Module 1) - 5 credits
- 📺 **Collect Channel** (Module 2a) - 10 credits
- 🧠 **Run Deep Analysis** (14 outputs) - 50 credits
- 💡 **Generate Ideas** (HDBSCAN) - 5 credits
- 🔎 **RAG Search** (chỉ retrieve) - 1 credit
- 🎬 **Scene Breakdown** (chỉ scenes) - 10 credits
- 📝 **Generate Script** - 30 credits (đang có)
- 🎨 **Thumbnail Analysis** (vision) - hidden

### B. Credit System Không Hiển Thị

Backend có CreditManager đầy đủ, nhưng:
- ❌ Dashboard không hiển thị credits còn lại
- ❌ Không có warning khi sắp hết
- ❌ Không có trang `/billing` để nạp thêm
- ❌ Không có transaction history UI

### C. Channel Assistant Workflow Bị Bỏ Qua

Backend flow chuẩn:
```
Collect Channel → Tạo Channel Assistant → Analyze Assistant → Script cho Assistant
```

UI hiện tại:
```
URL → Script trực tiếp (BỎ QUA assistant concept!)
```

→ User không có khái niệm "Channel DNA" hay "Assistant" trên UI.

---

## 5. SECURITY & RLS CHƯA ÁP DỤNG HOÀN TOÀN

✅ Backend có RLS (20 migrations)
⚠️ Frontend chưa enforce:
- Script Editor (`/scripts/[id]`) dùng `supabase` trực tiếp - bypass BFF
- Jobs page dùng `supabase` realtime - bypass BFF

**Lý do:** Thiếu `GET /api/scripts/[id]` proxy route trong BFF.

---

## 6. ĐỀ XUẤT CẢI THIỆN (Ưu tiên theo impact)

### 🔴 P0 - Phải có (Block nghiệp vụ chính)

```
1. /billing - Credit balance + transaction history
2. /assistants - Channel assistants list (phải có trước khi script)
3. /analysis/[assistant_id] - Xem 14 outputs
4. /ideas/[assistant_id] - Chọn ý tưởng từ HDBSCAN
```

### 🟡 P1 - UX improvements

```
5. /jobs/recent - Filter by status/type
6. /scripts/[id] - Edit + Save (không readOnly)
7. /account/settings - Profile management
8. /pricing - Tier comparison
```

### 🟢 P2 - Polish

```
9. /dashboard - Credit badge ở header
10. B-roll picker UI
11. Export PDF/DOCX
12. Analytics charts
```

---

## 7. MISSING API PROXY ROUTES

Để BFF hoàn chỉnh, cần thêm:

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/assistants` | List user's assistants |
| GET | `/api/assistants/[id]` | Get specific assistant |
| POST | `/api/assistants` | Create assistant |
| GET | `/api/analysis/[assistant_id]` | Get 14 outputs |
| GET | `/api/ideas/[assistant_id]` | Get HDBSCAN ideas |
| GET | `/api/scripts/[id]` | Get script (currently bypassed) |
| PATCH | `/api/scripts/[id]` | Save edited script |
| GET | `/api/credits/balance` | (đã có trong tasks) |
| GET | `/api/credits/transactions` | (đã có) |
| POST | `/api/credits/purchase` | Mock purchase |

---

## 8. KẾT LUẬN

**UI hiện tại = 20% nghiệp vụ thực tế.**

### Điểm mạnh:
- ✅ Login/Register works
- ✅ Realtime progress tracking tốt
- ✅ Script editor layout đẹp

### Điểm yếu nghiêm trọng:
- ❌ User không thấy "Channel Assistant" concept
- ❌ User không thấy 14 deep analysis outputs (giá trị lớn nhất)
- ❌ User không chọn được ideas trước khi generate script
- ❌ Không có credit UI (mặc dù backend charge)
- ❌ Script editor không save được
- ❌ Chỉ cho phép 1 job type duy nhất

### Cần thiết kế lại flow:

```
Login → Dashboard (credits visible)
        │
        ├── Validate Niche (nếu chưa có niche)
        ├── Collect Channel (URL)
        │     │
        │     ▼ (auto tạo assistant)
        │   Dashboard có Assistant mới
        │     │
        │     ├── Xem 14 Analysis Outputs
        │     ├── Xem Ideas (HDBSCAN)
        │     │     │
        │     │     ▼ (chọn 1 idea)
        │     │   Generate Script (anti-slop)
        │     │     │
        │     │     ▼
        │     │   Script Editor (editable, save)
        │     │     │
        │     │     ▼
        │     │   Breakdown Scenes (B-roll)
        │     │
        │     └── Account/Settings
        │
        └── Billing (credits, transactions)
```

UI hiện tại **THIẾU 80%** flows trên.

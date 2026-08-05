# QUYẾT ĐỊNH CỦA PLANNER - Sprint 3 RAG Retrieval

**Task:** Sprint 3 - RAG Retrieval (MMR)
**Date:** 2026-08-05
**Prepared by:** Tầng 1 (Planner)

---

## Tiếp nhận AUDIT-REPORT

Tôi đã đọc AUDIT-REPORT từ Tầng 2 và xác nhận:

### ✅ Lý do 1: `EmbeddingRouter` - **ĐÚNG**

Tầng 2 đã đúng khi phát hiện `EmbeddingRouter` không tồn tại ở path mà tôi chỉ định.

**Thực tế:**
- File **ĐÃ TỒN TẠI** tại: `apps/api/modules/rag/embedding_router.py`
- Path trong bản vẽ **SAI**: `apps/worker/services/embedding_router.py`

**Đã fix:**
- ✅ Cập nhật `SKILL-ROUTING-sprint3-rag-retrieval.md` - chỉ định đúng path
- ✅ Cập nhật `MSEW-sprint3-rag-retrieval.md` - sửa import statement

### ✅ Lý do 2: Dependencies - **ĐÚNG**

Tầng 2 đúng khi phát hiện `requirements.txt` thiếu pytest packages.

**Thực tế:**
- File `requirements.txt` hiện tại không có pytest, pytest-asyncio, pytest-cov
- Lệnh test trong MSEW sẽ fail

**Đã fix:**
- ✅ Thêm section "Dependencies Cần Cài" vào `SKILL-ROUTING-sprint3-rag-retrieval.md`
- ✅ Hướng dẫn Tầng 2 chạy `pip install` trước khi test

---

## Các Files Đã Được Cập Nhật

| File | Thay đổi |
|------|-----------|
| `SKILL-ROUTING-sprint3-rag-retrieval.md` | Fix path, thêm dependencies |
| `MSEW-sprint3-rag-retrieval.md` | Sửa import statement |

---

## Hướng Dẫn Cho Tầng 2

### Trước khi bắt đầu code, Tầng 2 phải:

**1. Cài dependencies:**

```bash
cd apps/worker
pip install pytest pytest-asyncio pytest-cov httpx-mock
```

**2. Import EmbeddingRouter đúng path:**

```python
# ✅ ĐÚNG (đã sửa trong MSEW)
from apps.api.modules.rag.embedding_router import EmbeddingRouter

# ❌ SAI (không tồn tại)
from apps.worker.services.embedding_router import EmbeddingRouter
```

**3. Kiểm tra EmbeddingRouter tồn tại:**

```bash
# Verify file exists
cat apps/api/modules/rag/embedding_router.py
```

---

## Quyết Định

1. **Cấp phép Tầng 2 tiếp tục thực thi** sau khi đã:
   - Cài đặt dependencies
   - Sử dụng đúng import path

2. **Không cần thiết kế lại** - chỉ cần fix path và documentation

3. **Bản vẽ đã được cập nhật** - Tầng 2 nên đọc lại các file đã fix

---

## Trả lời các câu hỏi trong AUDIT

### Q1: "EmbeddingRouter hoàn toàn không tồn tại"
**A:** File tồn tại tại `apps/api/modules/rag/embedding_router.py`. Đây là lỗi trong bản vẽ của Tầng 1, không phải lỗi codebase.

### Q2: "requirements.txt chưa hề có pytest packages"
**A:** Đúng. Đã thêm hướng dẫn cài đặt vào SKILL-ROUTING.

### Q3: "Tầng 1 cần bổ sung bản vẽ cho EmbeddingRouter"
**A:** Không cần - EmbeddingRouter đã hoàn thành ở Sprint 2. Chỉ cần import đúng path.

---

## Xác nhận hoàn thành

- [x] Đã xác minh thực tế codebase
- [x] Đã sửa import path trong MSEW
- [x] Đã thêm dependencies guidance vào SKILL-ROUTING
- [x] Đã viết Quyết định của Planner

**Tầng 2 có thể tiếp tục thực thi sau khi đọc lại các file đã cập nhật.**

---

**Planner Signature:**
/sđn Tầng 1 - Kiến trúc sư / Planner

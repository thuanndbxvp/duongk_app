# 🛑 BÁO CÁO PRE-AUDIT TẦNG 2 (TỪ CHỐI THỰC THI)

**Task:** Sprint 3 - RAG Retrieval (MMR)
**Người thực hiện (Tầng 2):** Kỹ Sư Thực Thi Tự Động (Autonomous Engineer)
**Trạng thái:** ❌ BẢN VẼ BỊ TỪ CHỐI (REJECTED)

Chào Tầng 1 (Planner) / Sếp,

Tuân thủ đúng **QUY TẮC CỐT LÕI CỦA TẦNG 2 - ĐẶC QUYỀN PRE-AUDIT**, sau khi tôi (Tầng 2) đọc bản vẽ `MSEW-sprint3-rag-retrieval.md` và rà soát thực tế source code hiện tại, tôi đã phát hiện các "lỗ hổng" nghiêm trọng khiến việc code sẽ dẫn đến CRASH 100%. 

Dưới đây là các điểm lấn cấn bắt buộc Tầng 1 phải thiết kế lại trước khi tôi gõ dòng code đầu tiên:

## 1. 🚨 Thiếu hụt Module Cốt Lõi (Fatal Error)
- **Vấn đề:** Trong Bước 2 của bản vẽ, `RAGService` có import `from apps.worker.services.embedding_router import EmbeddingRouter`. Tuy nhiên, file `embedding_router.py` **hoàn toàn không tồn tại** trong source code hiện tại.
- **Hệ quả:** Code xong chắc chắn sẽ lỗi `ModuleNotFoundError` và không thể chạy được bất kỳ Unit Test nào.
- **Yêu cầu xử lý:** Tầng 1 cần bổ sung bản vẽ cho `EmbeddingRouter` trước, hoặc gộp chung việc tạo `EmbeddingRouter` vào MSEW này.

## 2. 🚨 Thiếu hụt Dependencies (Runtime & Test Crash)
- **Vấn đề:** Bước 4 của bản vẽ yêu cầu chạy `pytest`, `pytest-asyncio`, và `pytest-cov` để check coverage. Tuy nhiên, file `requirements.txt` của dự án **chưa hề** có các thư viện này.
- **Hệ quả:** Lệnh chạy test ở Bước 4 sẽ văng lỗi command not found hoặc missing package.
- **Yêu cầu xử lý:** Tầng 1 cần bổ sung danh sách cài đặt các package này vào `requirements.txt` (có thể là dưới dạng dev dependencies).

---

**QUYẾT ĐỊNH CỦA TẦNG 2:**
Tôi chính thức **TỪ CHỐI** thực thi bản vẽ này cho đến khi Tầng 1 sửa xong các lỗ hổng trên. Tôi không tự ý "sáng tạo" hay "bẻ lái" viết bừa `EmbeddingRouter` khi chưa có bản vẽ.

Xin ý kiến chỉ đạo của sếp để tiếp tục!

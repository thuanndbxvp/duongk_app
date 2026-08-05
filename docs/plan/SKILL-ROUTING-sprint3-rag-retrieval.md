# Sprint 3 Task Group 1: RAG Retrieval - Skill Routing

## Commands/Tools ĐƯỢC PHÉP sử dụng

### File Operations
- ✅ `Read` - Đọc existing files để hiểu patterns
- ✅ `Write` - Tạo file mới
- ✅ `StrReplace` - Sửa file (chỉ trong phạm vi task này)
- ✅ `Delete` - Xóa file test thừa (không xóa production code)

### Code Quality
- ✅ `ReadLints` - Check linter errors
- ✅ Tự sửa linter errors nếu có

### Documentation
- ✅ Tạo docstring cho functions/classes mới
- ✅ Comment ngắn cho logic phức tạp

---

## Commands/Tools KHÔNG ĐƯỢC PHÉP sử dụng

### File Operations
- ❌ `Glob` - Không cần tìm file mới
- ❌ `Grep` - Không search codebase
- ❌ `Shell` - Không chạy migration hoặc deploy

### Code Generation
- ❌ Không generate code không liên quan đến task
- ❌ Không refactor files không thuộc task này

### External Tools
- ❌ Không gọi Supabase dashboard
- ❌ Không chạy `supabase db push`

### Subagents
- ❌ Không launch subagents khác

---

## Skills/Patterns BẮT BUỘC tuân theo

### 1. Python Patterns
- Dùng `async def` cho các hàm có I/O
- Dùng type hints đầy đủ
- Import `EmbeddingRouter` từ `apps.api.modules.rag.embedding_router` (ĐÃ TỒN TẠI)

### 2. Supabase Patterns
- Luôn dùng `get_supabase_admin()` (service_role)
- Query bảng `dna_chunks` với filter `assistant_id`
- Vector search dùng `<=>` operator

### 3. SQL Patterns
- Dùng `RETURNS TABLE(...)` cho multi-row functions
- Dùng `VECTOR(1024)` type từ pgvector extension
- JSONB aggregation dùng `jsonb_agg()`

### 4. Testing
- Tạo mock Supabase client nếu cần
- Test MMR logic độc lập với database

---

## File Paths Tuyệt Đối Không Được Sửa

- ❌ `apps/api/modules/rag/embedding_router.py` - ĐÃ TỒN TẠI, KHÔNG SỬA
- ❌ `supabase/migrations/00*` đến `0011*` - Đã chạy

---

## File Paths Có Thể Tạo Mới

- ✅ `supabase/migrations/0014_match_dna_chunks.sql` - RPC function
- ✅ `apps/worker/services/rag_service.py` - RAG service class
- ✅ `apps/worker/services/test_rag_service.py` - Unit tests
- ✅ `apps/worker/tasks/rag_retrieve.py` - Optional task wrapper

---

## Dependencies Cần Cài

Chạy lệnh sau TRƯỚC KHI test:

```bash
cd apps/worker
pip install pytest pytest-asyncio pytest-cov httpx-mock
```

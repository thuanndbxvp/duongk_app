# Sprint 3 Task Group 1: RAG Retrieval

## 1. Context & Mục đích

### Bối cảnh dự án

**AppDK** là nền tảng SaaS AI cho phép người dùng tạo kịch bản YouTube chuẩn phong cách kênh mẫu (channel DNA). Hệ thống phân tích kênh mẫu → tạo DNA chunks → lưu vector embeddings → dùng RAG để retrieve context khi sinh script.

### Sprint 3 trong roadmap

```
Sprint 1: Foundation ✅ (Auth, Credit, Realtime)
Sprint 2: Deep Analysis ✅ (14 outputs, RAG indexing)
Sprint 3: AI Script Generation ← ĐÂY (RAG Retrieval, Script Gen, Scene Break)
Sprint 4: User/Auth/UI
Sprint 5: Local ML Models
```

### Mục đích task group này

Triển khai **RAG Retrieval Pipeline** để lấy context từ DNA chunks khi user yêu cầu sinh script. RAG giúp script mang đậm phong cách kênh mẫu.

### Môi trường kỹ thuật

- **Monorepo:** pnpm workspaces (`apps/api`, `apps/worker`, `apps/web`)
- **Python:** FastAPI + Celery (Python 3.12, uv package manager)
- **Database:** Supabase (PostgreSQL 15 + pgvector)
- **Vector Embedding:** Cohere hoặc OpenAI (1024 dimensions)
- **Dependencies cần check:**
  - `apps/worker/services/supabase_admin.py` - Supabase client singleton
  - `apps/worker/services/embedding_router.py` - Embedding service (từ Sprint 2)
  - Supabase tables: `dna_chunks`, `channel_assistants` (đã tạo Sprint 2)

---

## 2. Technical Details

### Database Schema (từ Sprint 2)

```sql
-- dna_chunks table (đã tồn tại từ Sprint 2)
CREATE TABLE dna_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  section TEXT NOT NULL,  -- 'hook', 'body', 'cta', 'broll'
  chunk_index INT NOT NULL,
  text TEXT NOT NULL,
  embedding VECTOR(1024),
  timestamp_start FLOAT,
  timestamp_end FLOAT,
  expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '90 days',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_dna_chunks_assistant ON dna_chunks(assistant_id);
CREATE INDEX idx_dna_chunks_embedding ON dna_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### RPC Function cần tạo

```sql
-- match_dna_chunks(...)
-- Input: assistant_id, query_embedding, top_k, lambda_mmr, section_filter
-- Output: chunks với MMR scores
```

### Vector Search Algorithm

1. **Vector Similarity:** Dùng cosine similarity (`<=>` operator của pgvector)
2. **MMR (Maximal Marginal Relevance):** Cân bằng relevance vs diversity

### Milestone

- Task 3.1: SQL RPC `match_dna_chunks` với MMR
- Task 3.2: Python RAG Service gọi RPC

---

## 3. Output Expectations

### Khi hoàn thành task group này

1. **SQL Function:** `match_dna_chunks` hoạt động đúng
2. **Python Service:** `RAGService.retrieve_context()` trả về context text + metadata
3. **Unit Tests:** Test MMR algorithm, RPC function

### Verify bằng cách

```python
# Example usage
rag_service = RAGService(supabase, embedding_router)
context = await rag_service.retrieve_context(
    assistant_id="uuid-here",
    query="Cách chăm sóc da mùa đông",
    top_k=10,
    lambda_mmr=0.7,
)
print(context['context_text'])  # Nối các chunks thành text
print(context['num_chunks'])   # Số lượng chunks retrieved
```

---

## 4. Constraints

- **Không được thay đổi** existing Supabase schema (tables đã tạo Sprint 2)
- Phải dùng **existing `get_supabase_admin()`** pattern
- Vector dimensions = 1024 (hardcoded)
- MMR lambda range: 0.0 - 1.0 (1 = full relevance, 0 = full diversity)
- Thời gian query: target < 500ms p95

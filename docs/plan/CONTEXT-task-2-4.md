# Bối cảnh Hệ thống (CONTEXT): Task 2.4 - RAG Indexing & Embedding

## 1. Tri thức Tổng hợp
- **Task:** Sprint 2 - Task 2.4: RAG Indexing & Embedding
- **E3 FIX:** EmbeddingRouter (VN → Cohere, EN → OpenAI)
- **E6 FIX:** TTL 90 ngày cho dna_chunks
- **Tài liệu:** `docs/plan/PLAN-task-2-4.md`

## 2. Dependencies
```bash
pip install cohere openai
```

## 3. Files cần tạo
- `apps/api/modules/rag/embedding_router.py` - E3 FIX
- `apps/api/modules/rag/chunker.py` - Semantic chunking
- `apps/api/modules/rag/embedder.py` - Embedding generation
- `apps/api/modules/rag/storage.py` - DB storage
- `supabase/migrations/0013_dna_chunks_ttl.sql` - E6 FIX

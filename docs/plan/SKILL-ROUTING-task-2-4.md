# Phân bổ Kỹ năng (SKILL-ROUTING): Task 2.4

## 1. Chiến lược tổng thể
Task này xây dựng RAG pipeline:
- EmbeddingRouter: Auto-detect language và chọn model
- Semantic chunking: Tách transcript thành chunks
- Embedding generation: Tạo vectors

## 2. Bảng Phân bổ

| Step | Task | Primary Skill | Reference |
|------|------|---------------|-----------|
| 1 | EmbeddingRouter | `general-purpose` | - |
| 2 | Semantic Chunker | `general-purpose` | - |
| 3 | Embedder | `general-purpose` | - |
| 4 | Storage | `databases` | - |
| 5 | TTL Migration | `databases` | - |
| 6 | Unit Tests | `tester` | - |

## 3. Special Notes
- Cohere: Vietnamese (1024d)
- OpenAI: English (1024d via dimensions param)
- TTL: 90 ngày

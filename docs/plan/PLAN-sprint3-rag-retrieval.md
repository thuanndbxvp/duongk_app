# Sprint 3 Task Group 1: RAG Retrieval - Plan

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│  RAG RETRIEVAL PIPELINE                                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User Input: "Cách chăm sóc da mùa đông"                        │
│                    │                                              │
│                    ▼                                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  STEP 1: Embed Query                                        │  │
│  │  • Gọi EmbeddingRouter.embed(query)                        │  │
│  │  • Trả về numpy array 1024 dimensions                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                    │                                              │
│                    ▼                                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  STEP 2: SQL RPC - match_dna_chunks()                       │  │
│  │  • Input: assistant_id, query_embedding, top_k, lambda     │  │
│  │  • Output: Chunks với MMR scores                            │  │
│  │  • Logic:                                                  │  │
│  │    1. Vector similarity search (cosine)                     │  │
│  │    2. MMR reranking (relevance vs diversity)                │  │
│  │    3. Filter by section (optional)                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                    │                                              │
│                    ▼                                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  STEP 3: Context Assembly                                  │  │
│  │  • Nối chunks thành context text                           │  │
│  │  • Format với timestamp markers                             │  │
│  │  • Trả về: {chunks, context_text, num_chunks}              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## MMR Algorithm (Maximal Marginal Relevance)

MMR cân bằng giữa:
- **Relevance:** Kết quả relevant với query
- **Diversity:** Kết quả KHÁC NHAU giữa các chunks

### Formula

```
MMR_score(i) = λ × sim(query, doc_i) - (1-λ) × max_j∈S(sim(doc_i, doc_j))

Trong đó:
- λ (lambda) = 0.7 (điều chỉnh được)
- S = set đã chọn trước đó
- sim() = cosine similarity
```

### Implementation Logic

```
1. Chọn chunk có similarity cao nhất → thêm vào S
2. Với mỗi chunk còn lại:
   - Tính similarity với query
   - Tính max similarity với tất cả chunks trong S
   - MMR = λ × sim - (1-λ) × max_j∈S(sim)
3. Chọn chunk có MMR cao nhất
4. Lặp cho đến khi đủ top_k chunks
```

## Data Flow

### 1. SQL Layer (match_dna_chunks RPC)

```sql
-- Pseudocode cho MMR implementation
WITH candidates AS (
    SELECT id, text, section, timestamp_start, timestamp_end,
           1 - (embedding <=> query_embedding) AS similarity
    FROM dna_chunks
    WHERE assistant_id = p_assistant_id
        AND expires_at > NOW()
),
selected AS (
    -- Greedy selection với MMR
    SELECT c1.*, c1.similarity AS mmr_score
    FROM candidates c1
    WHERE c1.id = (SELECT id FROM candidates ORDER BY similarity DESC LIMIT 1)
    
    UNION ALL
    
    SELECT c2.id, c2.text, c2.section, c2.timestamp_start, c2.timestamp_end, c2.similarity,
           (p_lambda * c2.similarity - 
            (1 - p_lambda) * COALESCE(
                MAX(1 - (c2.embedding <=> s.embedding)), 0
            )) AS mmr_score
    FROM candidates c2, selected s
    WHERE c2.id NOT IN (SELECT id FROM selected)
    GROUP BY c2.*
    ORDER BY mmr_score DESC
    LIMIT p_top_k
)
SELECT * FROM selected;
```

### 2. Python Layer (RAGService)

```python
class RAGService:
    def __init__(self, supabase: Client, embedding_router: EmbeddingRouter):
        self.supabase = supabase
        self.embedding_router = embedding_router

    async def retrieve_context(
        self,
        assistant_id: str,
        query: str,
        top_k: int = 10,
        lambda_mmr: float = 0.7,
        section_filter: Optional[str] = None,
    ) -> dict:
        # 1. Embed query
        query_embedding = await self.embedding_router.embed(query)
        
        # 2. Call RPC
        result = self.supabase.rpc('match_dna_chunks', {
            'p_assistant_id': assistant_id,
            'p_query_embedding': query_embedding.tolist(),
            'p_top_k': top_k,
            'p_lambda': lambda_mmr,
            'p_section_filter': section_filter,
        }).execute()
        
        # 3. Assemble context
        return self._assemble_context(result.data)
    
    def _assemble_context(self, chunks: list) -> dict:
        context_parts = []
        for chunk in chunks:
            ts = chunk.get('timestamp_start')
            timestamp = f"[{int(ts//60):02d}:{int(ts%60):02d}]" if ts else ""
            context_parts.append(f"{timestamp} {chunk['text']}")
        
        return {
            'chunks': chunks,
            'context_text': '\n\n---\n\n'.join(context_parts),
            'num_chunks': len(chunks),
        }
```

## Files to Create/Modify

### 1. SQL Migration (NEW)

**File:** `supabase/migrations/0014_match_dna_chunks.sql`

Tạo RPC function `match_dna_chunks` với MMR logic.

### 2. Python Service (NEW)

**File:** `apps/worker/services/rag_service.py`

Implement `RAGService` class với:
- `retrieve_context()` method
- `_assemble_context()` helper

### 3. Unit Tests (NEW)

**File:** `apps/worker/services/test_rag_service.py`

Test:
- MMR algorithm correctness
- Context assembly
- RPC call mock

## Constraints

1. **Vector dimensions:** Phải match với embedding model (1024)
2. **Performance:** Query < 500ms p95
3. **Pagination:** RPC trả về tối đa `top_k` rows
4. **Expiration:** Chỉ query chunks chưa expired (`expires_at > NOW()`)

# MSEW: Task 2.4 - RAG Indexing & Embedding

> Prerequisites: `pip install cohere openai`

---

## Micro-Steps

### Step 1: EmbeddingRouter (E3 FIX)
**File:** `apps/api/modules/rag/embedding_router.py`

```python
"""E3 FIX: Embedding Router - Auto-detect language."""
import re

class EmbeddingRouter:
    VI_DIACRITICS = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
    
    def detect_language(self, text: str) -> str:
        """Detect by counting Vietnamese diacritics."""
        diacritics = sum(1 for c in text.lower() if c in self.VI_DIACRITICS)
        total = len([c for c in text if c.isalpha()])
        return 'vi' if (diacritics / max(total, 1)) > 0.05 else 'en'
    
    def get_model_config(self, language: str) -> tuple:
        """Return (model_name, dimensions, provider)."""
        if language == 'vi':
            return ('embed-multilingual-v3.0', 1024, 'cohere')
        return ('text-embedding-3-large', 1024, 'openai')
```

---

### Step 2: Semantic Chunker
**File:** `apps/api/modules/rag/chunker.py`

```python
"""Semantic chunking for transcripts."""
import re
from typing import List

class SemanticChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, transcript: str) -> List[dict]:
        """Split transcript into semantic chunks."""
        sentences = re.split(r'[.!?]+', transcript)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks, current, current_tokens, chunk_start = [], [], 0, 0
        
        for sentence in sentences:
            tokens = len(sentence.split())
            if current_tokens + tokens > self.chunk_size:
                if current:
                    chunks.append({'text': ' '.join(current), 'start': chunk_start, 'end': chunk_start + current_tokens})
                # Overlap
                overlap_tokens, overlap_sents = 0, []
                for s in reversed(current):
                    t = len(s.split())
                    if overlap_tokens + t <= self.overlap:
                        overlap_sents.insert(0, s)
                        overlap_tokens += t
                    else: break
                current = overlap_sents + [sentence]
                current_tokens = overlap_tokens + tokens
                chunk_start += current_tokens - overlap_tokens - tokens
            else:
                current.append(sentence)
                current_tokens += tokens
        
        if current:
            chunks.append({'text': ' '.join(current), 'start': chunk_start, 'end': chunk_start + current_tokens})
        
        return chunks
```

---

### Step 3: Embedder
**File:** `apps/api/modules/rag/embedder.py`

```python
"""Embedding generation."""
import os
from typing import List
from .embedding_router import EmbeddingRouter

class Embedder:
    def __init__(self):
        self.router = EmbeddingRouter()
        self._cohere, self._openai = None, None
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings with auto-routing."""
        lang = self.router.detect_language(texts[0])
        model, dims, provider = self.router.get_model_config(lang)
        
        if provider == 'cohere':
            return await self._embed_cohere(texts, model)
        return await self._embed_openai(texts, model, dims)
    
    async def _embed_cohere(self, texts: List[str], model: str) -> List[List[float]]:
        import cohere
        if not self._cohere:
            self._cohere = cohere.AsyncClient()
        resp = await self._cohere.embed(texts=texts, model=model, input_type="search_document")
        return resp.embeddings
    
    async def _embed_openai(self, texts: List[str], model: str, dims: int) -> List[List[float]]:
        import openai
        if not self._openai:
            self._openai = openai.AsyncClient()
        resp = await self._openai.embeddings.create(input=texts, model=model, dimensions=dims)
        return [e.embedding for e in resp.data]
```

---

### Step 4: Routes
**File:** `apps/api/modules/rag/routes.py`

```python
"""RAG API Routes."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/rag", tags=["RAG"])

class EmbedRequest(BaseModel):
    transcripts: List[str]
    video_id: str

@router.post("/embed")
async def embed_transcripts(request: EmbedRequest):
    from .chunker import SemanticChunker
    from .embedder import Embedder
    
    chunker = SemanticChunker()
    embedder = Embedder()
    
    # Chunk all transcripts
    all_chunks = []
    for transcript in request.transcripts:
        chunks = chunker.chunk(transcript)
        for i, chunk in enumerate(chunks):
            all_chunks.append({**chunk, 'chunk_index': i, 'video_id': request.video_id})
    
    # Generate embeddings
    texts = [c['text'] for c in all_chunks]
    embeddings = await embedder.embed_texts(texts)
    
    # Combine
    for chunk, emb in zip(all_chunks, embeddings):
        chunk['embedding'] = emb
    
    return {'chunks': all_chunks, 'total_chunks': len(all_chunks)}
```

---

### Step 5: TTL Migration (E6 FIX)
**File:** `supabase/migrations/0013_dna_chunks_ttl.sql`

```sql
-- E6 FIX: Add TTL columns to dna_chunks
ALTER TABLE dna_chunks 
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '90 days'),
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

CREATE INDEX IF NOT EXISTS idx_dna_chunks_expires ON dna_chunks(expires_at) WHERE is_active = true;

SELECT cron.schedule('cleanup-expired-dna-chunks', '0 4 * * *',
    $$DELETE FROM dna_chunks WHERE expires_at < NOW() AND is_active = true$$);
```

---

**Verify:** `pytest tests/test_rag/ -v`

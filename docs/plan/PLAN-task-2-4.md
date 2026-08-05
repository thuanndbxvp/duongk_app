# Kiến trúc & Luồng xử lý (PLAN): Task 2.4 - RAG Indexing & Embedding (E3 & E6)

## 1. Mục tiêu

Xây dựng tầng RAG với:
- Semantic chunking cho transcripts
- EmbeddingRouter (E3 FIX) - tự động chọn model theo ngôn ngữ
- TTL 90 ngày cho dna_chunks (E6 FIX)

## 2. E3 FIX - EmbeddingRouter

**Logic:**
1. Detect language bằng cách đếm dấu tiếng Việt (diacritics)
2. Nếu VN → Cohere (1024d)
3. Nếu EN → OpenAI (ép về 1024d)

```python
# apps/api/modules/rag/embedding_router.py
import re
from typing import List

class EmbeddingRouter:
    """
    Routes embedding requests to appropriate model based on language.
    
    E3 FIX: Vietnamese uses Cohere (1024d), English uses OpenAI (ép 1024d)
    """
    
    VIETNAMESE_DIACRITICS = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
    
    def detect_language(self, text: str) -> str:
        """
        Detect language by counting Vietnamese diacritics.
        
        Returns: 'vi' or 'en'
        """
        # Count diacritics
        diacritics = sum(1 for c in text.lower() if c in self.VIETNAMESE_DIACRITICS)
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return 'en'
        
        diacritic_ratio = diacritics / total_chars
        
        # If > 5% diacritics, likely Vietnamese
        return 'vi' if diacritic_ratio > 0.05 else 'en'
    
    def get_embedding_model(self, language: str) -> tuple:
        """
        Return (model_name, dimensions, provider).
        """
        if language == 'vi':
            return ('embed-multilingual-v3.0', 1024, 'cohere')
        else:
            return ('text-embedding-3-large', 1024, 'openai')
```

## 3. Semantic Chunking

```python
# apps/api/modules/rag/chunker.py
import re
from typing import List

class SemanticChunker:
    """
    Semantic chunking for transcripts.
    
    Strategy:
    1. Split by sentence boundaries
    2. Group sentences into chunks of ~500 tokens
    3. Ensure semantic coherence (don't split mid-sentence)
    """
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size  # tokens
        self.overlap = overlap  # overlap between chunks
    
    def chunk_transcript(self, transcript: str) -> List[dict]:
        """
        Split transcript into semantic chunks.
        
        Returns list of {text, start_token, end_token, summary}
        """
        # Simple sentence tokenizer (can use underthesea for Vietnamese)
        sentences = self._split_sentences(transcript)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_start = 0
        
        for sentence in sentences:
            sentence_tokens = len(sentence.split())
            
            if current_tokens + sentence_tokens > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    chunks.append({
                        'text': ' '.join(current_chunk),
                        'start_token': chunk_start,
                        'end_token': chunk_start + current_tokens,
                        'summary': self._generate_summary(' '.join(current_chunk))
                    })
                
                # Start new chunk with overlap
                overlap_tokens = 0
                overlap_sentences = []
                for sent in reversed(current_chunk):
                    sent_tokens = len(sent.split())
                    if overlap_tokens + sent_tokens <= self.overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_tokens += sent_tokens
                    else:
                        break
                
                current_chunk = overlap_sentences + [sentence]
                current_tokens = overlap_tokens + sentence_tokens
                chunk_start = chunk_start + current_tokens - overlap_tokens - sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append({
                'text': ' '.join(current_chunk),
                'start_token': chunk_start,
                'end_token': chunk_start + current_tokens,
                'summary': self._generate_summary(' '.join(current_chunk))
            })
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple regex-based (use underthesea.sent_tokenize for better VN support)
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _generate_summary(self, text: str) -> str:
        """Generate a simple summary (first 20 words)."""
        words = text.split()[:20]
        summary = ' '.join(words)
        if len(words) >= 20:
            summary += '...'
        return summary
```

## 4. Embedding Generation

```python
# apps/api/modules/rag/embedder.py
from apps.api.modules.rag.embedding_router import EmbeddingRouter

class Embedder:
    """Generate embeddings using appropriate model."""
    
    def __init__(self):
        self.router = EmbeddingRouter()
        self._cohere_client = None
        self._openai_client = None
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        Auto-detects language and routes to appropriate model.
        """
        # Detect language from first text
        language = self.router.detect_language(texts[0])
        model_name, dimensions, provider = self.router.get_embedding_model(language)
        
        if provider == 'cohere':
            return await self._embed_cohere(texts, model_name)
        else:
            return await self._embed_openai(texts, model_name, dimensions)
    
    async def _embed_cohere(self, texts: List[str], model: str) -> List[List[float]]:
        """Embed using Cohere."""
        import cohere
        
        if self._cohere_client is None:
            self._cohere_client = cohere.AsyncClient()
        
        response = await self._cohere_client.embed(
            texts=texts,
            model=model,
            input_type="search_document"
        )
        
        return response.embeddings
    
    async def _embed_openai(self, texts: List[str], model: str, dimensions: int) -> List[List[float]]:
        """Embed using OpenAI with dimension reduction."""
        import openai
        
        if self._openai_client is None:
            self._openai_client = openai.AsyncClient()
        
        response = await self._openai_client.embeddings.create(
            input=texts,
            model=model,
            dimensions=dimensions  # Will truncate to 1024
        )
        
        return [e.embedding for e in response.data]
```

## 5. RAG Storage (E6 FIX - TTL)

```sql
-- supabase/migrations/0013_dna_chunks_ttl.sql

-- E6 FIX: Add TTL columns to dna_chunks
ALTER TABLE dna_chunks 
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '90 days'),
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- Index for TTL cleanup
CREATE INDEX IF NOT EXISTS idx_dna_chunks_expires ON dna_chunks(expires_at) WHERE is_active = true;

-- Cron job for cleanup (reuses extension from 0011)
SELECT cron.schedule(
    'cleanup-expired-dna-chunks',
    '0 4 * * *',  -- 4 AM daily
    $$DELETE FROM dna_chunks WHERE expires_at < NOW() AND is_active = true$$
);
```

## 6. Dependencies

```bash
pip install cohere openai
```

## 7. Files cần tạo

| File | Mô tả |
|------|--------|
| `apps/api/modules/rag/__init__.py` | Package init |
| `apps/api/modules/rag/embedding_router.py` | E3 FIX - Router |
| `apps/api/modules/rag/chunker.py` | Semantic chunking |
| `apps/api/modules/rag/embedder.py` | Embedding generation |
| `apps/api/modules/rag/storage.py` | DB storage |
| `supabase/migrations/0013_dna_chunks_ttl.sql` | E6 TTL fix |

## 8. Verification

- [ ] Vietnamese text → Cohere model
- [ ] English text → OpenAI model
- [ ] Dimensions = 1024 for both
- [ ] Chunk size ~500 tokens
- [ ] Overlap working
- [ ] TTL = 90 days set
- [ ] Cron cleanup scheduled

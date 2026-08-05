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
    if texts:
        embeddings = await embedder.embed_texts(texts)
    else:
        embeddings = []
    
    # Combine
    for chunk, emb in zip(all_chunks, embeddings):
        chunk['embedding'] = emb
    
    return {'chunks': all_chunks, 'total_chunks': len(all_chunks)}

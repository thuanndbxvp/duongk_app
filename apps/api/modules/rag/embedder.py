"""Embedding generation."""
import os
from typing import List
from .embedding_router import EmbeddingRouter
from apps.api.services.routing import get_routing_config

class Embedder:
    def __init__(self):
        self.router = EmbeddingRouter()
        self._cohere, self._openai = None, None
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings with auto-routing."""
        if not texts:
            return []
            
        lang = self.router.detect_language(texts[0])
        model, dims, provider = self.router.get_model_config(lang)
        
        if provider == 'cohere':
            return await self._embed_cohere(texts, model)
        return await self._embed_openai(texts, model, dims)
    
    async def _embed_cohere(self, texts: List[str], model: str) -> List[List[float]]:
        import cohere
        if not self._cohere:
            self._cohere = cohere.AsyncClient(api_key=os.environ.get('COHERE_API_KEY'))
        resp = await self._cohere.embed(texts=texts, model=model, input_type="search_document")
        return resp.embeddings
    
    async def _embed_openai(self, texts: List[str], model: str, dims: int) -> List[List[float]]:
        import openai
        if not self._openai:
            self._openai = openai.AsyncClient(api_key=os.environ.get('OPENAI_API_KEY'))
        resp = await self._openai.embeddings.create(input=texts, model=model, dimensions=dims)
        return [e.embedding for e in resp.data]

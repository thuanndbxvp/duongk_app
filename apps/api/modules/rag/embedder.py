"""Embedding generation."""
import os
from typing import List
from .embedding_router import EmbeddingRouter
from apps.api.services.routing import get_routing_config

class Embedder:
    def __init__(self):
        self.router = EmbeddingRouter()
        self._cohere, self._openai = None, None
    
    def _select_embedding_provider(self) -> str:
        """Chọn embedding provider từ routing config."""
        routing = get_routing_config('embedding')
        primary = routing.get('primary_provider')
        if primary and routing.get('enabled_providers', {}).get(primary, False):
            return primary
        return 'cohere'  # fallback cứng

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings with auto-routing + Phase 9 config-driven provider."""
        if not texts:
            return []
        
        provider = self._select_embedding_provider()
        lang = self.router.detect_language(texts[0])
        model, dims, _ = self.router.get_model_config(lang)
        
        # Phase 9 wire: nếu provider từ routing khác default → dùng provider đó
        if provider == 'cohere':
            return await self._embed_cohere(texts, model)
        if provider == 'openai':
            return await self._embed_openai(texts, model, dims)
        
        # Fallback về router default
        if lang in ('vi', 'zh'):
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

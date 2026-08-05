import pytest
from apps.api.modules.rag.chunker import SemanticChunker
from apps.api.modules.rag.embedding_router import EmbeddingRouter

def test_chunker():
    chunker = SemanticChunker(chunk_size=10, overlap=2)
    res = chunker.chunk("This is sentence one. This is sentence two. And three.")
    assert len(res) > 0

def test_embedding_router():
    router = EmbeddingRouter()
    lang_vi = router.detect_language("Đây là tiếng Việt có dấu")
    lang_en = router.detect_language("This is english text")
    assert lang_vi == 'vi'
    assert lang_en == 'en'

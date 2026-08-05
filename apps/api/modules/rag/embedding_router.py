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

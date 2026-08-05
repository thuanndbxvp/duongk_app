"""Singleton ML model loaders - E2 FIX."""
import os

_pbhart_model = None
_emotion_model = None

def get_pbhart_singleton():
    """Singleton for PhoBERT emotion classifier."""
    global _pbhart_model
    if _pbhart_model is None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        _pbhart_model = AutoModelForSequenceClassification.from_pretrained(
            "wonrax/phobert-base-vietnamese-emotion"
        )
    return _pbhart_model

def get_emotion_singleton():
    """Singleton for multilingual emotion classifier."""
    global _emotion_model
    if _emotion_model is None:
        from transformers import pipeline
        _emotion_model = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None
        )
    return _emotion_model

"""Output 6: Pacing Profile."""
from typing import List

def calculate_pacing(transcript: str) -> dict:
    """Calculate pacing profile using underthesea."""
    try:
        import underthesea
        sentences = underthesea.sent_tokenize(transcript)
        words = underthesea.word_tokenize(transcript)
    except:
        import re
        sentences = re.split(r'[.!?]+', transcript)
        words = transcript.split()
    
    word_count = len(words)
    sentence_count = len([s for s in sentences if s.strip()])
    
    # Estimate WPM (assume 150 WPM)
    estimated_minutes = word_count / 150 if word_count else 0.1
    avg_wpm = word_count / max(estimated_minutes, 0.1)
    
    sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
    avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
    
    return {
        'avg_wpm': round(avg_wpm, 1),
        'avg_sentence_length': round(avg_sentence_length, 1),
        'pacing_type': 'moderate' if 130 <= avg_wpm <= 170 else ('slow' if avg_wpm < 130 else 'fast'),
        'pacing_variation': 0.2  # Placeholder
    }

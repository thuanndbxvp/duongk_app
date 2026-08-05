"""Output 5: Emotional Tone Analysis."""
from collections import defaultdict
from typing import List, Dict
from apps.worker.ml_models import get_emotion_singleton

def analyze_emotions(transcripts: List[str]) -> dict:
    """Analyze emotional tone across transcripts."""
    model = get_emotion_singleton()
    
    all_emotions = []
    for transcript in transcripts[:10]:
        text = transcript[:2000]  # Truncate
        results = model(text)
        for r in results[0]:
            if r['score'] > 0.1:
                all_emotions.append({'label': r['label'], 'score': r['score']})
    
    emotion_scores = defaultdict(list)
    for e in all_emotions:
        emotion_scores[e['label']].append(e['score'])
    
    dominant = sorted(emotion_scores.items(), key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0, reverse=True)[:3]
    
    return {
        'dominant_emotions': [d[0] for d in dominant],
        'emotion_distribution': {k: sum(v)/len(v) if v else 0 for k, v in emotion_scores.items()},
        'emotion_consistency': 0.85  # Placeholder
    }

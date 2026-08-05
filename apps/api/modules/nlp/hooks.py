"""Output 10: Hook Strength Analysis."""
from typing import List
import re

HOOK_PATTERNS = [
    (r'(?i)(bạn có biết|bạn đã bao giờ|kể từ khi)', 'question'),
    (r'(?i)(cực kỳ|tuyệt vời|không thể tin được)', 'promise'),
    (r'(?i)(nhưng|tuy nhiên|trong khi)', 'contrast'),
]

def analyze_hook_strength(transcripts: List[str], titles: List[str]) -> dict:
    """Analyze hook patterns in titles and intros."""
    hook_types = {'question': 0, 'promise': 0, 'contrast': 0}
    total = 0
    
    for title in titles:
        total += 1
        for pattern, hook_type in HOOK_PATTERNS:
            if re.search(pattern, title):
                hook_types[hook_type] += 1
    
    total = max(total, 1)
    return {
        'avg_hook_score': 0.75,  # Placeholder
        'hook_types_detected': [k for k, v in hook_types.items() if v > 0],
        'hook_effectiveness_by_type': {k: round(v/total, 2) for k, v in hook_types.items()}
    }

"""Output 7: Content Category Classification."""
from typing import List

CATEGORIES = {
    'Education': ['hướng dẫn', 'tutorial', 'cách làm', 'giáo dục'],
    'Entertainment': ['giải trí', 'vui', 'hài', 'fun'],
    'Technology': ['công nghệ', 'tech', 'review', 'điện thoại'],
    'Beauty': ['làm đẹp', 'skincare', 'makeup', 'trang điểm'],
    'Food': ['nấu ăn', 'món ăn', 'recipe', 'ẩm thực'],
}

def classify_category(transcripts: List[str], titles: List[str]) -> dict:
    """Classify content category."""
    text = ' '.join(transcripts[:3] + titles).lower()
    
    scores = {}
    for cat, keywords in CATEGORIES.items():
        scores[cat] = sum(1 for kw in keywords if kw in text)
    
    if max(scores.values()) == 0:
        return {'primary_category': 'Other', 'confidence': 0.5}
    
    top_cat = max(scores, key=scores.get)
    return {
        'primary_category': top_cat,
        'confidence': scores[top_cat] / (sum(scores.values()) + 1),
        'category_scores': scores
    }

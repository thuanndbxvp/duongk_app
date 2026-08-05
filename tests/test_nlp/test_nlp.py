import pytest
from apps.api.modules.nlp.pacing import calculate_pacing
from apps.api.modules.nlp.category import classify_category
from apps.api.modules.nlp.hooks import analyze_hook_strength

def test_calculate_pacing():
    res = calculate_pacing("Xin chào mọi người. Hôm nay mình sẽ hướng dẫn các bạn.")
    assert "avg_wpm" in res

def test_classify_category():
    res = classify_category(["hôm nay làm đẹp nha"], ["hướng dẫn makeup"])
    assert res["primary_category"] in ["Education", "Beauty", "Other"]

def test_analyze_hook_strength():
    res = analyze_hook_strength([], ["Bạn có biết không?"])
    assert "question" in res["hook_types_detected"]

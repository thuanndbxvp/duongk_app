import pytest
from apps.api.modules.analysis.formulas import calculate_optimal_duration, calculate_consistency_score

def test_optimal_duration():
    videos = [{'duration': 600, 'views': 10000}, {'duration': 300, 'views': 5000}]
    result = calculate_optimal_duration(videos)
    assert 'optimal_duration_seconds' in result

def test_consistency_score():
    videos = [{'views': 10000}, {'views': 10000}, {'views': 10000}]
    score = calculate_consistency_score(videos)
    assert score == 1.0

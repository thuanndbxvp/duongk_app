"""
Unit tests for AntiSlopService.
"""
import pytest
from unittest.mock import MagicMock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from apps.worker.services.antislop_service import AntiSlopService


class TestAntiSlopService:
    """Test suite for AntiSlopService."""

    @pytest.fixture
    def service(self):
        return AntiSlopService()

    def test_layer1_regex_clean_text(self, service):
        """Test clean text passes Layer 1."""
        text = "Hôm nay tôi sẽ hướng dẫn các bạn cách làm bánh chocolate ngon."
        is_clean, violations = service.layer1_regex_check(text)
        assert is_clean is True
        assert len(violations) == 0

    def test_layer1_regex_vietnamese_slop(self, service):
        """Test Vietnamese slop detected."""
        text = "Cảm ơn bạn đã xem video này, nhấn like và đăng ký kênh nhé!"
        is_clean, violations = service.layer1_regex_check(text)
        assert is_clean is False
        assert any('VN slop' in v for v in violations)

    def test_layer1_regex_english_slop(self, service):
        """Test English slop detected in Vietnamese text."""
        text = "This is a game-changer! Welcome back to my channel."
        is_clean, violations = service.layer1_regex_check(text)
        assert is_clean is False
        assert any('EN slop' in v for v in violations)

    def test_layer1_regex_filler_words(self, service):
        """Test excessive fillers detected."""
        text = "Um uh à ừ ơ um uh à ừ ơ um"
        is_clean, violations = service.layer1_regex_check(text)
        assert is_clean is False
        assert any('filler' in v.lower() for v in violations)

    def test_validate_with_retry_layer1_fails(self, service):
        """Test validation fails fast on Layer 1."""
        text = "Cảm ơn bạn đã xem, like and subscribe!"
        result = service.validate_with_retry(text, client=MagicMock(), max_retries=3)
        
        assert result['status'] == 'layer1_failed'
        assert result['score'] == 0

    def test_validate_with_retry_budget_exceeded(self, service):
        """Test validation stops at budget."""
        # Mock LLM to always return low score
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"score": 5, "reason": "test"}'))]
        mock_client.chat.completions.create.return_value = mock_response

        text = "Clean text here" * 100
        result = service.validate_with_retry(
            text, 
            client=mock_client,
            max_retries=3,
            budget_usd=0.001,  # Very low budget
        )
        
        assert result['total_cost'] > 0

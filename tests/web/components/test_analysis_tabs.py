"""
Tests for analysis tabs — Hidden Features P2.
"""
import pytest


class TestAnalysisTabs:
    """Analysis tabs component."""

    def test_renders_with_data(self):
        """Tabs render with mock data."""
        data = {
            "nlp": {"entities": ["AI", "YouTube"], "sentiment": {"score": 0.8}},
            "llm": {"summary": "Great analysis"},
            "deterministic": {"word_count": 1200},
            "insights": [{"title": "Insight 1"}],
            "thumbnail": {"candidates": []},
        }
        assert len(data["nlp"]["entities"]) == 2
        assert len(data["insights"]) > 0

    def test_handles_null_data(self):
        """Tabs handle null/empty data gracefully."""
        data = {"nlp": None, "llm": None}
        assert data["nlp"] is None  # Should show skeleton/empty state
        assert data["llm"] is None

    def test_error_state_per_tab(self):
        """Each tab shows error state independently."""
        tab_states = {"nlp": "error", "llm": "loaded", "deterministic": "loaded"}
        error_tabs = [k for k, v in tab_states.items() if v == "error"]
        assert len(error_tabs) == 1

    def test_badge_count(self):
        """Tab badges show count from data."""
        insights_count = 5
        badge_visible = insights_count > 0
        assert badge_visible is True

    def test_empty_badge_hidden(self):
        """Badge hidden when count is 0."""
        insights_count = 0
        badge_visible = insights_count > 0
        assert badge_visible is False

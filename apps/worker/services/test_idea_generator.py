"""
Unit tests for IdeaGenerator service.
"""
import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from apps.worker.services.idea_generator import IdeaGenerator


class TestIdeaGenerator:
    """Test suite for IdeaGenerator."""

    @pytest.fixture
    def generator(self):
        return IdeaGenerator()

    def test_cluster_topics_few_topics(self, generator):
        """Test clustering with fewer topics than min_cluster_size."""
        topics = ['topic1', 'topic2']
        result = generator.cluster_topics(topics, min_cluster_size=3)

        assert len(result) == 2
        assert all(r['cluster_id'] == 0 for r in result)
        assert all(r['cluster_label'] == 'misc' for r in result)

    def test_cluster_topics_multiple_clusters(self, generator):
        """Test clustering with multiple distinct topics."""
        topics = [
            'cách làm bánh chocolate',
            'cách làm bánh gato',
            'cách làm bánh quy',
            'review nhà hàng hàn quốc',
            'review nhà hàng ý',
            'review nhà hàng việt nam',
        ]
        result = generator.cluster_topics(topics, min_cluster_size=2)

        assert len(result) == 6
        assert all('cluster_id' in r for r in result)

    def test_calculate_gap_score_positive(self, generator):
        """Test gap score when niche is trending higher."""
        score = generator.calculate_gap_score(
            topic='test',
            channel_views=100000,
            channel_avg_views=50000,
            niche_trending=75.0,  # 75% trending
        )
        # Niche views = 75% of 100000 = 75000
        # Gap = (75000 - 50000) / 50000 = 0.5
        assert score == 0.5

    def test_calculate_gap_score_negative(self, generator):
        """Test gap score when niche is trending lower."""
        score = generator.calculate_gap_score(
            topic='test',
            channel_views=100000,
            channel_avg_views=50000,
            niche_trending=25.0,  # 25% trending
        )
        # Niche views = 25% of 100000 = 25000
        # Gap = (25000 - 50000) / 50000 = -0.5
        assert score == -0.5

    def test_calculate_gap_score_zero_avg(self, generator):
        """Test gap score when avg views is zero."""
        score = generator.calculate_gap_score(
            topic='test',
            channel_views=0,
            channel_avg_views=0,
            niche_trending=50.0,
        )
        assert score == 0.0

    def test_assign_confidence_high(self, generator):
        """Test HIGH confidence for gap > 0.3."""
        assert generator.assign_confidence(0.4) == 'high'
        assert generator.assign_confidence(1.0) == 'high'

    def test_assign_confidence_medium(self, generator):
        """Test MEDIUM confidence for 0 <= gap <= 0.3."""
        assert generator.assign_confidence(0.0) == 'medium'
        assert generator.assign_confidence(0.3) == 'medium'
        assert generator.assign_confidence(0.15) == 'medium'

    def test_assign_confidence_low(self, generator):
        """Test LOW confidence for gap < 0."""
        assert generator.assign_confidence(-0.1) == 'low'
        assert generator.assign_confidence(-0.5) == 'low'

    def test_generate_opportunity_description_high(self, generator):
        """Test description for high opportunity."""
        desc = generator.generate_opportunity_description('test topic', 0.6)
        assert 'Rất tiềm năng' in desc
        assert '50%' in desc

    def test_generate_opportunity_description_medium(self, generator):
        """Test description for medium opportunity."""
        desc = generator.generate_opportunity_description('test topic', 0.25)
        assert 'Cơ hội tốt' in desc or 'Có tiềm năng' in desc

    def test_generate_opportunity_description_low(self, generator):
        """Test description for low opportunity."""
        desc = generator.generate_opportunity_description('test topic', -0.2)
        assert 'Cạnh tranh cao' in desc

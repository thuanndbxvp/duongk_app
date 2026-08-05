"""
Idea Generation Service - HDBSCAN clustering & Gap Score calculation.
"""
from typing import Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from hdbscan import HDBSCAN


class IdeaGenerator:
    """Service for generating video topic ideas with gap analysis."""

    def cluster_topics(
        self,
        topics: list[str],
        min_cluster_size: int = 3,
    ) -> list[dict]:
        """
        Cluster topics using HDBSCAN.
        
        Args:
            topics: List of topic strings
            min_cluster_size: Minimum points per cluster
            
        Returns:
            List of dicts with topic, cluster_id, cluster_label
        """
        if not topics:
            return []

        # Edge case: not enough topics
        if len(topics) < min_cluster_size:
            return [
                {'topic': t, 'cluster_id': 0, 'cluster_label': 'misc'}
                for t in topics
            ]

        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(
            max_features=100,
            ngram_range=(1, 2),
        )
        vectors = vectorizer.fit_transform(topics)

        # HDBSCAN clustering
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            metric='euclidean', # cosine isn't directly supported by default in hdbscan unless specified with pairwise distances, fallback to default euclidean for stability
            cluster_selection_method='eom',
        )
        cluster_labels = clusterer.fit_predict(vectors.toarray())

        # Assign cluster names (top terms from centroid)
        cluster_names = self._get_cluster_names(
            vectors, cluster_labels, vectorizer, topics
        )

        return [
            {
                'topic': topic,
                'cluster_id': int(cluster_id),
                'cluster_label': cluster_names.get(cluster_id, 'unknown'),
            }
            for topic, cluster_id in zip(topics, cluster_labels)
        ]

    def _get_cluster_names(
        self,
        vectors,
        labels: np.ndarray,
        vectorizer: TfidfVectorizer,
        topics: list[str],
    ) -> dict:
        """Extract cluster names from top terms."""
        names = {}
        feature_names = vectorizer.get_feature_names_out()

        for label in set(labels):
            if label == -1:  # Noise
                names[label] = 'outlier'
                continue

            # Get indices for this cluster
            mask = labels == label
            if not mask.any():
                continue

            # Calculate centroid
            centroid = vectors[mask].mean(axis=0).A1

            # Get top 2 terms
            top_indices = centroid.argsort()[-2:][::-1]
            names[label] = ', '.join(feature_names[i] for i in top_indices)

        return names

    def calculate_gap_score(
        self,
        topic: str,
        channel_views: int,
        channel_avg_views: float,
        niche_trending: float,
    ) -> float:
        """
        Calculate gap score using Formula A14.
        
        Gap_Score = (Niche_Trending - Channel_Avg) / Channel_Avg
        
        Args:
            topic: Topic name (for reference)
            channel_views: Total channel views
            channel_avg_views: Average views per video
            niche_trending: Trending score 0-100 (Google Trends)
            
        Returns:
            Gap score (e.g., 0.25 = 25% opportunity)
        """
        if channel_avg_views <= 0:
            return 0.0

        # Estimate niche views from trending score
        niche_avg_views = (niche_trending / 100) * channel_views

        # Gap Score
        gap_score = (niche_avg_views - channel_avg_views) / channel_avg_views
        return round(gap_score, 3)

    def assign_confidence(self, gap_score: float) -> str:
        """Assign confidence level based on gap score."""
        if gap_score > 0.3:
            return 'high'
        elif gap_score >= 0:
            return 'medium'
        else:
            return 'low'

    def generate_opportunity_description(
        self,
        topic: str,
        gap_score: float,
    ) -> str:
        """Generate human-readable opportunity description."""
        if gap_score > 0.5:
            return f"Rất tiềm năng: {topic} đang trending cao hơn 50% so với mức trung bình của kênh"
        elif gap_score > 0.2:
            return f"Cơ hội tốt: {topic} trending cao hơn 20% so với mức trung bình của kênh"
        elif gap_score > 0:
            return f"Có tiềm năng: {topic} đang trending cao hơn mức trung bình của kênh"
        else:
            return f"Cạnh tranh cao: {topic} đang trending thấp hơn mức trung bình của kênh"
